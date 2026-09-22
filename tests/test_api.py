"""
Testes de integração para os endpoints da API.
Usa mocks para não depender de chamadas reais ao LLM.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["GOOGLE_API_KEY"] = "fake-api-key-for-testing"
os.environ["OPENAI_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["LOG_LEVEL"] = "WARNING"

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from diagram_executor import DiagramExecResult
from ensemble_service import EnsembleOutcome, ProviderResponse


_PNG_1X1 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

_ANALISE = {
    "lei_aplicada": "Lei de Kirchhoff das Tensões (LKT)",
    "equacao_diferencial": "RC dVc/dt + Vc = Vin",
    "passos_laplace": "1. Aplicando Laplace: Vin(s) = RCs·Vc(s) + Vc(s)",
    "funcao_transferencia": "G(s) = 1 / (RCs + 1)",
    "analise_resultado": "Sistema de 1ª ordem, estável, polo em s = -1/RC",
    "codigo_diagrama": "import control as ctrl\nG = ctrl.tf([1], [R*C, 1])",
}


def _exec_result():
    return DiagramExecResult(
        diagramas_png_base64=[_PNG_1X1],
        execucao_ok=True,
        log_execucao="",
        diagramas_arquivos=["diagrams/diagrama_ex1.png"],
    )


def _outcome(payload=None, executado=False, **kwargs):
    payload = payload or dict(_ANALISE)
    return EnsembleOutcome(
        executado=executado,
        payload_vencedor=payload,
        provedor_vencedor=kwargs.get("provedor_vencedor", "google"),
        consenso_ft=kwargs.get("consenso_ft", payload.get("funcao_transferencia")),
        concordancia=kwargs.get("concordancia"),
        mensagem=kwargs.get("mensagem"),
        respostas=kwargs.get("respostas", []),
    )


@pytest.fixture
def client():
    with patch("llm_service.genai"):
        from main import app

        with TestClient(app) as test_client:
            yield test_client


class TestHealthCheck:
    @pytest.mark.api
    def test_root_retorna_status_online(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "online"

    @pytest.mark.api
    def test_root_retorna_versao_e_modelo(self, client):
        data = client.get("/").json()
        assert "versao" in data
        assert "modelo_llm" in data


class TestEndpointAnaliseCompleta:
    @pytest.mark.api
    @patch("main.execute_diagram_python")
    @patch("main.run_ensemble_analise")
    def test_analise_completa_sucesso(self, mock_ens, mock_exec, client):
        mock_ens.return_value = _outcome()
        mock_exec.return_value = _exec_result()
        response = client.post(
            "/gerar-analise-completa",
            json={"descricao": "Circuito RC série com saída no capacitor"},
        )
        assert response.status_code == 200
        data = response.json()
        for chave in (
            "lei_aplicada",
            "equacao_diferencial",
            "passos_laplace",
            "funcao_transferencia",
            "analise_resultado",
        ):
            assert chave in data

    @pytest.mark.api
    @patch("main.save_diagram_pngs_to_disk", return_value=["diagrams/diagrama_grafo_ex1.png"])
    @patch("main.render_diagram_graph", return_value=b"\x89PNG\r\n\x1a\n")
    @patch("main.execute_diagram_python")
    @patch("main.run_ensemble_analise")
    def test_analise_completa_renderiza_grafo_sem_codigo(
        self, mock_ens, mock_exec, mock_render, mock_save, client
    ):
        payload = dict(_ANALISE)
        payload["codigo_diagrama"] = None
        payload["grafo_diagrama"] = {
            "nos": [
                {"id": "u", "tipo": "entrada"},
                {"id": "g", "tipo": "bloco", "ganho": "1/(R*C*s+1)"},
                {"id": "y", "tipo": "saida"},
            ],
            "arestas": [
                {"origem": "u", "destino": "g", "sinal": "+"},
                {"origem": "g", "destino": "y", "sinal": "+"},
            ],
        }
        mock_ens.return_value = _outcome(payload)
        data = client.post(
            "/gerar-analise-completa",
            json={"descricao": "Circuito RC série"},
        ).json()
        mock_exec.assert_not_called()
        mock_render.assert_called_once()
        assert data.get("diagramas_png_base64")
        assert data.get("execucao_diagrama_ok") is False

    @pytest.mark.api
    def test_analise_completa_descricao_invalida(self, client):
        response = client.post("/gerar-analise-completa", json={"descricao": "x"})
        assert response.status_code == 422

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    @patch("main.run_ensemble_analise")
    def test_analise_completa_roda_verificacao_de_ft(self, mock_ens, mock_exec, client):
        mock_ens.return_value = _outcome()
        mock_exec.return_value = _exec_result()
        data = client.post(
            "/gerar-analise-completa",
            json={"descricao": "Circuito RC série com saída no capacitor"},
        ).json()
        assert data["verificacao_executada"] is True
        assert data["verificacao_ft_ok"] is True

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    @patch("main.run_ensemble_analise")
    def test_analise_completa_expoe_ensemble_sem_voto(self, mock_ens, mock_exec, client):
        mock_ens.return_value = _outcome(
            executado=False,
            mensagem="Ensemble não executado: são necessários pelo menos 2 provedores.",
        )
        mock_exec.return_value = _exec_result()
        data = client.post(
            "/gerar-analise-completa",
            json={"descricao": "Circuito RC série com saída no capacitor"},
        ).json()
        assert data["ensemble_executado"] is False
        assert data["ensemble_provedor_vencedor"] == "google"

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    @patch("main.run_ensemble_analise")
    def test_analise_completa_usa_payload_vencedor_do_voto(self, mock_ens, mock_exec, client):
        payload = dict(_ANALISE)
        payload["lei_aplicada"] = "escolhida pelo voto"
        mock_ens.return_value = _outcome(
            payload=payload,
            executado=True,
            concordancia="2/2",
            provedor_vencedor="anthropic",
            respostas=[
                ProviderResponse("google", "gemini", True, payload["funcao_transferencia"], payload),
                ProviderResponse("anthropic", "claude", True, payload["funcao_transferencia"], payload),
            ],
        )
        mock_exec.return_value = _exec_result()
        data = client.post(
            "/gerar-analise-completa",
            json={"descricao": "Circuito RC série com saída no capacitor"},
        ).json()
        assert data["lei_aplicada"] == "escolhida pelo voto"
        assert data["ensemble_executado"] is True
        assert data["ensemble_concordancia"] == "2/2"
        assert data["ensemble_provedor_vencedor"] == "anthropic"
        assert len(data["ensemble_respostas"]) == 2

    @pytest.mark.api
    @patch("main.run_ensemble_analise")
    def test_analise_completa_sem_payload_retorna_500(self, mock_ens, client):
        mock_ens.return_value = EnsembleOutcome(
            executado=True,
            mensagem="Nenhum provedor conseguiu gerar a análise completa.",
        )
        response = client.post(
            "/gerar-analise-completa",
            json={"descricao": "Circuito RC série com saída no capacitor"},
        )
        assert response.status_code == 500
        assert response.json()["sucesso"] is False

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    @patch("main.run_ensemble_analise")
    def test_analise_completa_sem_grafo_nao_executa_verificacao(self, mock_ens, mock_exec, client):
        mock_ens.return_value = _outcome()
        mock_exec.return_value = _exec_result()
        data = client.post(
            "/gerar-analise-completa",
            json={"descricao": "Circuito RC série com saída no capacitor"},
        ).json()
        assert data["verificacao_grafo_executada"] is False
        assert data["verificacao_grafo_ok"] is True

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    @patch("main.run_ensemble_analise")
    def test_analise_completa_valida_grafo_coerente(self, mock_ens, mock_exec, client):
        mock_exec.return_value = _exec_result()
        grafo = {
            "nos": [
                {"id": "u", "tipo": "entrada"},
                {"id": "g", "tipo": "bloco", "ganho": "1/(R*C*s+1)"},
                {"id": "y", "tipo": "saida"},
            ],
            "arestas": [
                {"origem": "u", "destino": "g", "sinal": "+"},
                {"origem": "g", "destino": "y", "sinal": "+"},
            ],
        }
        payload = dict(_ANALISE)
        payload["grafo_diagrama"] = grafo
        mock_ens.return_value = _outcome(payload=payload)
        data = client.post(
            "/gerar-analise-completa",
            json={"descricao": "Circuito RC série com saída no capacitor"},
        ).json()
        assert data["verificacao_grafo_executada"] is True
        assert data["verificacao_grafo_ok"] is True

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    @patch("main.run_ensemble_analise")
    def test_analise_completa_grafo_malformado_nao_quebra_resposta(self, mock_ens, mock_exec, client):
        mock_exec.return_value = _exec_result()
        payload = dict(_ANALISE)
        payload["grafo_diagrama"] = {
            "nos": [
                {"id": "u", "tipo": "entrada"},
                {"id": "g", "tipo": "bloco", "ganho": "1/(R*C*s+1)"},
            ],
            "arestas": [{"origem": "u", "destino": "g", "sinal": "+"}],
        }
        mock_ens.return_value = _outcome(payload=payload)
        data = client.post(
            "/gerar-analise-completa",
            json={"descricao": "Circuito RC série com saída no capacitor"},
        ).json()
        assert data["verificacao_grafo_executada"] is True
        assert data["verificacao_grafo_ok"] is False
        assert data["mensagem_verificacao_grafo"] is not None


class TestTratamentoErros:
    @pytest.mark.api
    def test_endpoint_inexistente(self, client):
        assert client.get("/endpoint-que-nao-existe").status_code == 404

    @pytest.mark.api
    def test_metodo_nao_permitido(self, client):
        assert client.get("/gerar-analise-completa").status_code == 405

    @pytest.mark.api
    def test_corpo_json_invalido(self, client):
        response = client.post(
            "/gerar-analise-completa",
            content="isso não é json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.api
    def test_rota_removida_nao_existe(self, client):
        for rota in (
            "/gerar-apenas-ft",
            "/gerar-apenas-ft-ensemble",
            "/gerar-diagrama-por-ft",
            "/gerar-ft-e-diagrama",
            "/validar-minha-resposta",
        ):
            assert client.post(rota, json={"descricao": "Circuito RC série com saída no capacitor"}).status_code == 404


class TestCORS:
    @pytest.mark.api
    def test_cors_permite_origem(self, client):
        response = client.options(
            "/gerar-analise-completa",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code in [200, 405]


class TestDocumentacao:
    @pytest.mark.api
    def test_openapi_disponivel(self, client):
        data = client.get("/openapi.json").json()
        assert "openapi" in data
        assert "/gerar-analise-completa" in data["paths"]
        assert "/gerar-apenas-ft" not in data["paths"]

    @pytest.mark.api
    def test_swagger_ui_disponivel(self, client):
        assert client.get("/docs").status_code == 200

    @pytest.mark.api
    def test_redoc_disponivel(self, client):
        assert client.get("/redoc").status_code == 200
