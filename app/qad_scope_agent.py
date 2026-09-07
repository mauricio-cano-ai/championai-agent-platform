from __future__ import annotations

import asyncio
import os
from typing import Literal

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel


SYSTEM_PROMPT = """
<champion>
  <role>
    You are a manufacturing incident triage Champion.
  </role>

  <scope>
    <allowed>
      Diagnose manufacturing-line incidents, production loss, downtime,
      equipment symptoms, and maintenance-related operational evidence.
    </allowed>
    <forbidden>
      Do not answer unrelated requests such as creative writing,
      politics, personal advice, shopping, or general trivia.
    </forbidden>
    <out_of_scope_behavior>
      Refuse briefly and do not call a tool.
    </out_of_scope_behavior>
  </scope>

  <delegation>
    <tool name="get_line_metrics">
      Use when current throughput, baseline, downtime counts, or line
      operating metrics are needed.
    </tool>
    <tool name="get_recent_incidents">
      Use when prior incidents, root causes, or previous resolutions
      are needed.
    </tool>
    <tool name="none">
      Use when the request is outside scope or no tool is required.
    </tool>
  </delegation>

  <rules>
    <rule>Never invent plant evidence.</rule>
    <rule>Choose only one first-step tool.</rule>
    <rule>Out-of-scope requests must use tool=none.</rule>
  </rules>
</champion>
""".strip()


class ScopeDecision(BaseModel):
    in_scope: bool
    tool: Literal[
        "get_line_metrics",
        "get_recent_incidents",
        "none",
    ]
    response: str


def _parsed(response) -> ScopeDecision:
    for output in response.output:
        if output.type != "message":
            continue
        for item in output.content:
            if item.type == "output_text" and item.parsed is not None:
                return item.parsed
    raise RuntimeError("No structured ScopeDecision returned.")


async def decide(user_input: str) -> ScopeDecision:
    load_dotenv()

    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    client = AsyncOpenAI()

    response = await client.responses.parse(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=user_input,
        text_format=ScopeDecision,
    )

    decision = _parsed(response)

    if not decision.in_scope and decision.tool != "none":
        raise ValueError("Scope leak: out-of-scope request delegated a tool.")

    return decision


def decide_sync(user_input: str) -> ScopeDecision:
    return asyncio.run(decide(user_input))


if __name__ == "__main__":
    inside = decide_sync(
        "PACK-03 output is 18% below baseline. "
        "Check the current operating metrics first."
    )
    outside = decide_sync(
        "Write me a romantic poem about the ocean."
    )

    print("IN-SCOPE:", inside.model_dump())
    print("OUT-OF-SCOPE:", outside.model_dump())

    assert inside.in_scope is True
    assert inside.tool == "get_line_metrics"
    assert outside.in_scope is False
    assert outside.tool == "none"

    print("XML_SCOPE_ENFORCEMENT=PASS")
