"""
Testes unitários para os prompts e funções de formatação.
Verifica estrutura, conteúdo e formatação dos prompts.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts import (
    SYSTEM_PROMPT,
    PROMPT_APENAS_FT,
    PROMPT_ANALISE_COMPLETA,
    PROMPT_VALIDAR_RESPOSTA,
    PROMPT_CONFIG,
    formatar_prompt_ft,
    formatar_prompt_analise_completa,
    formatar_prompt_validacao,
    get_generation_config
)


# ============================================================================
# TESTES: SYSTEM_PROMPT
# ============================================================================

class TestSystemPrompt:
    """Testes para o system prompt."""
    
    @pytest.mark.unit
    def test_system_prompt_existe(self):
        """System prompt deve existir e não estar vazio."""
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 100
    
    @pytest.mark.unit
    def test_system_prompt_define_persona(self):
        """System prompt deve definir a persona do especialista."""
        assert "especialista" in SYSTEM_PROMPT.lower() or "professor" in SYSTEM_PROMPT.lower()
    
    @pytest.mark.unit
    def test_system_prompt_menciona_json(self):
        """System prompt deve instruir sobre formato JSON."""
        assert "JSON" in SYSTEM_PROMPT
    
    @pytest.mark.unit
    def test_system_prompt_menciona_competencias(self):
        """System prompt deve listar competências técnicas."""
        competencias = ["Newton", "Kirchhoff", "Laplace", "EDO"]
        encontradas = sum(1 for c in competencias if c in SYSTEM_PROMPT)
        assert encontradas >= 2, "Deve mencionar pelo menos 2 competências técnicas"


# ============================================================================
# TESTES: PROMPT_APENAS_FT
# ============================================================================

class TestPromptApenasFT:
    """Testes para o prompt de função de transferência."""
    
    @pytest.mark.unit
    def test_prompt_ft_tem_placeholder(self):
        """Prompt deve ter placeholder para descrição."""
        assert "{descricao}" in PROMPT_APENAS_FT
    
    @pytest.mark.unit
    def test_prompt_ft_tem_exemplos(self):
        """Prompt deve conter exemplos (few-shot)."""
        assert "Exemplo" in PROMPT_APENAS_FT
        # Deve ter pelo menos 3 exemplos
        assert PROMPT_APENAS_FT.count("Exemplo") >= 3
    
    @pytest.mark.unit
    def test_prompt_ft_menciona_json(self):
        """Prompt deve instruir sobre formato JSON."""
        assert "JSON" in PROMPT_APENAS_FT
        assert "funcao_transferencia" in PROMPT_APENAS_FT
    
    @pytest.mark.unit
    def test_prompt_ft_exemplos_variados(self):
        """Prompt deve ter exemplos de diferentes tipos de sistemas."""
        tipos = ["RC", "massa", "RLC", "RL"]
        encontrados = sum(1 for t in tipos if t in PROMPT_APENAS_FT)
        assert encontrados >= 3, "Deve ter exemplos de pelo menos 3 tipos de sistemas"


# ============================================================================
# TESTES: PROMPT_ANALISE_COMPLETA
# ============================================================================

class TestPromptAnaliseCompleta:
    """Testes para o prompt de análise completa."""
    
    @pytest.mark.unit
    def test_prompt_analise_tem_placeholder(self):
        """Prompt deve ter placeholder para descrição."""
        assert "{descricao}" in PROMPT_ANALISE_COMPLETA
    
    @pytest.mark.unit
    def test_prompt_analise_tem_chain_of_thought(self):
        """Prompt deve usar técnica de Chain of Thought."""
        # Deve ter etapas numeradas ou passos definidos
        assert "Etapa" in PROMPT_ANALISE_COMPLETA or "Passo" in PROMPT_ANALISE_COMPLETA
    
    @pytest.mark.unit
    def test_prompt_analise_solicita_todas_chaves(self):
        """Prompt deve solicitar todas as chaves do schema."""
        chaves = [
            "lei_aplicada",
            "equacao_diferencial",
            "passos_laplace",
            "funcao_transferencia",
            "analise_resultado",
            "codigo_diagrama"
        ]
        for chave in chaves:
            assert chave in PROMPT_ANALISE_COMPLETA, f"Deve solicitar '{chave}'"
    
    @pytest.mark.unit
    def test_prompt_analise_menciona_python_control(self):
        """Prompt deve mencionar biblioteca python-control."""
        assert "control" in PROMPT_ANALISE_COMPLETA.lower()
    
    @pytest.mark.unit
    def test_prompt_analise_tem_exemplo_completo(self):
        """Prompt deve ter pelo menos um exemplo completo."""
        # Verifica se o exemplo tem todas as chaves
        assert "lei_aplicada" in PROMPT_ANALISE_COMPLETA
        assert "import" in PROMPT_ANALISE_COMPLETA  # Código de exemplo


# ============================================================================
# TESTES: PROMPT_VALIDAR_RESPOSTA
# ============================================================================

class TestPromptValidacao:
    """Testes para o prompt de validação."""
    
    @pytest.mark.unit
    def test_prompt_validacao_tem_placeholders(self):
        """Prompt deve ter placeholders para descrição e FT do usuário."""
        assert "{descricao}" in PROMPT_VALIDAR_RESPOSTA
        assert "{funcao_transferencia_usuario}" in PROMPT_VALIDAR_RESPOSTA
    
    @pytest.mark.unit
    def test_prompt_validacao_menciona_equivalencia(self):
        """Prompt deve mencionar equivalência matemática."""
        assert "equivalen" in PROMPT_VALIDAR_RESPOSTA.lower()
    
    @pytest.mark.unit
    def test_prompt_validacao_tem_exemplos_correto_e_incorreto(self):
        """Prompt deve ter exemplos de resposta correta e incorreta."""
        assert "resposta_correta\": true" in PROMPT_VALIDAR_RESPOSTA.lower() or \
               "resposta_correta\": True" in PROMPT_VALIDAR_RESPOSTA
        assert "resposta_correta\": false" in PROMPT_VALIDAR_RESPOSTA.lower() or \
               "resposta_correta\": False" in PROMPT_VALIDAR_RESPOSTA
    
    @pytest.mark.unit
    def test_prompt_validacao_solicita_feedback(self):
        """Prompt deve solicitar feedback construtivo."""
        assert "feedback" in PROMPT_VALIDAR_RESPOSTA
        assert "construtiv" in PROMPT_VALIDAR_RESPOSTA.lower() or \
               "educativ" in PROMPT_VALIDAR_RESPOSTA.lower()


# ============================================================================
# TESTES: Funções de Formatação
# ============================================================================

class TestFormatarPromptFT:
    """Testes para a função formatar_prompt_ft."""
    
    @pytest.mark.unit
    def test_formata_descricao_simples(self):
        """Deve inserir descrição no placeholder."""
        descricao = "Circuito RC série"
        prompt = formatar_prompt_ft(descricao)
        
        assert descricao in prompt
        assert "{descricao}" not in prompt
    
    @pytest.mark.unit
    def test_remove_espacos_extras(self):
        """Deve remover espaços extras da descrição."""
        descricao = "  Circuito RC série  "
        prompt = formatar_prompt_ft(descricao)
        
        assert "Circuito RC série" in prompt
        assert "  Circuito" not in prompt
    
    @pytest.mark.unit
    def test_preserva_conteudo_prompt(self):
        """Deve preservar exemplos e instruções do prompt."""
        prompt = formatar_prompt_ft("Teste")
        
        assert "Exemplo" in prompt
        assert "JSON" in prompt


class TestFormatarPromptAnalise:
    """Testes para a função formatar_prompt_analise_completa."""
    
    @pytest.mark.unit
    def test_formata_descricao(self):
        """Deve inserir descrição no placeholder."""
        descricao = "Sistema massa-mola-amortecedor"
        prompt = formatar_prompt_analise_completa(descricao)
        
        assert descricao in prompt
    
    @pytest.mark.unit
    def test_mantem_estrutura_cot(self):
        """Deve manter estrutura de Chain of Thought."""
        prompt = formatar_prompt_analise_completa("Teste")
        
        assert "Etapa" in prompt or "Passo" in prompt


class TestFormatarPromptValidacao:
    """Testes para a função formatar_prompt_validacao."""
    
    @pytest.mark.unit
    def test_formata_ambos_campos(self):
        """Deve inserir descrição e FT do usuário."""
        descricao = "Circuito RC"
        ft_usuario = "G(s) = 1 / (s + 1)"
        
        prompt = formatar_prompt_validacao(descricao, ft_usuario)
        
        assert descricao in prompt
        assert ft_usuario in prompt
    
    @pytest.mark.unit
    def test_remove_espacos_ambos_campos(self):
        """Deve remover espaços extras de ambos os campos."""
        prompt = formatar_prompt_validacao(
            "  Circuito RC  ",
            "  G(s) = 1  "
        )
        
        assert "Circuito RC" in prompt
        assert "G(s) = 1" in prompt


# ============================================================================
# TESTES: Configuração de Geração
# ============================================================================

class TestGenerationConfig:
    """Testes para a configuração de geração."""
    
    @pytest.mark.unit
    def test_config_existe(self):
        """Configuração deve existir."""
        assert PROMPT_CONFIG is not None
        assert isinstance(PROMPT_CONFIG, dict)
    
    @pytest.mark.unit
    def test_config_tem_temperature(self):
        """Deve definir temperature."""
        assert "temperature" in PROMPT_CONFIG
        assert 0 <= PROMPT_CONFIG["temperature"] <= 1
    
    @pytest.mark.unit
    def test_config_temperature_baixa(self):
        """Temperature deve ser baixa para respostas determinísticas."""
        assert PROMPT_CONFIG["temperature"] <= 0.5
    
    @pytest.mark.unit
    def test_config_tem_max_tokens(self):
        """Deve definir max_output_tokens."""
        assert "max_output_tokens" in PROMPT_CONFIG
        assert PROMPT_CONFIG["max_output_tokens"] >= 4096
    
    @pytest.mark.unit
    def test_get_generation_config_retorna_copia(self):
        """Função deve retornar cópia da config."""
        config1 = get_generation_config()
        config2 = get_generation_config()
        
        # Deve retornar cópias independentes
        config1["temperature"] = 99
        assert config2["temperature"] != 99


# ============================================================================
# TESTES: Qualidade dos Prompts
# ============================================================================

class TestQualidadePrompts:
    """Testes de qualidade geral dos prompts."""
    
    @pytest.mark.unit
    def test_prompts_nao_tem_placeholders_restantes(self):
        """Prompts formatados não devem ter placeholders do template não preenchidos."""
        # Apenas os placeholders usados em .format() nos prompts (texto literal como {polos} em exemplos não conta)
        placeholders_do_template = ("{descricao}", "{funcao_transferencia_usuario}")

        prompt_ft = formatar_prompt_ft("Descrição teste")
        prompt_analise = formatar_prompt_analise_completa("Descrição teste")
        prompt_validacao = formatar_prompt_validacao("Descrição", "G(s) = 1")

        for name, prompt in [
            ("FT", prompt_ft),
            ("Análise", prompt_analise),
            ("Validação", prompt_validacao),
        ]:
            restantes = [p for p in placeholders_do_template if p in prompt]
            assert not restantes, (
                f"Prompt {name} não deve ter placeholders não preenchidos: {restantes}"
            )
    
    @pytest.mark.unit
    def test_prompts_tem_instrucoes_formato(self):
        """Todos os prompts devem ter instruções de formato."""
        prompts = [PROMPT_APENAS_FT, PROMPT_ANALISE_COMPLETA, PROMPT_VALIDAR_RESPOSTA]
        
        for prompt in prompts:
            assert "JSON" in prompt, "Prompt deve instruir sobre formato JSON"
    
    @pytest.mark.unit
    def test_prompts_tem_tamanho_adequado(self):
        """Prompts devem ter tamanho adequado (não muito curtos)."""
        assert len(PROMPT_APENAS_FT) > 1000
        assert len(PROMPT_ANALISE_COMPLETA) > 2000
        assert len(PROMPT_VALIDAR_RESPOSTA) > 1500
