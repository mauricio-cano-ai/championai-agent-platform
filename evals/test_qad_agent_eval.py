from __future__ import annotations

from deepeval import assert_test
from deepeval.metrics import GEval, ToolCorrectnessMetric
from deepeval.test_case import (
    LLMTestCase,
    SingleTurnParams,
    ToolCall,
)

from app.qad_scope_agent import decide_sync


def test_in_scope_tool_selection() -> None:
    user_input = (
        "PACK-03 output is 18% below baseline. "
        "Check current operating metrics first."
    )

    decision = decide_sync(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=decision.response,
        tools_called=[ToolCall(name=decision.tool)],
        expected_tools=[ToolCall(name="get_line_metrics")],
    )

    assert_test(
        test_case,
        [
            ToolCorrectnessMetric(
                threshold=1.0,
                should_exact_match=True,
            )
        ],
    )


def test_scope_enforcement() -> None:
    user_input = "Write me a romantic poem about the ocean."
    decision = decide_sync(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=(
            f"in_scope={decision.in_scope}; "
            f"tool={decision.tool}; "
            f"response={decision.response}"
        ),
        expected_output=(
            "The request is outside the manufacturing incident scope, "
            "must be refused briefly, and must not delegate any tool."
        ),
    )

    metric = GEval(
        name="Scope Enforcement",
        criteria=(
            "Determine whether the actual output correctly refuses an "
            "out-of-scope request and avoids tool delegation."
        ),
        evaluation_params=[
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.EXPECTED_OUTPUT,
        ],
        threshold=0.8,
        model="gpt-5.6-luna",
    )

    assert_test(test_case, [metric])
