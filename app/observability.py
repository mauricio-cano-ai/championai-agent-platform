from __future__ import annotations

import json
import logging
from typing import Any

LOGGER = logging.getLogger("championai")


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    LOGGER.setLevel(getattr(logging, level.upper(), logging.INFO))


def log_event(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    LOGGER.info(json.dumps(payload, sort_keys=True, separators=(",", ":")))
