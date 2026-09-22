"""
Testes unitários para o prompt de análise completa.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts import (
    PROMPT_ANALISE_COMPLETA,
    PROMPT_CONFIG,
    SYSTEM_PROMPT,
    formatar_prompt_analise_completa,
    get_generation_config,
)


class TestSystemPrompt:
    @pytest.mark.unit
    def test_system_prompt_existe(self):
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 100

    @pytest.mark.unit
    def test_system_prompt_define_persona(self):
        assert "especialista" in SYSTEM_PROMPT.lower() or "professor" in SYSTEM_PROMPT.lower()

    @pytest.mark.unit
    def test_system_prompt_menciona_json(self):
        assert "JSON" in SYSTEM_PROMPT


class TestPromptAnaliseCompleta:
    @pytest.mark.unit
    def test_prompt_analise_tem_placeholder(self):
        assert "{descricao}" in PROMPT_ANALISE_COMPLETA

    @pytest.mark.unit
    def test_prompt_analise_tem_chain_of_thought(self):
        assert "Etapa" in PROMPT_ANALISE_COMPLETA or "Passo" in PROMPT_ANALISE_COMPLETA

    @pytest.mark.unit
    @pytest.mark.unit
    def test_prompt_analise_solicita_todas_chaves(self):
        chaves = [
            "lei_aplicada",
            "equacao_diferencial",
            "passos_laplace",
            "funcao_transferencia",
            "analise_resultado",
            "grafo_diagrama",
        ]
        for chave in chaves:
            assert chave in PROMPT_ANALISE_COMPLETA, f"Deve solicitar '{chave}'"

    @pytest.mark.unit
    def test_prompt_nao_pede_codigo_matplotlib(self):
        assert "EXATAMENTE estas 6 chaves" in PROMPT_ANALISE_COMPLETA
        assert "NÃO inclua \"codigo_diagrama\"" in PROMPT_ANALISE_COMPLETA
        assert "step_response" not in PROMPT_ANALISE_COMPLETA
        assert "plt.show" not in PROMPT_ANALISE_COMPLETA
        assert "FancyBboxPatch" not in PROMPT_ANALISE_COMPLETA


    @pytest.mark.unit
    def test_prompt_padroniza_funcao_transferencia(self):
        assert "Padronização OBRIGATÓRIA de \"funcao_transferencia\"" in PROMPT_ANALISE_COMPLETA
        assert "G(s) = 1/(M*s**2 + K)" in PROMPT_ANALISE_COMPLETA
        assert '"funcao_transferencia": "G(s) = 1/(R*C*s + 1)"' in PROMPT_ANALISE_COMPLETA


class TestFormatarPromptAnalise:
    @pytest.mark.unit
    def test_formata_descricao(self):
        descricao = "Sistema massa-mola-amortecedor"
        prompt = formatar_prompt_analise_completa(descricao)
        assert descricao in prompt
        assert "{descricao}" not in prompt

    @pytest.mark.unit
    def test_remove_espacos_extras(self):
        prompt = formatar_prompt_analise_completa("  Circuito RC série  ")
        assert "Circuito RC série" in prompt


class TestGenerationConfig:
    @pytest.mark.unit
    def test_config_temperature_baixa(self):
        assert "temperature" in PROMPT_CONFIG
        assert PROMPT_CONFIG["temperature"] <= 0.5

    @pytest.mark.unit
    def test_config_tem_max_tokens(self):
        assert PROMPT_CONFIG["max_output_tokens"] >= 4096

    @pytest.mark.unit
    def test_get_generation_config_retorna_copia(self):
        config1 = get_generation_config()
        config2 = get_generation_config()
        config1["temperature"] = 99
        assert config2["temperature"] != 99
