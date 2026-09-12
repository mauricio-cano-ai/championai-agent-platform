"""A2A boundary sketch: task exchange is explicit, typed and side-effect free by default."""
from pydantic import BaseModel, ConfigDict


class AgentTaskEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: str
    capability: str
    payload_ref: str
    allow_side_effects: bool = False
