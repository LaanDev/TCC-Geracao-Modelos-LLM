"""
Testes unitários para os schemas Pydantic.
Verifica validação de dados de entrada e saída.
"""

import pytest
from pydantic import ValidationError

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import (
    ProblemaRequest,
    ValidacaoRequest,
    FuncaoTransferenciaResponse,
    AnaliseCompletaResponse,
    ValidacaoResponse,
    ErrorResponse
)


# ============================================================================
# TESTES: ProblemaRequest
# ============================================================================

class TestProblemaRequest:
    """Testes para o schema de requisição de problema."""
    
    @pytest.mark.unit
    def test_problema_request_valido(self):
        """Deve aceitar descrição válida."""
        request = ProblemaRequest(
            descricao="Circuito RC série com saída no capacitor"
        )
        assert request.descricao == "Circuito RC série com saída no capacitor"
    
    @pytest.mark.unit
    def test_problema_request_descricao_longa(self):
        """Deve aceitar descrição longa e detalhada."""
        descricao_longa = """
        Um sistema mecânico é composto por um bloco de massa M = 2kg, 
        conectado a uma parede por uma mola de constante elástica K = 100 N/m 
        e um amortecedor viscoso com coeficiente B = 10 Ns/m. Uma força 
        externa F(t) é aplicada ao bloco. Considere o deslocamento x(t) 
        como saída e a força F(t) como entrada.
        """
        request = ProblemaRequest(descricao=descricao_longa)
        assert len(request.descricao) > 100
    
    @pytest.mark.unit
    def test_problema_request_descricao_muito_curta(self):
        """Deve rejeitar descrição muito curta (< 10 caracteres)."""
        with pytest.raises(ValidationError) as exc_info:
            ProblemaRequest(descricao="RC")
        
        assert "min_length" in str(exc_info.value) or "String should have at least" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_problema_request_descricao_vazia(self):
        """Deve rejeitar descrição vazia."""
        with pytest.raises(ValidationError):
            ProblemaRequest(descricao="")
    
    @pytest.mark.unit
    def test_problema_request_sem_descricao(self):
        """Deve rejeitar quando descrição não é fornecida."""
        with pytest.raises(ValidationError):
            ProblemaRequest()


# ============================================================================
# TESTES: ValidacaoRequest
# ============================================================================

class TestValidacaoRequest:
    """Testes para o schema de requisição de validação."""
    
    @pytest.mark.unit
    def test_validacao_request_valida(self):
        """Deve aceitar dados válidos."""
        request = ValidacaoRequest(
            descricao="Circuito RC série",
            funcao_transferencia_usuario="G(s) = 1 / (RCs + 1)"
        )
        assert request.descricao == "Circuito RC série"
        assert request.funcao_transferencia_usuario == "G(s) = 1 / (RCs + 1)"
    
    @pytest.mark.unit
    def test_validacao_request_ft_complexa(self):
        """Deve aceitar FT com notação complexa."""
        request = ValidacaoRequest(
            descricao="Sistema de segunda ordem",
            funcao_transferencia_usuario="G(s) = ωn² / (s² + 2ζωns + ωn²)"
        )
        assert "ωn" in request.funcao_transferencia_usuario
    
    @pytest.mark.unit
    def test_validacao_request_sem_ft(self):
        """Deve rejeitar quando FT não é fornecida."""
        with pytest.raises(ValidationError):
            ValidacaoRequest(descricao="Circuito RC série")


# ============================================================================
# TESTES: FuncaoTransferenciaResponse
# ============================================================================

class TestFuncaoTransferenciaResponse:
    """Testes para o schema de resposta de FT."""
    
    @pytest.mark.unit
    def test_ft_response_valida(self):
        """Deve aceitar FT válida."""
        response = FuncaoTransferenciaResponse(
            funcao_transferencia="G(s) = 1 / (s + 1)"
        )
        assert "G(s)" in response.funcao_transferencia
    
    @pytest.mark.unit
    def test_ft_response_segunda_ordem(self):
        """Deve aceitar FT de segunda ordem."""
        response = FuncaoTransferenciaResponse(
            funcao_transferencia="G(s) = 1 / (s² + 2s + 1)"
        )
        assert "s²" in response.funcao_transferencia
    
    @pytest.mark.unit
    def test_ft_response_sem_ft(self):
        """Deve rejeitar quando FT não é fornecida."""
        with pytest.raises(ValidationError):
            FuncaoTransferenciaResponse()


# ============================================================================
# TESTES: AnaliseCompletaResponse
# ============================================================================

class TestAnaliseCompletaResponse:
    """Testes para o schema de resposta de análise completa."""
    
    @pytest.mark.unit
    def test_analise_completa_valida(self):
        """Deve aceitar análise completa com todos os campos."""
        response = AnaliseCompletaResponse(
            lei_aplicada="Lei de Kirchhoff das Tensões",
            equacao_diferencial="RC dVc/dt + Vc = Vin",
            passos_laplace="1. Aplicar Laplace...",
            funcao_transferencia="G(s) = 1 / (RCs + 1)",
            analise_resultado="Sistema de 1ª ordem, estável"
        )
        assert response.lei_aplicada == "Lei de Kirchhoff das Tensões"
        assert response.codigo_diagrama is None  # Campo opcional
    
    @pytest.mark.unit
    def test_analise_completa_com_codigo(self):
        """Deve aceitar análise com código de diagrama."""
        response = AnaliseCompletaResponse(
            lei_aplicada="2ª Lei de Newton",
            equacao_diferencial="M d²x/dt² + B dx/dt + Kx = F",
            passos_laplace="Aplicando Laplace...",
            funcao_transferencia="G(s) = 1 / (Ms² + Bs + K)",
            analise_resultado="Sistema de 2ª ordem",
            codigo_diagrama="import control as ctrl\nG = ctrl.tf([1], [M, B, K])"
        )
        assert response.codigo_diagrama is not None
        assert "import control" in response.codigo_diagrama
    
    @pytest.mark.unit
    def test_analise_completa_campo_faltando(self):
        """Deve rejeitar quando campo obrigatório falta."""
        with pytest.raises(ValidationError):
            AnaliseCompletaResponse(
                lei_aplicada="Lei de Newton",
                # Faltando outros campos obrigatórios
            )


# ============================================================================
# TESTES: ValidacaoResponse
# ============================================================================

class TestValidacaoResponse:
    """Testes para o schema de resposta de validação."""
    
    @pytest.mark.unit
    def test_validacao_response_correta(self):
        """Deve aceitar validação com resposta correta."""
        response = ValidacaoResponse(
            resposta_correta=True,
            feedback="Parabéns! Sua resposta está correta.",
            solucao_correta="G(s) = 1 / (RCs + 1)"
        )
        assert response.resposta_correta is True
    
    @pytest.mark.unit
    def test_validacao_response_incorreta(self):
        """Deve aceitar validação com resposta incorreta."""
        response = ValidacaoResponse(
            resposta_correta=False,
            feedback="O numerador está incorreto. Deveria ser 1.",
            solucao_correta="G(s) = 1 / (RCs + 1)"
        )
        assert response.resposta_correta is False
        assert "incorreto" in response.feedback.lower()
    
    @pytest.mark.unit
    def test_validacao_response_sem_feedback(self):
        """Deve rejeitar quando feedback não é fornecido."""
        with pytest.raises(ValidationError):
            ValidacaoResponse(
                resposta_correta=True,
                solucao_correta="G(s) = 1 / (s + 1)"
            )


# ============================================================================
# TESTES: ErrorResponse
# ============================================================================

class TestErrorResponse:
    """Testes para o schema de resposta de erro."""
    
    @pytest.mark.unit
    def test_error_response_basica(self):
        """Deve criar resposta de erro básica."""
        response = ErrorResponse(erro="Falha na comunicação com o LLM")
        assert response.sucesso is False
        assert "Falha" in response.erro
    
    @pytest.mark.unit
    def test_error_response_com_resposta_bruta(self):
        """Deve aceitar resposta bruta do LLM."""
        response = ErrorResponse(
            erro="JSON inválido",
            resposta_bruta="Este não é um JSON válido..."
        )
        assert response.resposta_bruta is not None


# ============================================================================
# TESTES: Serialização JSON
# ============================================================================

class TestSerializacao:
    """Testes de serialização para JSON."""
    
    @pytest.mark.unit
    def test_problema_request_to_dict(self):
        """Deve serializar corretamente para dicionário."""
        request = ProblemaRequest(descricao="Sistema RC")
        data = request.model_dump()
        assert isinstance(data, dict)
        assert data["descricao"] == "Sistema RC"
    
    @pytest.mark.unit
    def test_analise_completa_to_json(self):
        """Deve serializar corretamente para JSON."""
        response = AnaliseCompletaResponse(
            lei_aplicada="LKT",
            equacao_diferencial="EDO",
            passos_laplace="Passos",
            funcao_transferencia="G(s)",
            analise_resultado="Análise"
        )
        json_str = response.model_dump_json()
        assert isinstance(json_str, str)
        assert "LKT" in json_str
