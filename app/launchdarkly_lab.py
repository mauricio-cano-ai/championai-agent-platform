from __future__ import annotations

from ldclient import Config, Context, LDClient
from ldclient.integrations.test_data import TestData


FLAG_KEY = "champion-prompt-version"


def main() -> None:
    # Official LaunchDarkly TestData source: real SDK behavior,
    # deterministic local flag changes, no cloud account needed.
    test_data = TestData.data_source()

    test_data.update(
        test_data.flag(FLAG_KEY)
        .variations("v1", "v2")
        .fallthrough_variation(0)
    )

    client = LDClient(
        config=Config(
            "local-qad-training-key",
            update_processor_class=test_data,
            send_events=False,
        )
    )

    context = Context.create("mauricio-qad-training")

    first = client.variation(
        FLAG_KEY,
        context,
        "v1",
    )

    print(f"initial_prompt_version={first}")
    assert first == "v1"

    # Simulate an environment-gated rollout without redeploying code.
    test_data.update(
        test_data.flag(FLAG_KEY)
        .variations("v1", "v2")
        .fallthrough_variation(1)
    )

    second = client.variation(
        FLAG_KEY,
        context,
        "v1",
    )

    print(f"rolled_out_prompt_version={second}")
    assert second == "v2"

    client.close()
    print("LAUNCHDARKLY_PROMPT_ROLLOUT=PASS")


if __name__ == "__main__":
    main()
