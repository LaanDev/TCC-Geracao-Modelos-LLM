"""
Testes do orquestrador de Ensemble entre provedores de LLM (ensemble_service.py).

Os provedores são mockados via `monkeypatch.setitem` em `_PROVIDERS` — o dict é lido
de novo a cada chamada dentro de `run_ensemble_ft`, então isso substitui de fato a
função usada, diferente de patchar `_call_google` etc. diretamente (que já estariam
"capturadas" dentro da tupla no momento da definição do módulo).
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
    run_ensemble_ft,
    verify_ft_with_ensemble,
)


def _fake_provider(nome, retorno=None, excecao=None):
    """Monta uma tupla (disponivel, chamada, modelo) pronta pra substituir em _PROVIDERS."""

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
    def test_ft_escritas_diferente_mas_iguais_ficam_no_mesmo_grupo(self):
        respostas = [
            ProviderResponse("google", "m1", True, "G(s) = 1 / (RCs + 1)"),
            ProviderResponse("openai", "m2", True, "G(s) = 1 / (1 + RCs)"),
        ]
        grupos = _agrupar_por_equivalencia(respostas)
        assert len(grupos) == 1
        assert len(grupos[0]) == 2

    def test_ft_matematicamente_diferentes_ficam_em_grupos_separados(self):
        respostas = [
            ProviderResponse("google", "m1", True, "G(s) = 1 / (RCs + 1)"),
            ProviderResponse("openai", "m2", True, "G(s) = 1 / (RCs + 2)"),
        ]
        grupos = _agrupar_por_equivalencia(respostas)
        assert len(grupos) == 2

    def test_resposta_sem_sucesso_e_ignorada_no_agrupamento(self):
        respostas = [
            ProviderResponse("google", "m1", True, "G(s) = 1 / (RCs + 1)"),
            ProviderResponse("openai", "m2", False, None, erro="timeout"),
        ]
        grupos = _agrupar_por_equivalencia(respostas)
        assert len(grupos) == 1
        assert len(grupos[0]) == 1

    def test_ft_nao_parseavel_e_ignorada_sem_quebrar_o_agrupamento(self):
        respostas = [
            ProviderResponse("google", "m1", True, "G(s) = 1 / (RCs + 1)"),
            ProviderResponse("openai", "m2", True, "isso não é uma função de transferência"),
        ]
        grupos = _agrupar_por_equivalencia(respostas)
        assert len(grupos) == 1
        assert len(grupos[0]) == 1
        assert grupos[0][0].provedor == "google"


@pytest.mark.unit
class TestRunEnsembleFt:
    def test_menos_de_dois_provedores_nao_executa(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.ensemble_enabled", True)
        monkeypatch.setattr(
            ensemble_service,
            "_PROVIDERS",
            {"google": _fake_provider("google", retorno="G(s) = 1/(s+1)")},
        )
        outcome = run_ensemble_ft("um sistema qualquer")
        assert outcome.executado is False
        assert "pelo menos 2 provedores" in outcome.mensagem

    def test_ensemble_desabilitado_nao_executa_mesmo_com_provedores(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.ensemble_enabled", False)
        monkeypatch.setattr(
            ensemble_service,
            "_PROVIDERS",
            {
                "google": _fake_provider("google", retorno="G(s) = 1/(s+1)"),
                "openai": _fake_provider("openai", retorno="G(s) = 1/(s+1)"),
            },
        )
        outcome = run_ensemble_ft("um sistema qualquer")
        assert outcome.executado is False

    def test_dois_provedores_concordam_gera_consenso(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.ensemble_enabled", True)
        monkeypatch.setattr(
            ensemble_service,
            "_PROVIDERS",
            {
                "google": _fake_provider("google", retorno="G(s) = 1 / (RCs + 1)"),
                "openai": _fake_provider("openai", retorno="G(s) = 1 / (1 + RCs)"),
            },
        )
        outcome = run_ensemble_ft("circuito RC série")
        assert outcome.executado is True
        assert outcome.concordancia == "2/2"
        assert outcome.consenso_ft is not None
        assert len(outcome.respostas) == 2

    def test_maioria_vence_quando_um_provedor_diverge(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.ensemble_enabled", True)
        monkeypatch.setattr(
            ensemble_service,
            "_PROVIDERS",
            {
                "google": _fake_provider("google", retorno="G(s) = 1 / (RCs + 1)"),
                "openai": _fake_provider("openai", retorno="G(s) = 1 / (1 + RCs)"),
                "anthropic": _fake_provider("anthropic", retorno="G(s) = 1 / (RCs + 2)"),
            },
        )
        outcome = run_ensemble_ft("circuito RC série")
        assert outcome.executado is True
        assert outcome.concordancia == "2/3"

    def test_provedor_com_erro_nao_derruba_o_ensemble(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.ensemble_enabled", True)
        monkeypatch.setattr(
            ensemble_service,
            "_PROVIDERS",
            {
                "google": _fake_provider("google", retorno="G(s) = 1 / (RCs + 1)"),
                "openai": _fake_provider("openai", excecao=RuntimeError("chave inválida")),
            },
        )
        outcome = run_ensemble_ft("circuito RC série")
        assert outcome.executado is True
        assert outcome.concordancia == "1/1"
        falhas = [r for r in outcome.respostas if not r.sucesso]
        assert len(falhas) == 1
        assert falhas[0].erro == "chave inválida"

    def test_nenhuma_ft_parseavel_nao_gera_consenso(self, monkeypatch):
        monkeypatch.setattr("ensemble_service.settings.ensemble_enabled", True)
        monkeypatch.setattr(
            ensemble_service,
            "_PROVIDERS",
            {
                "google": _fake_provider("google", retorno="texto sem FT nenhuma"),
                "openai": _fake_provider("openai", retorno="outro texto sem FT"),
            },
        )
        outcome = run_ensemble_ft("um sistema qualquer")
        assert outcome.executado is True
        assert outcome.consenso_ft is None
        assert "sem consenso" in outcome.mensagem.lower()


@pytest.mark.unit
class TestVerifyFtWithEnsemble:
    def test_sem_ensemble_executado_ok_por_falta_de_dados(self, monkeypatch):
        monkeypatch.setattr(
            ensemble_service,
            "run_ensemble_ft",
            lambda descricao: EnsembleOutcome(executado=False, mensagem="menos de 2 provedores"),
        )
        out = verify_ft_with_ensemble("um sistema qualquer", "G(s) = 1/(s+1)")
        assert out.executado is False
        assert out.ok is True

    def test_ft_primaria_equivalente_ao_consenso(self, monkeypatch):
        monkeypatch.setattr(
            ensemble_service,
            "run_ensemble_ft",
            lambda descricao: EnsembleOutcome(
                executado=True, consenso_ft="G(s) = 1 / (1 + RCs)", concordancia="2/2"
            ),
        )
        out = verify_ft_with_ensemble("circuito RC série", "G(s) = 1 / (RCs + 1)")
        assert out.executado is True
        assert out.ok is True
        assert out.mensagem is None

    def test_ft_primaria_diverge_do_consenso(self, monkeypatch):
        monkeypatch.setattr(
            ensemble_service,
            "run_ensemble_ft",
            lambda descricao: EnsembleOutcome(
                executado=True, consenso_ft="G(s) = 1 / (RCs + 2)", concordancia="2/3"
            ),
        )
        out = verify_ft_with_ensemble("circuito RC série", "G(s) = 1 / (RCs + 1)")
        assert out.executado is True
        assert out.ok is False
        assert "não é equivalente" in out.mensagem
