"""
Testes unitários para os schemas Pydantic.
"""

import os
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import AnaliseCompletaResponse, ErrorResponse, ProblemaRequest


class TestProblemaRequest:
    @pytest.mark.unit
    def test_problema_request_valido(self):
        request = ProblemaRequest(descricao="Circuito RC série com saída no capacitor")
        assert request.descricao == "Circuito RC série com saída no capacitor"

    @pytest.mark.unit
    def test_problema_request_descricao_muito_curta(self):
        with pytest.raises(ValidationError):
            ProblemaRequest(descricao="RC")

    @pytest.mark.unit
    def test_problema_request_sem_descricao(self):
        with pytest.raises(ValidationError):
            ProblemaRequest()


class TestAnaliseCompletaResponse:
    @pytest.mark.unit
    def test_analise_completa_valida(self):
        response = AnaliseCompletaResponse(
            lei_aplicada="Lei de Kirchhoff das Tensões",
            equacao_diferencial="RC dVc/dt + Vc = Vin",
            passos_laplace="1. Aplicar Laplace...",
            funcao_transferencia="G(s) = 1 / (RCs + 1)",
            analise_resultado="Sistema de 1ª ordem, estável",
        )
        assert response.lei_aplicada == "Lei de Kirchhoff das Tensões"
        assert response.codigo_diagrama is None
        assert response.ensemble_executado is False

    @pytest.mark.unit
    def test_analise_completa_com_codigo(self):
        response = AnaliseCompletaResponse(
            lei_aplicada="2ª Lei de Newton",
            equacao_diferencial="M d²x/dt² + B dx/dt + Kx = F",
            passos_laplace="Aplicando Laplace...",
            funcao_transferencia="G(s) = 1 / (Ms² + Bs + K)",
            analise_resultado="Sistema de 2ª ordem",
            codigo_diagrama="import control as ctrl\nG = ctrl.tf([1], [M, B, K])",
        )
        assert "import control" in response.codigo_diagrama

    @pytest.mark.unit
    def test_analise_completa_campo_faltando(self):
        with pytest.raises(ValidationError):
            AnaliseCompletaResponse(lei_aplicada="Lei de Newton")


class TestErrorResponse:
    @pytest.mark.unit
    def test_error_response_basica(self):
        response = ErrorResponse(erro="Falha na comunicação com o LLM")
        assert response.sucesso is False

    @pytest.mark.unit
    def test_error_response_com_resposta_bruta(self):
        response = ErrorResponse(erro="JSON inválido", resposta_bruta="não é json")
        assert response.resposta_bruta is not None


class TestSerializacao:
    @pytest.mark.unit
    def test_problema_request_to_dict(self):
        data = ProblemaRequest(descricao="Sistema RC").model_dump()
        assert data["descricao"] == "Sistema RC"

    @pytest.mark.unit
    def test_analise_completa_to_json(self):
        json_str = AnaliseCompletaResponse(
            lei_aplicada="LKT",
            equacao_diferencial="EDO",
            passos_laplace="Passos",
            funcao_transferencia="G(s)",
            analise_resultado="Análise",
        ).model_dump_json()
        assert "LKT" in json_str
