from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CHAMPIONAI_", extra="ignore")

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    retry_max_attempts: int = Field(default=3, ge=1, le=8)
    retry_base_delay_seconds: float = Field(default=0.2, ge=0, le=10)
