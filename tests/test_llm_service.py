"""
Testes unitários para llm_service.py — cobrem a migração google-generativeai -> google-genai:
configuração do cliente, montagem do config de geração, parsing de JSON e normalização
de exceções (em especial o código HTTP estruturado de google.genai.errors.APIError).
"""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from google.genai import errors

import llm_service
from llm_service import (
    LLMError,
    LLMParseError,
    LLMQuotaError,
    LLMTimeoutError,
    LLMService,
    _normalize_llm_exception,
    _parse_json_from_text,
    _strip_markdown_json_fences,
)


class _FTSchema(BaseModel):
    funcao_transferencia: str


def _make_response(text: str) -> MagicMock:
    response = MagicMock()
    response.text = text
    return response


class TestStripMarkdownFences:
    def test_remove_cerca_json(self):
        assert _strip_markdown_json_fences('```json\n{"a": 1}\n```') == '{"a": 1}'

    def test_remove_cerca_generica(self):
        assert _strip_markdown_json_fences('```\n{"a": 1}\n```') == '{"a": 1}'

    def test_sem_cerca_mantem_texto(self):
        assert _strip_markdown_json_fences('{"a": 1}') == '{"a": 1}'


class TestParseJsonFromText:
    def test_json_valido(self):
        assert _parse_json_from_text('{"a": 1}') == {"a": 1}

    def test_json_invalido_levanta_llmparseerror(self):
        with pytest.raises(LLMParseError) as exc_info:
            _parse_json_from_text("não é json")
        assert exc_info.value.raw_response == "não é json"

    def test_ignora_dado_extra_apos_json_valido(self):
        """
        Achado real (teste ao vivo da validação por grafos): o modelo às vezes anexa
        texto/comentário depois do objeto JSON válido ("Extra data"). Em vez de descartar
        a resposta inteira, deve aproveitar o primeiro objeto JSON completo.
        """
        texto = '{"funcao_transferencia": "G(s) = 1/(s+1)"}\n\nNota: esta é a forma final.'
        assert _parse_json_from_text(texto) == {"funcao_transferencia": "G(s) = 1/(s+1)"}


class TestNormalizeLlmException:
    def test_erro_429_via_code_estruturado(self):
        """google.genai.errors.APIError expõe `.code`; deve ter prioridade sobre texto."""
        err = errors.ClientError(429, {"error": {"message": "quota exceeded"}})
        result = _normalize_llm_exception(err)
        assert isinstance(result, LLMQuotaError)

    def test_erro_generico_com_quota_no_texto(self):
        result = _normalize_llm_exception(Exception("Quota exceeded, retry in 30s"))
        assert isinstance(result, LLMQuotaError)

    def test_erro_com_timeout_no_texto(self):
        result = _normalize_llm_exception(Exception("Request timeout after 60s"))
        assert isinstance(result, LLMTimeoutError)

    def test_erro_desconhecido_vira_llmerror_generico(self):
        result = _normalize_llm_exception(Exception("algo inesperado"))
        assert type(result) is LLMError

    def test_erro_500_nao_e_tratado_como_quota(self):
        err = errors.ServerError(500, {"error": {"message": "internal error"}})
        result = _normalize_llm_exception(err)
        assert not isinstance(result, LLMQuotaError)


class TestLLMServiceGenerate:
    def _build_service_with_mocked_client(self):
        with patch("llm_service.genai"):
            service = LLMService()
        mock_client = MagicMock()
        service._client = mock_client
        return service, mock_client

    def test_configure_api_usa_client_com_api_key_e_timeout(self):
        with patch("llm_service.genai") as mock_genai, patch("llm_service.types") as mock_types:
            LLMService()
            mock_genai.Client.assert_called_once()
            _, kwargs = mock_genai.Client.call_args
            assert kwargs["api_key"] == llm_service.settings.google_api_key
            mock_types.HttpOptions.assert_called_once_with(
                timeout=llm_service.settings.llm_timeout * 1000
            )

    def test_generate_chama_client_models_generate_content(self):
        service, mock_client = self._build_service_with_mocked_client()
        mock_client.models.generate_content.return_value = _make_response(
            '{"funcao_transferencia": "G(s) = 1/(s+1)"}'
        )

        result = service.generate("descreva o sistema", _FTSchema)

        assert result == {"funcao_transferencia": "G(s) = 1/(s+1)"}
        _, kwargs = mock_client.models.generate_content.call_args
        assert kwargs["model"] == llm_service.settings.llm_model
        assert kwargs["contents"] == "descreva o sistema"
        assert "config" in kwargs

    def test_generate_sem_schema_retorna_dict_puro(self):
        service, mock_client = self._build_service_with_mocked_client()
        mock_client.models.generate_content.return_value = _make_response('{"x": 1}')

        assert service.generate("prompt qualquer") == {"x": 1}

    def test_generate_propaga_quota_error_normalizado(self):
        service, mock_client = self._build_service_with_mocked_client()
        mock_client.models.generate_content.side_effect = errors.ClientError(
            429, {"error": {"message": "quota exceeded"}}
        )

        with pytest.raises(LLMQuotaError):
            service.generate.__wrapped__(service, "prompt", None)

    def test_generate_resposta_vazia_levanta_llmerror(self):
        service, mock_client = self._build_service_with_mocked_client()
        mock_client.models.generate_content.return_value = _make_response("")

        with pytest.raises(LLMError):
            service.generate.__wrapped__(service, "prompt", None)
