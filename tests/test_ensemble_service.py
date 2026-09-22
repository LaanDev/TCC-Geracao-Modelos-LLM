"""
Testes do orquestrador de Ensemble (ensemble_service.py).

Os provedores são mockados via substituição de `_PROVIDERS` — o dict é lido
de novo a cada chamada, então isso substitui a função usada.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ensemble_service
from ensemble_service import (
    EnsembleOutcome,
    ProviderResponse,
    _agrupar_por_equivalencia,
    provedores_disponiveis,
    run_ensemble_analise,
)


def _analise(ft: str) -> dict:
    return {
        "lei_aplicada": "LKT",
        "equacao_diferencial": "EDO",
        "passos_laplace": "Laplace",
        "funcao_transferencia": ft,
        "analise_resultado": "ok",
    }


def _fake_provider(nome, retorno=None, excecao=None):
    def chamada(prompt):
        if excecao is not None:
            raise excecao
        return retorno

    return (lambda: True, chamada, lambda: f"modelo-fake-{nome}")


@pytest.mark.unit
class TestProvedoresDisponiveis:
    def test_sem_nenhuma_chave_nenhum_provedor(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.google_api_key", "")
        monkeypatch.setattr("ensemble_service.settings.openai_api_key", None)
        monkeypatch.setattr("ensemble_service.settings.anthropic_api_key", None)
        monkeypatch.setattr("ensemble_service.settings.groq_api_key", None)
        assert provedores_disponiveis() == []

    def test_so_provedores_com_chave_configurada(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.google_api_key", "chave-google")
        monkeypatch.setattr("ensemble_service.settings.openai_api_key", None)
        monkeypatch.setattr("ensemble_service.settings.anthropic_api_key", "chave-anthropic")
        monkeypatch.setattr("ensemble_service.settings.groq_api_key", None)
        assert provedores_disponiveis() == ["google", "anthropic"]


@pytest.mark.unit
class TestAgruparPorEquivalencia:
    def test_fts_equivalentes_entram_no_mesmo_grupo(self):
        respostas = [
            ProviderResponse("google", "m1", True, "G(s) = 1 / (RCs + 1)", _analise("G(s) = 1 / (RCs + 1)")),
            ProviderResponse("openai", "m2", True, "G(s) = 1 / (1 + RCs)", _analise("G(s) = 1 / (1 + RCs)")),
        ]
        grupos = _agrupar_por_equivalencia(respostas)
        assert len(grupos) == 1
        assert len(grupos[0]) == 2

    def test_fts_diferentes_ficam_em_grupos_separados(self):
        respostas = [
            ProviderResponse("google", "m1", True, "G(s) = 1 / (RCs + 1)", _analise("G(s) = 1 / (RCs + 1)")),
            ProviderResponse("openai", "m2", True, "G(s) = 1 / (RCs + 2)", _analise("G(s) = 1 / (RCs + 2)")),
        ]
        grupos = _agrupar_por_equivalencia(respostas)
        assert len(grupos) == 2

    def test_falha_e_ignorada(self):
        respostas = [
            ProviderResponse("google", "m1", True, "G(s) = 1 / (RCs + 1)", _analise("G(s) = 1 / (RCs + 1)")),
            ProviderResponse("openai", "m2", False, None, erro="timeout"),
        ]
        grupos = _agrupar_por_equivalencia(respostas)
        assert len(grupos) == 1
        assert len(grupos[0]) == 1

    def test_ft_nao_parseavel_e_ignorada(self):
        respostas = [
            ProviderResponse("google", "m1", True, "G(s) = 1 / (RCs + 1)", _analise("G(s) = 1 / (RCs + 1)")),
            ProviderResponse("openai", "m2", True, "isso não é uma função de transferência", _analise("x")),
        ]
        grupos = _agrupar_por_equivalencia(respostas)
        assert len(grupos) == 1
        assert grupos[0][0].provedor == "google"


@pytest.mark.unit
class TestRunEnsembleAnalise:
    def test_menos_de_dois_provedores_nao_vota_mas_devolve_payload(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.ensemble_enabled", True)
        monkeypatch.setattr(
            ensemble_service,
            "_PROVIDERS",
            {"google": _fake_provider("google", retorno=_analise("G(s) = 1/(s+1)"))},
        )
        outcome = run_ensemble_analise("um sistema qualquer longo")
        assert outcome.executado is False
        assert outcome.payload_vencedor is not None
        assert outcome.provedor_vencedor == "google"
        assert "pelo menos 2 provedores" in outcome.mensagem

    def test_ensemble_desabilitado_usa_so_o_primeiro(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.ensemble_enabled", False)
        monkeypatch.setattr(
            ensemble_service,
            "_PROVIDERS",
            {
                "google": _fake_provider("google", retorno=_analise("G(s) = 1/(s+1)")),
                "openai": _fake_provider("openai", retorno=_analise("G(s) = 1/(s+1)")),
            },
        )
        outcome = run_ensemble_analise("um sistema qualquer longo")
        assert outcome.executado is False
        assert len(outcome.respostas) == 1
        assert outcome.provedor_vencedor == "google"

    def test_dois_provedores_concordam_escolhe_payload_vencedor(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.ensemble_enabled", True)
        monkeypatch.setattr(
            ensemble_service,
            "_PROVIDERS",
            {
                "google": _fake_provider("google", retorno=_analise("G(s) = 1 / (RCs + 1)")),
                "openai": _fake_provider("openai", retorno=_analise("G(s) = 1 / (1 + RCs)")),
            },
        )
        outcome = run_ensemble_analise("circuito RC série")
        assert outcome.executado is True
        assert outcome.concordancia == "2/2"
        assert outcome.payload_vencedor is not None
        assert outcome.provedor_vencedor == "google"

    def test_maioria_vence_quando_um_provedor_diverge(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.ensemble_enabled", True)
        payload_ok = _analise("G(s) = 1 / (RCs + 1)")
        payload_ok["lei_aplicada"] = "vencedor"
        monkeypatch.setattr(
            ensemble_service,
            "_PROVIDERS",
            {
                "google": _fake_provider("google", retorno=payload_ok),
                "openai": _fake_provider("openai", retorno=_analise("G(s) = 1 / (1 + RCs)")),
                "anthropic": _fake_provider("anthropic", retorno=_analise("G(s) = 1 / (RCs + 2)")),
            },
        )
        outcome = run_ensemble_analise("circuito RC série")
        assert outcome.executado is True
        assert outcome.concordancia == "2/3"
        assert outcome.payload_vencedor["lei_aplicada"] == "vencedor"

    def test_provedor_com_erro_nao_derruba_o_ensemble(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.ensemble_enabled", True)
        monkeypatch.setattr(
            ensemble_service,
            "_PROVIDERS",
            {
                "google": _fake_provider("google", retorno=_analise("G(s) = 1 / (RCs + 1)")),
                "openai": _fake_provider("openai", excecao=RuntimeError("chave inválida")),
            },
        )
        outcome = run_ensemble_analise("circuito RC série")
        assert outcome.executado is True
        assert outcome.concordancia == "1/1"
        falhas = [r for r in outcome.respostas if not r.sucesso]
        assert len(falhas) == 1
        assert falhas[0].erro == "chave inválida"

    def test_nenhuma_ft_parseavel_nao_gera_consenso(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.ensemble_enabled", True)
        ruim = _analise("texto sem FT nenhuma")
        monkeypatch.setattr(
            ensemble_service,
            "_PROVIDERS",
            {
                "google": _fake_provider("google", retorno=ruim),
                "openai": _fake_provider("openai", retorno=_analise("outro texto sem FT")),
            },
        )
        outcome = run_ensemble_analise("um sistema qualquer longo")
        assert outcome.executado is True
        assert outcome.consenso_ft is None
        assert "sem consenso" in outcome.mensagem.lower()
