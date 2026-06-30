"""Configuration placeholders for the Money_Never_sleep API service."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000


settings = Settings()
