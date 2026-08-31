"""
Testes de integração para os endpoints da API.
Usa mocks para não depender de chamadas reais ao LLM.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagram_executor import DiagramExecResult

# Mock das configurações antes de importar
os.environ["GOOGLE_API_KEY"] = "fake-api-key-for-testing"
os.environ["LOG_LEVEL"] = "WARNING"


# ============================================================================
# FIXTURES LOCAIS
# ============================================================================

@pytest.fixture
def client():
    """Cliente de teste com LLM mockado."""
    with patch('llm_service.genai'):
        # google.genai.Client(...) fica mockado; nenhuma chamada real é feita.

        # Import app after mocking
        from main import app

        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def mock_llm_ft():
    """Mock do serviço LLM para endpoint de FT."""
    with patch('main.get_llm_service') as mock:
        service = MagicMock()
        service.generate.return_value = {
            "funcao_transferencia": "G(s) = 1 / (RCs + 1)"
        }
        mock.return_value = service
        yield service


@pytest.fixture
def mock_llm_analise():
    """Mock do serviço LLM para endpoint de análise completa."""
    with patch('main.get_llm_service') as mock:
        service = MagicMock()
        service.generate.return_value = {
            "lei_aplicada": "Lei de Kirchhoff das Tensões (LKT)",
            "equacao_diferencial": "RC dVc/dt + Vc = Vin",
            "passos_laplace": "1. Aplicando Laplace: Vin(s) = RCs·Vc(s) + Vc(s)",
            "funcao_transferencia": "G(s) = 1 / (RCs + 1)",
            "analise_resultado": "Sistema de 1ª ordem, estável, polo em s = -1/RC",
            "codigo_diagrama": "import control as ctrl\nG = ctrl.tf([1], [R*C, 1])"
        }
        mock.return_value = service
        yield service


@pytest.fixture
def mock_llm_diagram_por_ft():
    """Mock LLM retornando apenas codigo_diagrama."""
    with patch("main.get_llm_service") as mock:
        service = MagicMock()
        service.generate.return_value = {
            "codigo_diagrama": (
                "import matplotlib.pyplot as plt\n"
                "plt.figure(); plt.plot([0, 1], [0, 1]); plt.show()"
            )
        }
        mock.return_value = service
        yield service


@pytest.fixture
def mock_llm_ft_e_diagrama():
    """Mock LLM para /gerar-ft-e-diagrama."""
    with patch("main.get_llm_service") as mock:
        service = MagicMock()
        # Mesma forma canônica do verificador SymPy para descrições RC+Vc típicas de teste
        service.generate.return_value = {
            "funcao_transferencia": "G(s) = 1 / (RCs + 1)",
            "codigo_diagrama": (
                "import matplotlib.pyplot as plt\n"
                "plt.figure(); plt.plot([0, 1], [0, 1]); plt.show()"
            ),
        }
        mock.return_value = service
        yield service


@pytest.fixture
def mock_llm_validacao():
    """Mock do serviço LLM para endpoint de validação."""
    with patch('main.get_llm_service') as mock:
        service = MagicMock()
        service.generate.return_value = {
            "resposta_correta": True,
            "feedback": "Excelente! Sua resposta está correta.",
            "solucao_correta": "G(s) = 1 / (RCs + 1)"
        }
        mock.return_value = service
        yield service


# ============================================================================
# TESTES: Endpoint Raiz (Health Check)
# ============================================================================

class TestHealthCheck:
    """Testes para o endpoint de health check."""
    
    @pytest.mark.api
    def test_root_retorna_status_online(self, client):
        """Endpoint raiz deve retornar status online."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
    
    @pytest.mark.api
    def test_root_retorna_versao(self, client):
        """Endpoint raiz deve retornar versão da API."""
        response = client.get("/")
        
        data = response.json()
        assert "versao" in data
        assert data["versao"] is not None
    
    @pytest.mark.api
    def test_root_retorna_modelo(self, client):
        """Endpoint raiz deve retornar modelo LLM configurado."""
        response = client.get("/")
        
        data = response.json()
        assert "modelo_llm" in data


# ============================================================================
# TESTES: Endpoint /gerar-apenas-ft
# ============================================================================

class TestEndpointApenasFT:
    """Testes para o endpoint de geração de FT."""
    
    @pytest.mark.api
    def test_gerar_ft_sucesso(self, client, mock_llm_ft):
        """Deve retornar FT com sucesso."""
        response = client.post(
            "/gerar-apenas-ft",
            json={"descricao": "Circuito RC série com saída no capacitor"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "funcao_transferencia" in data
        assert "G(s)" in data["funcao_transferencia"]
    
    @pytest.mark.api
    def test_gerar_ft_descricao_curta(self, client):
        """Deve rejeitar descrição muito curta."""
        response = client.post(
            "/gerar-apenas-ft",
            json={"descricao": "RC"}
        )
        
        assert response.status_code == 422  # Validation Error
    
    @pytest.mark.api
    def test_gerar_ft_sem_descricao(self, client):
        """Deve rejeitar requisição sem descrição."""
        response = client.post(
            "/gerar-apenas-ft",
            json={}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.api
    def test_gerar_ft_chama_llm(self, client, mock_llm_ft):
        """Deve chamar o serviço LLM."""
        client.post(
            "/gerar-apenas-ft",
            json={"descricao": "Circuito RC série com saída no capacitor"}
        )
        
        mock_llm_ft.generate.assert_called_once()


# ============================================================================
# TESTES: Endpoint /gerar-analise-completa
# ============================================================================

class TestEndpointAnaliseCompleta:
    """Testes para o endpoint de análise completa."""

    _PNG_1X1 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )

    def _mock_exec_result(self):
        return DiagramExecResult(
            diagramas_png_base64=[self._PNG_1X1],
            execucao_ok=True,
            log_execucao="",
            diagramas_arquivos=["diagrams/diagrama_rota5_ex1.png"],
        )

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    def test_analise_completa_sucesso(self, mock_exec, client, mock_llm_analise):
        """Deve retornar análise completa com sucesso."""
        mock_exec.return_value = self._mock_exec_result()
        response = client.post(
            "/gerar-analise-completa",
            json={"descricao": "Circuito RC série com saída no capacitor"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verifica todas as chaves esperadas
        assert "lei_aplicada" in data
        assert "equacao_diferencial" in data
        assert "passos_laplace" in data
        assert "funcao_transferencia" in data
        assert "analise_resultado" in data

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    def test_analise_completa_retorna_codigo(self, mock_exec, client, mock_llm_analise):
        """Deve retornar código Python para diagrama."""
        mock_exec.return_value = self._mock_exec_result()
        response = client.post(
            "/gerar-analise-completa",
            json={"descricao": "Circuito RC série"}
        )

        data = response.json()
        assert "codigo_diagrama" in data
        assert "import" in data.get("codigo_diagrama", "")

    @pytest.mark.api
    def test_analise_completa_descricao_invalida(self, client):
        """Deve rejeitar descrição inválida."""
        response = client.post(
            "/gerar-analise-completa",
            json={"descricao": "x"}
        )

        assert response.status_code == 422

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    def test_analise_completa_roda_verificacao_de_ft(self, mock_exec, client, mock_llm_analise):
        """/gerar-analise-completa também deve expor os campos de verificação (sem retry)."""
        mock_exec.return_value = self._mock_exec_result()
        response = client.post(
            "/gerar-analise-completa",
            json={"descricao": "Circuito RC série com saída no capacitor"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["verificacao_executada"] is True
        assert data["verificacao_ft_ok"] is True
        assert data["nova_tentativa_pos_verificacao"] is False
        mock_llm_analise.generate.assert_called_once()

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    def test_analise_completa_sem_grafo_nao_executa_verificacao(
        self, mock_exec, client, mock_llm_analise
    ):
        """Resposta sem 'grafo_diagrama' não deve quebrar nem falsamente reprovar."""
        mock_exec.return_value = self._mock_exec_result()
        response = client.post(
            "/gerar-analise-completa",
            json={"descricao": "Circuito RC série com saída no capacitor"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["verificacao_grafo_executada"] is False
        assert data["verificacao_grafo_ok"] is True

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    def test_analise_completa_valida_grafo_coerente(self, mock_exec, client):
        """LLM emite grafo_diagrama coerente com a FT -> verificacao_grafo_ok=True."""
        mock_exec.return_value = self._mock_exec_result()
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
        with patch("main.get_llm_service") as mock_get_llm:
            service = MagicMock()
            service.generate.return_value = {
                "lei_aplicada": "Lei de Kirchhoff das Tensões (LKT)",
                "equacao_diferencial": "RC dVc/dt + Vc = Vin",
                "passos_laplace": "Aplicando Laplace: RCs*Vc(s) + Vc(s) = Vin(s)",
                "funcao_transferencia": "G(s) = 1 / (RCs + 1)",
                "analise_resultado": "Sistema de 1a ordem, estável.",
                "codigo_diagrama": "import matplotlib.pyplot as plt\nplt.plot([0])\nplt.show()",
                "grafo_diagrama": grafo,
            }
            mock_get_llm.return_value = service

            response = client.post(
                "/gerar-analise-completa",
                json={"descricao": "Circuito RC série com saída no capacitor"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["verificacao_grafo_executada"] is True
        assert data["verificacao_grafo_ok"] is True
        assert data["mensagem_verificacao_grafo"] is None

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    def test_analise_completa_grafo_malformado_nao_quebra_resposta(self, mock_exec, client):
        """Grafo com estrutura inválida sinaliza falha, não derruba a API."""
        mock_exec.return_value = self._mock_exec_result()
        grafo_sem_saida = {
            "nos": [
                {"id": "u", "tipo": "entrada"},
                {"id": "g", "tipo": "bloco", "ganho": "1/(R*C*s+1)"},
            ],
            "arestas": [{"origem": "u", "destino": "g", "sinal": "+"}],
        }
        with patch("main.get_llm_service") as mock_get_llm:
            service = MagicMock()
            service.generate.return_value = {
                "lei_aplicada": "Lei de Kirchhoff das Tensões (LKT)",
                "equacao_diferencial": "RC dVc/dt + Vc = Vin",
                "passos_laplace": "Aplicando Laplace: RCs*Vc(s) + Vc(s) = Vin(s)",
                "funcao_transferencia": "G(s) = 1 / (RCs + 1)",
                "analise_resultado": "Sistema de 1a ordem, estável.",
                "codigo_diagrama": "import matplotlib.pyplot as plt\nplt.plot([0])\nplt.show()",
                "grafo_diagrama": grafo_sem_saida,
            }
            mock_get_llm.return_value = service

            response = client.post(
                "/gerar-analise-completa",
                json={"descricao": "Circuito RC série com saída no capacitor"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["verificacao_grafo_executada"] is True
        assert data["verificacao_grafo_ok"] is False
        assert data["mensagem_verificacao_grafo"] is not None


# ============================================================================
# TESTES: Endpoint /validar-minha-resposta
# ============================================================================

class TestEndpointDiagrama:
    """Diagrama por FT e FT+diagrama incluem execução automática."""

    _PNG_1X1 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    def test_gerar_diagrama_por_ft_retorna_imagens(
        self, mock_exec, client, mock_llm_diagram_por_ft
    ):
        mock_exec.return_value = DiagramExecResult(
            diagramas_png_base64=[self._PNG_1X1],
            execucao_ok=True,
            log_execucao="",
            diagramas_arquivos=["diagrams/diagrama_rota3_ex1.png"],
        )
        response = client.post(
            "/gerar-diagrama-por-ft",
            json={"funcao_transferencia": "G(s) = 1/(s+1)"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "codigo_diagrama" in data
        assert data["execucao_diagrama_ok"] is True
        assert len(data["diagramas_png_base64"]) == 1
        mock_exec.assert_called_once()

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    def test_gerar_diagrama_por_ft_valida_grafo_coerente(self, mock_exec, client):
        """LLM emite grafo_diagrama coerente com a FT -> verificacao_grafo_ok=True."""
        mock_exec.return_value = DiagramExecResult(
            diagramas_png_base64=[self._PNG_1X1],
            execucao_ok=True,
            log_execucao="",
            diagramas_arquivos=["diagrams/diagrama_rota3_ex1.png"],
        )
        grafo = {
            "nos": [
                {"id": "u", "tipo": "entrada"},
                {"id": "g", "tipo": "bloco", "ganho": "1/(s+1)"},
                {"id": "y", "tipo": "saida"},
            ],
            "arestas": [
                {"origem": "u", "destino": "g", "sinal": "+"},
                {"origem": "g", "destino": "y", "sinal": "+"},
            ],
        }
        with patch("main.get_llm_service") as mock_get_llm:
            service = MagicMock()
            service.generate.return_value = {
                "codigo_diagrama": "import matplotlib.pyplot as plt\nplt.plot([0])\nplt.show()",
                "grafo_diagrama": grafo,
            }
            mock_get_llm.return_value = service

            response = client.post(
                "/gerar-diagrama-por-ft",
                json={"funcao_transferencia": "G(s) = 1/(s+1)"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["verificacao_grafo_executada"] is True
        assert data["verificacao_grafo_ok"] is True
        assert data["mensagem_verificacao_grafo"] is None

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    def test_gerar_diagrama_por_ft_sem_grafo_nao_executa_verificacao(
        self, mock_exec, client, mock_llm_diagram_por_ft
    ):
        """Resposta antiga do LLM sem 'grafo_diagrama' não deve quebrar nem falsamente reprovar."""
        mock_exec.return_value = DiagramExecResult(
            diagramas_png_base64=[self._PNG_1X1],
            execucao_ok=True,
            log_execucao="",
            diagramas_arquivos=["diagrams/diagrama_rota3_ex1.png"],
        )
        response = client.post(
            "/gerar-diagrama-por-ft",
            json={"funcao_transferencia": "G(s) = 1/(s+1)"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["verificacao_grafo_executada"] is False
        assert data["verificacao_grafo_ok"] is True

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    def test_gerar_diagrama_por_ft_grafo_malformado_nao_quebra_resposta(self, mock_exec, client):
        """Grafo com estrutura inválida (ex.: sem nó 'saida') sinaliza falha, não derruba a API."""
        mock_exec.return_value = DiagramExecResult(
            diagramas_png_base64=[self._PNG_1X1],
            execucao_ok=True,
            log_execucao="",
            diagramas_arquivos=["diagrams/diagrama_rota3_ex1.png"],
        )
        grafo_sem_saida = {
            "nos": [
                {"id": "u", "tipo": "entrada"},
                {"id": "g", "tipo": "bloco", "ganho": "1/(s+1)"},
            ],
            "arestas": [{"origem": "u", "destino": "g", "sinal": "+"}],
        }
        with patch("main.get_llm_service") as mock_get_llm:
            service = MagicMock()
            service.generate.return_value = {
                "codigo_diagrama": "import matplotlib.pyplot as plt\nplt.plot([0])\nplt.show()",
                "grafo_diagrama": grafo_sem_saida,
            }
            mock_get_llm.return_value = service

            response = client.post(
                "/gerar-diagrama-por-ft",
                json={"funcao_transferencia": "G(s) = 1/(s+1)"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["verificacao_grafo_executada"] is True
        assert data["verificacao_grafo_ok"] is False
        assert data["mensagem_verificacao_grafo"] is not None

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    def test_gerar_diagrama_por_ft_retry_quando_ft_nao_parseia(self, mock_exec, client):
        """FT de entrada sem '=' deve disparar o prompt de correção (antes órfão) e chamar o LLM 2x."""
        mock_exec.return_value = DiagramExecResult(
            diagramas_png_base64=[self._PNG_1X1],
            execucao_ok=True,
            log_execucao="",
            diagramas_arquivos=["diagrams/diagrama_rota3_ex1.png"],
        )
        with patch("main.get_llm_service") as mock_get_llm:
            service = MagicMock()
            service.generate.side_effect = [
                {"codigo_diagrama": "import matplotlib.pyplot as plt\nplt.plot([0])\nplt.show()"},
                {"codigo_diagrama": "import matplotlib.pyplot as plt\nplt.plot([1])\nplt.show()"},
            ]
            mock_get_llm.return_value = service

            response = client.post(
                "/gerar-diagrama-por-ft",
                json={"funcao_transferencia": "isso nao eh uma FT valida"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["verificacao_ft_ok"] is False
        assert data["nova_tentativa_pos_verificacao"] is True
        assert service.generate.call_count == 2

    @pytest.mark.api
    @patch("main.execute_diagram_python")
    def test_gerar_ft_e_diagrama_retorna_imagens(
        self, mock_exec, client, mock_llm_ft_e_diagrama
    ):
        mock_exec.return_value = DiagramExecResult(
            diagramas_png_base64=[self._PNG_1X1],
            execucao_ok=True,
            log_execucao="",
            diagramas_arquivos=["diagrams/diagrama_rota3_ex1.png"],
        )
        response = client.post(
            "/gerar-ft-e-diagrama",
            json={"descricao": "Circuito RC série com saída no capacitor para teste"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["funcao_transferencia"]
        assert len(data["diagramas_png_base64"]) == 1


class TestEndpointValidacao:
    """Testes para o endpoint de validação."""
    
    @pytest.mark.api
    def test_validacao_sucesso(self, client, mock_llm_validacao):
        """Deve validar resposta com sucesso."""
        response = client.post(
            "/validar-minha-resposta",
            json={
                "descricao": "Circuito RC série, saída no capacitor",
                "funcao_transferencia_usuario": "G(s) = 1 / (RCs + 1)"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "resposta_correta" in data
        assert "feedback" in data
        assert "solucao_correta" in data
    
    @pytest.mark.api
    def test_validacao_resposta_correta(self, client, mock_llm_validacao):
        """Deve indicar resposta correta."""
        response = client.post(
            "/validar-minha-resposta",
            json={
                "descricao": "Circuito RC série",
                "funcao_transferencia_usuario": "G(s) = 1 / (RCs + 1)"
            }
        )
        
        data = response.json()
        assert data["resposta_correta"] is True
    
    @pytest.mark.api
    def test_validacao_sem_ft_usuario(self, client):
        """Deve rejeitar sem FT do usuário."""
        response = client.post(
            "/validar-minha-resposta",
            json={"descricao": "Circuito RC série"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.api
    def test_validacao_campos_vazios(self, client):
        """Deve rejeitar campos vazios."""
        response = client.post(
            "/validar-minha-resposta",
            json={
                "descricao": "",
                "funcao_transferencia_usuario": ""
            }
        )
        
        assert response.status_code == 422


# ============================================================================
# TESTES: Tratamento de Erros
# ============================================================================

class TestTratamentoErros:
    """Testes para tratamento de erros da API."""
    
    @pytest.mark.api
    def test_endpoint_inexistente(self, client):
        """Deve retornar 404 para endpoint inexistente."""
        response = client.get("/endpoint-que-nao-existe")
        
        assert response.status_code == 404
    
    @pytest.mark.api
    def test_metodo_nao_permitido(self, client):
        """Deve retornar 405 para método não permitido."""
        response = client.get("/gerar-apenas-ft")
        
        assert response.status_code == 405
    
    @pytest.mark.api
    def test_corpo_json_invalido(self, client):
        """Deve retornar erro para JSON inválido."""
        response = client.post(
            "/gerar-apenas-ft",
            content="isso não é json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.api
    def test_erro_llm_retorna_500(self, client):
        """Deve retornar 500 quando LLM falha."""
        with patch('main.get_llm_service') as mock:
            from llm_service import LLMError
            service = MagicMock()
            service.generate.side_effect = LLMError("Falha no LLM")
            mock.return_value = service
            
            response = client.post(
                "/gerar-apenas-ft",
                json={"descricao": "Circuito RC série com saída no capacitor"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert data["sucesso"] is False
            assert "erro" in data


# ============================================================================
# TESTES: CORS
# ============================================================================

class TestCORS:
    """Testes para configuração de CORS."""
    
    @pytest.mark.api
    def test_cors_permite_origem(self, client):
        """CORS deve permitir origens configuradas."""
        response = client.options(
            "/gerar-apenas-ft",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # Deve aceitar preflight ou retornar headers CORS
        assert response.status_code in [200, 405]


# ============================================================================
# TESTES: Documentação
# ============================================================================

class TestDocumentacao:
    """Testes para documentação automática."""
    
    @pytest.mark.api
    def test_openapi_disponivel(self, client):
        """OpenAPI schema deve estar disponível."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
    
    @pytest.mark.api
    def test_swagger_ui_disponivel(self, client):
        """Swagger UI deve estar disponível."""
        response = client.get("/docs")
        
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_redoc_disponivel(self, client):
        """ReDoc deve estar disponível."""
        response = client.get("/redoc")
        
        assert response.status_code == 200
