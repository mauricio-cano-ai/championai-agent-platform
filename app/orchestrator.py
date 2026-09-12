from __future__ import annotations

from uuid import uuid4

from .domain import ActionProposal, Evidence, IncidentRequest, TaskRecord, TaskStatus
from .ports import Executor, Investigator, Planner, TaskStore
from .reliability import RetryPolicy, retry_async


class TaskNotFoundError(KeyError):
    pass


class InvalidTransitionError(RuntimeError):
    pass


class Orchestrator:
    def __init__(
        self,
        *,
        store: TaskStore,
        planner: Planner,
        investigator: Investigator,
        executor: Executor,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.store = store
        self.planner = planner
        self.investigator = investigator
        self.executor = executor
        self.retry_policy = retry_policy or RetryPolicy()

    async def submit(self, request: IncidentRequest) -> TaskRecord:
        existing = await self.store.get_by_request_id(request.request_id)
        if existing is not None:
            return existing

        candidate = TaskRecord(
            task_id=f"task-{uuid4().hex[:16]}",
            request=request,
            status=TaskStatus.INVESTIGATING,
        )
        task = await self.store.create(candidate)
        if task.task_id != candidate.task_id or task.status is not TaskStatus.INVESTIGATING:
            return task

        plan = await retry_async(lambda: self.planner.plan(request), self.retry_policy)
        raw_evidence = await retry_async(
            lambda: self.investigator.collect(request, plan),
            self.retry_policy,
        )
        evidence = [
            item if isinstance(item, Evidence) else Evidence.model_validate(item)
            for item in raw_evidence
        ]
        strongest = max((item.confidence for item in evidence), default=0.0)
        proposal = ActionProposal(
            action=f"apply a reversible mitigation to {request.asset_id}",
            rationale=(
                f"Evidence collected from {len(evidence)} sources; "
                f"strongest confidence {strongest:.2f}"
            ),
            risk="medium",
        )
        task.plan = plan
        task.evidence = evidence
        task.proposal = proposal
        task.status = TaskStatus.WAITING_APPROVAL
        return await self.store.save(task)

    async def approve(self, task_id: str, *, approved_by: str) -> TaskRecord:
        task = await self._require(task_id)
        if task.status is TaskStatus.COMPLETED:
            return task
        proposal = task.proposal
        if task.status is not TaskStatus.WAITING_APPROVAL or proposal is None:
            raise InvalidTransitionError(f"cannot approve task in {task.status}")

        claimed = await self.store.claim_execution(task_id)
        if not claimed:
            current = await self._require(task_id)
            if current.status is TaskStatus.COMPLETED:
                return current
            raise InvalidTransitionError("execution already claimed")

        execution = await retry_async(
            lambda: self.executor.execute(proposal),
            self.retry_policy,
        )
        task.execution = execution
        task.decision_by = approved_by
        task.status = TaskStatus.COMPLETED
        return await self.store.save(task)

    async def reject(self, task_id: str, *, rejected_by: str, reason: str) -> TaskRecord:
        task = await self._require(task_id)
        if task.status is not TaskStatus.WAITING_APPROVAL:
            raise InvalidTransitionError(f"cannot reject task in {task.status}")
        task.decision_by = rejected_by
        task.decision_reason = reason
        task.status = TaskStatus.REJECTED
        return await self.store.save(task)

    async def _require(self, task_id: str) -> TaskRecord:
        task = await self.store.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task
