"""
Configurações centralizadas da aplicação.
Usa pydantic-settings para validação e carregamento a partir do .env.
"""

from typing import List, Optional

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

    # Execução automática do código gerado para diagramas (subprocesso isolado)
    execute_diagram_code: bool = True
    diagram_execution_timeout: int = 45
    # Persistência dos PNG gerados em disco (pasta relativa à raiz do projeto)
    diagram_save_to_disk: bool = True
    diagram_output_dir: str = "diagrams"

    # Verificação pós-LLM (SymPy + gabaritos canônicos) e retry curtíssimo
    ft_verification_enabled: bool = True
    ft_verification_retry_llm: bool = True

    # Validação estrutural do diagrama por grafo (Fórmula de Ganho de Mason).
    # Roda só quando o LLM emite "grafo_diagrama"; se ausente/malformado, é ignorada
    # silenciosamente (não bloqueia a resposta), então é seguro deixar ligada por padrão.
    graph_validation_enabled: bool = True

    # Ensemble entre provedores de LLM diferentes (Google + Anthropic + Groq + OpenAI): cada
    # provedor configurado (chave de API presente) responde à mesma pergunta em paralelo,
    # e o consenso é decidido por equivalência simbólica (SymPy) entre as FTs — não por
    # comparação de string. Provedores sem chave configurada são simplesmente pulados;
    # o ensemble só roda de fato com pelo menos 2 provedores disponíveis.
    ensemble_enabled: bool = True
    ensemble_timeout: int = 60
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-haiku-4-5-20251001"
    # Groq: tier gratuito sem cartão de crédito (console.groq.com/keys), API compatível com
    # o formato da OpenAI (mesmo SDK `openai`, só troca a `base_url`).
    groq_api_key: Optional[str] = None
    groq_model: str = "openai/gpt-oss-120b"

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
