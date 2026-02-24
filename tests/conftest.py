"""
Configurações e fixtures compartilhadas para os testes.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock das configurações antes de importar os módulos
os.environ.setdefault("GOOGLE_API_KEY", "fake-api-key-for-testing")


# ============================================================================
# FIXTURES DE CONFIGURAÇÃO
# ============================================================================

@pytest.fixture(scope="session")
def mock_settings():
    """Mock das configurações da aplicação."""
    with patch.dict(os.environ, {
        "GOOGLE_API_KEY": "fake-api-key-for-testing",
        "LLM_MODEL": "models/gemma-3-12b-it",
        "LLM_TIMEOUT": "60",
        "LOG_LEVEL": "WARNING"
    }):
        yield


# ============================================================================
# FIXTURES DE DADOS DE TESTE
# ============================================================================

@pytest.fixture
def problema_rc():
    """Problema clássico: Circuito RC."""
    return {
        "descricao": "Um circuito elétrico é composto por um resistor R e um capacitor C em série. A entrada é a tensão da fonte Vin(t) e a saída é a tensão no capacitor Vc(t). Encontre G(s) = Vc(s)/Vin(s).",
        "resposta_esperada": "G(s) = 1 / (RCs + 1)"
    }


@pytest.fixture
def problema_massa_mola():
    """Problema clássico: Sistema massa-mola-amortecedor."""
    return {
        "descricao": "Um sistema mecânico possui uma massa M, uma mola com constante K e um amortecedor com coeficiente B. A entrada é uma força F(t) e a saída é o deslocamento x(t). Encontre G(s) = X(s)/F(s).",
        "resposta_esperada": "G(s) = 1 / (Ms² + Bs + K)"
    }


@pytest.fixture
def problema_rlc():
    """Problema clássico: Circuito RLC série."""
    return {
        "descricao": "Um circuito RLC série com resistor R, indutor L e capacitor C. A entrada é Vin(t) e a saída é a tensão no capacitor Vc(t). Encontre G(s).",
        "resposta_esperada": "G(s) = 1 / (LCs² + RCs + 1)"
    }


@pytest.fixture
def problema_tanque():
    """Problema clássico: Sistema de nível de tanque."""
    return {
        "descricao": "Um tanque cilíndrico tem área de seção transversal A e resistência hidráulica R na saída. A entrada é a vazão qi(t) e a saída é a altura do líquido h(t). Encontre G(s) = H(s)/Qi(s).",
        "resposta_esperada": "G(s) = R / (ARs + 1)"
    }


@pytest.fixture
def validacao_correta():
    """Dados para teste de validação com resposta correta."""
    return {
        "descricao": "Circuito RC série, saída no capacitor",
        "funcao_transferencia_usuario": "G(s) = 1 / (RCs + 1)",
        "esperado_correto": True
    }


@pytest.fixture
def validacao_incorreta():
    """Dados para teste de validação com resposta incorreta."""
    return {
        "descricao": "Circuito RC série, saída no capacitor",
        "funcao_transferencia_usuario": "G(s) = R / (RCs + 1)",
        "esperado_correto": False
    }


# ============================================================================
# FIXTURES DE MOCK DO LLM
# ============================================================================

@pytest.fixture
def mock_llm_response_ft():
    """Mock de resposta do LLM para função de transferência."""
    return {
        "funcao_transferencia": "G(s) = 1 / (RCs + 1)"
    }


@pytest.fixture
def mock_llm_response_completa():
    """Mock de resposta do LLM para análise completa."""
    return {
        "lei_aplicada": "Lei de Kirchhoff das Tensões (LKT)",
        "equacao_diferencial": "RC dVc/dt + Vc = Vin",
        "passos_laplace": "Aplicando Laplace: RCs·Vc(s) + Vc(s) = Vin(s)",
        "funcao_transferencia": "G(s) = 1 / (RCs + 1)",
        "analise_resultado": "Sistema de 1ª ordem, estável, polo em s = -1/RC",
        "codigo_diagrama": "import control as ctrl\nG = ctrl.TransferFunction([1], [R*C, 1])"
    }


@pytest.fixture
def mock_llm_response_validacao_correta():
    """Mock de resposta do LLM para validação correta."""
    return {
        "resposta_correta": True,
        "feedback": "Excelente! Sua resposta está correta.",
        "solucao_correta": "G(s) = 1 / (RCs + 1)"
    }


@pytest.fixture
def mock_llm_response_validacao_incorreta():
    """Mock de resposta do LLM para validação incorreta."""
    return {
        "resposta_correta": False,
        "feedback": "Sua resposta está incorreta. O numerador deveria ser 1, não R.",
        "solucao_correta": "G(s) = 1 / (RCs + 1)"
    }


# ============================================================================
# FIXTURES DO CLIENTE DE TESTE
# ============================================================================

@pytest.fixture
def mock_llm_service():
    """Mock completo do serviço LLM."""
    with patch('main.get_llm_service') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


@pytest.fixture
def test_client(mock_settings):
    """Cliente de teste do FastAPI."""
    # Import after setting up mocks
    from fastapi.testclient import TestClient
    
    # Mock o serviço LLM antes de importar main
    with patch('llm_service.genai'):
        from main import app
        with TestClient(app) as client:
            yield client
