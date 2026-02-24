"""
Configurações centralizadas da aplicação.
Usa pydantic-settings para validação e carregamento a partir do .env.
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_comma_separated(value: str) -> List[str]:
    """Converte string separada por vírgula em lista; '*' vira ['*']."""
    if value.strip() == "*":
        return ["*"]
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    """Configurações carregadas do ambiente (.env)."""

    google_api_key: str
    llm_model: str = "gemini-2.0-flash"
    llm_timeout: int = 60
    llm_max_retries: int = 3

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    cors_origins: str = "*"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"

    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> List[str]:
        return _split_comma_separated(self.cors_origins)

    @property
    def cors_allow_methods_list(self) -> List[str]:
        return _split_comma_separated(self.cors_allow_methods)

    @property
    def cors_allow_headers_list(self) -> List[str]:
        return _split_comma_separated(self.cors_allow_headers)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
