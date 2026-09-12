import json
import logging

from app.config import Settings
from app.observability import configure_logging, log_event


def test_settings_are_typed_and_validate_retry_bounds(monkeypatch):
    monkeypatch.setenv("CHAMPIONAI_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CHAMPIONAI_RETRY_MAX_ATTEMPTS", "4")
    settings = Settings()
    assert settings.log_level == "DEBUG"
    assert settings.retry_max_attempts == 4


def test_structured_log_event_is_machine_readable_and_excludes_payload(caplog):
    configure_logging("INFO")
    with caplog.at_level(logging.INFO, logger="championai"):
        log_event("task_transition", task_id="task-1", status="WAITING_APPROVAL")
    payload = json.loads(caplog.records[-1].message)
    assert payload == {"event": "task_transition", "status": "WAITING_APPROVAL", "task_id": "task-1"}
