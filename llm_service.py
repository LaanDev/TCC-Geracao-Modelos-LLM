"""
Serviço de comunicação com o LLM (Google Gemini/Gemma).
Responsável por: configuração, timeout, retry e parsing de respostas.
"""

import json
import logging
import re
import time
from typing import Any, Dict, Optional, Type

from functools import wraps
import google.generativeai as genai
from pydantic import BaseModel, ValidationError

from config import settings
from prompts import SYSTEM_PROMPT, get_generation_config

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("llm_service")

MARKDOWN_JSON_FENCE_START = "```json"
MARKDOWN_JSON_FENCE_START_ALT = "```"
MARKDOWN_FENCE_END = "```"
RAW_RESPONSE_DEBUG_LENGTH = 500
QUOTA_RETRY_WAIT_SECONDS = 45
QUOTA_RETRY_MAX_WAIT_SECONDS = 120


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------


class LLMError(Exception):
    """Erro base para falhas do LLM."""


class LLMTimeoutError(LLMError):
    """Timeout na chamada ao LLM."""


class LLMParseError(LLMError):
    """Resposta do LLM não é JSON válido."""

    def __init__(self, message: str, raw_response: Optional[str] = None):
        super().__init__(message)
        self.raw_response = raw_response


class LLMValidationError(LLMError):
    """Resposta não passou na validação do schema."""


class LLMQuotaError(LLMError):
    """Cota da API excedida (429)."""


# -----------------------------------------------------------------------------
# Retry decorator
# -----------------------------------------------------------------------------


def _wait_seconds_for_quota(attempt: int, error_message: str) -> float:
    """Calcula tempo de espera para retry em caso de quota (429)."""
    if attempt != 1:
        return 60.0
    match = re.search(r"retry in (\d+(?:\.\d+)?)\s*s", error_message.lower())
    if match:
        return min(float(match.group(1)) + 2, QUOTA_RETRY_MAX_WAIT_SECONDS)
    return QUOTA_RETRY_WAIT_SECONDS


def retry_on_failure(
    max_retries: Optional[int] = None,
    delay: float = 1.0,
    backoff: float = 2.0,
):
    """Retry automático para falhas recuperáveis (timeout, parse, quota)."""

    if max_retries is None:
        max_retries = settings.llm_max_retries

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (LLMTimeoutError, LLMParseError, LLMQuotaError) as e:
                    last_exception = e
                    wait = (
                        _wait_seconds_for_quota(attempt, str(e))
                        if isinstance(e, LLMQuotaError)
                        else current_delay
                    )
                    logger.warning(
                        "Tentativa %s/%s falhou: %s. Aguardando %.1fs...",
                        attempt,
                        max_retries,
                        e,
                        wait,
                    )
                    if attempt < max_retries:
                        time.sleep(wait)
                        if not isinstance(e, LLMQuotaError):
                            current_delay = wait * backoff
                except Exception as e:
                    logger.error("Erro não recuperável: %s", e)
                    raise

            logger.error("Todas as %s tentativas falharam.", max_retries)
            raise last_exception

        return wrapper

    return decorator


# -----------------------------------------------------------------------------
# LLM Service
# -----------------------------------------------------------------------------


def _strip_markdown_json_fences(text: str) -> str:
    """Remove cercas de código markdown (```json ... ```) do texto."""
    stripped = text.strip()
    if stripped.startswith(MARKDOWN_JSON_FENCE_START):
        stripped = stripped[len(MARKDOWN_JSON_FENCE_START) :]
    elif stripped.startswith(MARKDOWN_JSON_FENCE_START_ALT):
        stripped = stripped[len(MARKDOWN_JSON_FENCE_START_ALT) :]
    if stripped.endswith(MARKDOWN_FENCE_END):
        stripped = stripped[: -len(MARKDOWN_FENCE_END)]
    return stripped.strip()


def _parse_json_from_text(response_text: str) -> Dict[str, Any]:
    """Extrai e parseia JSON do texto da resposta. Levanta LLMParseError se inválido."""
    cleaned = _strip_markdown_json_fences(response_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("Falha ao fazer parse do JSON: %s", e)
        logger.debug("Resposta bruta: %s...", response_text[:RAW_RESPONSE_DEBUG_LENGTH])
        raise LLMParseError(
            f"O LLM não retornou um JSON válido: {e}",
            raw_response=response_text,
        ) from e


def _is_quota_error(exception: Exception) -> bool:
    """Indica se o erro é de cota/rate limit (429)."""
    err_str = str(exception).lower()
    return "429" in err_str or "quota" in err_str or "rate" in err_str


def _is_timeout_error(exception: Exception) -> bool:
    """Indica se o erro é de timeout."""
    return "timeout" in str(exception).lower()


def _normalize_llm_exception(exception: Exception) -> LLMError:
    """Converte exceção genérica em tipo específico do domínio LLM."""
    if _is_timeout_error(exception):
        return LLMTimeoutError(f"Timeout na requisição: {exception}")
    if _is_quota_error(exception):
        return LLMQuotaError(
            "Quota da API excedida. Aguarde cerca de 1 minuto e tente novamente. "
            f"Detalhes: {exception}"
        )
    return LLMError(f"Falha na comunicação com o LLM: {exception}")


class LLMService:
    """
    Serviço para comunicação com o LLM do Google (Gemini/Gemma).
    Uma única responsabilidade: enviar prompt e devolver resposta validada.
    """

    def __init__(self):
        self._model = None
        self._configure_api()

    def _configure_api(self) -> None:
        """Configura a API do Google com a chave do ambiente."""
        try:
            genai.configure(api_key=settings.google_api_key)
            logger.info("API do Google configurada com sucesso.")
        except Exception as e:
            logger.critical("Falha ao configurar API do Google: %s", e)
            raise LLMError(f"Não foi possível configurar a API: {e}") from e

    @property
    def model(self) -> genai.GenerativeModel:
        """Modelo Gemini (lazy loading)."""
        if self._model is None:
            self._model = genai.GenerativeModel(
                model_name=settings.llm_model,
                system_instruction=SYSTEM_PROMPT,
            )
            logger.info("Modelo '%s' inicializado.", settings.llm_model)
        return self._model

    def _get_response_text(self, response) -> str:
        """Extrai texto da resposta; levanta LLMError se bloqueada ou vazia."""
        try:
            text = response.text if response.text else ""
        except (ValueError, AttributeError) as e:
            logger.error("Resposta bloqueada ou vazia: %s", e)
            raise LLMError(
                "A resposta do modelo foi bloqueada ou está vazia. "
                "Tente reformular a descrição ou verifique as configurações de segurança da API."
            ) from e
        if not text.strip():
            raise LLMError("O modelo retornou uma resposta vazia.")
        return text

    def _validate_against_schema(
        self, data: Dict[str, Any], schema: Type[BaseModel]
    ) -> BaseModel:
        """Valida dicionário contra schema Pydantic."""
        try:
            return schema(**data)
        except ValidationError as e:
            logger.error("Resposta não passou na validação do schema: %s", e)
            raise LLMValidationError(f"Resposta inválida: {e}") from e

    @retry_on_failure()
    def generate(
        self,
        prompt: str,
        response_schema: Optional[Type[BaseModel]] = None,
    ) -> Dict[str, Any]:
        """
        Gera resposta do LLM para o prompt e valida contra o schema (se fornecido).
        Retorna dicionário (model_dump do schema ou JSON parseado).
        """
        logger.info("Enviando prompt ao LLM...")
        logger.debug("Prompt (primeiros 200 chars): %s...", prompt[:200])

        start = time.time()
        generation_config = get_generation_config()

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                request_options={"timeout": settings.llm_timeout},
            )
        except genai.types.generation_types.StopCandidateException as e:
            logger.error("Geração interrompida: %s", e)
            raise LLMError(f"Geração interrompida pelo modelo: {e}") from e
        except TimeoutError:
            logger.error("Timeout após %ss", settings.llm_timeout)
            raise LLMTimeoutError(
                f"A requisição excedeu o tempo limite de {settings.llm_timeout}s"
            )
        except Exception as e:
            raise _normalize_llm_exception(e)

        elapsed = time.time() - start
        logger.info("Resposta recebida em %.2fs", elapsed)

        response_text = self._get_response_text(response)
        data = _parse_json_from_text(response_text)

        if response_schema:
            validated = self._validate_against_schema(data, response_schema)
            return validated.model_dump()
        return data


# -----------------------------------------------------------------------------
# Singleton
# -----------------------------------------------------------------------------

_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Retorna a instância do serviço LLM (singleton)."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
