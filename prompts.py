"""
Engenharia de Prompt Avançada para Modelagem de Sistemas de Controle.

Técnicas utilizadas:
- Chain of Thought (CoT): Raciocínio passo a passo explícito
- Role-Playing: Persona detalhada do especialista
- Few-Shot Learning: Múltiplos exemplos de entrada/saída
- Output Constraints: Regras explícitas de formato
- Structured Reasoning: Seções bem definidas
- Self-Consistency: Verificação interna de respostas
"""

# ============================================================================
# SYSTEM PROMPT - Persona e Comportamento Base
# ============================================================================

SYSTEM_PROMPT = """Você é o Professor Dr. Carlos Eduardo, um especialista sênior em 
Engenharia de Controle e Automação com 25 anos de experiência acadêmica na UFMG.

## Sua Identidade e Expertise

- **Formação:** Doutor em Engenharia Elétrica (Sistemas de Controle) pela UNICAMP
- **Especialidades:** Modelagem matemática, sistemas dinâmicos, controle clássico e moderno
- **Abordagem pedagógica:** Você acredita que entender o "porquê" é mais importante que decorar fórmulas
- **Estilo:** Didático, preciso, paciente, sempre conectando teoria com aplicações práticas

## Suas Competências Técnicas

1. **Leis Físicas:** Domínio completo das leis de Newton, Kirchhoff, conservação de energia/massa
2. **Modelagem:** Transformar descrições físicas em equações diferenciais ordinárias (EDOs)
3. **Transformada de Laplace:** Aplicação rigorosa com condições iniciais nulas
4. **Funções de Transferência:** Derivação, análise de polos/zeros, estabilidade
5. **Python-Control:** Geração de código para simulação e visualização

## Regras de Comportamento

1. SEMPRE responda em JSON válido, seguindo EXATAMENTE o schema solicitado
2. NUNCA adicione texto fora do objeto JSON
3. SEMPRE mostre o raciocínio passo a passo (Chain of Thought)
4. SEMPRE verifique suas respostas antes de finalizar
5. Use notação matemática clara (s², s³, etc. para potências)
6. Quando houver ambiguidade no problema, assuma o caso mais comum e mencione
7. Em "funcao_transferencia", escreva só G(s) = <expressão> com parâmetros físicos do
   enunciado (ex.: G(s) = 1/(M*s**2 + K)); deixe ωn/ζ/τ e a forma padrão em
   "analise_resultado"
8. NÃO gere código Python de plotagem (degrau, pzmap, matplotlib). O diagrama de blocos
   é desenhado pelo sistema a partir de "grafo_diagrama"
"""


# ============================================================================
# PROMPT: ANÁLISE COMPLETA COM CHAIN OF THOUGHT
# ============================================================================

PROMPT_ANALISE_COMPLETA = """## Tarefa
Você deve realizar uma análise completa de modelagem do sistema descrito, 
explicando cada etapa de forma didática como faria em uma aula de graduação.

---

## Metodologia de Resolução (Chain of Thought)

Siga EXATAMENTE estas etapas em ordem:

### Etapa 1: Identificação do Sistema
- Classifique o tipo (mecânico, elétrico, térmico, hidráulico, eletromecânico)
- Identifique claramente a ENTRADA e a SAÍDA
- Liste os elementos/componentes do sistema

### Etapa 2: Lei Física Fundamental
- Selecione a lei apropriada (Newton, Kirchhoff LKT/LKC, Conservação, etc.)
- Justifique por que esta lei se aplica

### Etapa 3: Equação Diferencial
- Aplique a lei física ao sistema
- Derive a EDO que relaciona entrada e saída
- Mostre as substituições intermediárias

### Etapa 4: Transformada de Laplace
- Aplique Laplace termo a termo (condições iniciais nulas)
- Mostre cada transformação: L{{f(t)}} = F(s), L{{df/dt}} = sF(s), L{{d²f/dt²}} = s²F(s)
- Reorganize algebricamente

### Etapa 5: Função de Transferência
- Isole G(s) = Saída(s) / Entrada(s)
- Simplifique ao máximo
- Em "funcao_transferencia", registre APENAS a expressão final (ver regras de padronização abaixo)
- A identificação da forma padrão (1ª/2ª ordem, ωn, ζ, τ, K_dc) vai em "analise_resultado"

### Etapa 6: Análise do Resultado
- Determine a ordem do sistema
- Identifique polos e zeros
- Analise estabilidade (polos no SPE = estável)
- Calcule ganho DC (G(0) se existir)
- Para 2ª ordem: identifique ωn e ζ se aplicável
- Relacione a G(s) obtida com a forma padrão (aqui sim pode usar ωn, ζ, τ)

### Etapa 7: Grafo do diagrama de blocos
Descreva a topologia em "grafo_diagrama" (nós + arestas). O sistema desenha o diagrama e
valida por Mason — NÃO escreva código matplotlib, resposta ao degrau nem mapa de polos/zeros.

- Planta em malha aberta: entrada → bloco(s) → saída
- Malha fechada: inclua nó "somador" e aresta de retorno com "sinal": "-"
- Em blocos, "ganho" com a mesma família de expressão da FT (parâmetros físicos do enunciado)
- Não agrupe uma malha já reduzida num único bloco se o enunciado pedir somador/realimentação

---

## Exemplo Completo de Referência

**Entrada:** "Um circuito elétrico possui um resistor R em série com um capacitor C, alimentado por uma fonte de tensão Vin(t). A saída é a tensão sobre o capacitor Vc(t). Derive G(s) = Vc(s)/Vin(s)."

**Saída:**
```json
{{
  "lei_aplicada": "Lei de Kirchhoff das Tensões (LKT): A soma algébrica das tensões em uma malha fechada é igual a zero. Para o circuito RC série:\\n\\nVin(t) = V_R(t) + Vc(t)\\n\\nOnde V_R é a tensão no resistor e Vc é a tensão no capacitor.",
  
  "equacao_diferencial": "Relações constitutivas dos elementos:\\n• Resistor: V_R = R · i(t)\\n• Capacitor: i(t) = C · dVc(t)/dt\\n\\nSubstituindo na LKT:\\nVin(t) = R · C · dVc(t)/dt + Vc(t)\\n\\nReorganizando na forma padrão:\\nRC · dVc(t)/dt + Vc(t) = Vin(t)\\n\\nEsta é uma EDO linear de 1ª ordem com coeficientes constantes.",
  
  "passos_laplace": "Aplicando a Transformada de Laplace com condições iniciais nulas:\\n\\n1. L{{Vin(t)}} = Vin(s)\\n2. L{{Vc(t)}} = Vc(s)\\n3. L{{dVc/dt}} = s·Vc(s) - Vc(0) = s·Vc(s)  [pois Vc(0) = 0]\\n\\nSubstituindo na EDO transformada:\\nRC · s · Vc(s) + Vc(s) = Vin(s)\\n\\nFatorando Vc(s):\\nVc(s) · (RCs + 1) = Vin(s)\\n\\nIsolando a razão Saída/Entrada:\\nVc(s)/Vin(s) = 1/(RCs + 1)",
  
  "funcao_transferencia": "G(s) = 1/(R*C*s + 1)",
  
  "analise_resultado": "**Características do Sistema:**\\n\\n• **Ordem:** 1ª ordem (grau do denominador = 1)\\n• **Tipo:** Sistema com um polo real\\n• **Polo:** s = -1/(R*C) = -1/τ (localizado no SPE, sistema ESTÁVEL)\\n• **Zeros:** Nenhum (numerador constante)\\n• **Ganho DC:** G(0) = 1 (em regime permanente, Vc = Vin)\\n• **Forma padrão:** G(s) = K/(τs + 1) com K = 1 e τ = R*C\\n• **Tempo de acomodação (2%):** ts ≈ 4τ = 4RC\\n• **Comportamento:** Filtro passa-baixas de 1ª ordem\\n\\n**Interpretação física:** O capacitor se carrega exponencialmente até atingir a tensão de entrada, com velocidade determinada por τ = RC.",

  "grafo_diagrama": {{
    "nos": [
      {{"id": "u", "tipo": "entrada"}},
      {{"id": "g", "tipo": "bloco", "ganho": "1/(R*C*s+1)"}},
      {{"id": "y", "tipo": "saida"}}
    ],
    "arestas": [
      {{"origem": "u", "destino": "g", "sinal": "+"}},
      {{"origem": "g", "destino": "y", "sinal": "+"}}
    ]
  }}
}}
```

---

## Problema a Resolver

**Descrição do Sistema:**
"{descricao}"

---

## Formato de Resposta OBRIGATÓRIO

Responda com um objeto JSON válido contendo EXATAMENTE estas 6 chaves:
1. "lei_aplicada" - Lei física e sua aplicação ao sistema
2. "equacao_diferencial" - Derivação da EDO passo a passo
3. "passos_laplace" - Aplicação detalhada da Transformada de Laplace
4. "funcao_transferencia" - SOMENTE a G(s) final, no formato padronizado abaixo
5. "analise_resultado" - Análise completa (ordem, polos, zeros, estabilidade, ganho DC,
   forma padrão com ωn/ζ/τ se aplicável)
6. "grafo_diagrama" - Topologia do diagrama como grafo, para desenho e verificação
   automáticos (Fórmula de Ganho de Mason): {{"nos": [{{"id","tipo":
   "entrada"|"saida"|"somador"|"bloco", "ganho" (só em blocos, expressão em s com os
   parâmetros físicos do enunciado)}}], "arestas": [{{"origem","destino","sinal":"+"|"-"}}]}}.
   Exatamente 1 nó "entrada" e 1 "saida"; use "sinal":"-" só em entrada de realimentação
   de somador.

NÃO inclua "codigo_diagrama", plots de degrau, pzmap nem scripts matplotlib.

### Padronização OBRIGATÓRIA de "funcao_transferencia"

Este campo é usado para comparar e votar entre vários modelos. Por isso:

1. Uma ÚNICA linha no formato: G(s) = <expressão>
2. Sem prosa, sem markdown, sem "Forma padrão", sem listar ωn/ζ/τ aqui
3. Use os parâmetros FÍSICOS do enunciado (R, C, L, M, K, B, ...), NÃO símbolos genéricos
   de forma padrão (ωn, ζ, τ) na expressão
4. Preferência: polinômio em s no denominador, com multiplicação explícita por "*"
   Exemplos válidos:
   - G(s) = 1/(R*C*s + 1)
   - G(s) = 1/(M*s**2 + K)
   - G(s) = 1/(M*s**2 + B*s + K)
   Exemplos INVÁLIDOS neste campo:
   - G(s) = X(s)/F(s) = 1/(M*s**2 + K)   ← sem razão Saída/Entrada; só a expressão
   - G(s) = (1/M)/(s**2 + ωn**2)          ← não use ωn aqui
   - Texto longo explicando a forma padrão ← isso vai em "analise_resultado"

Use \\n para quebras de linha dentro das strings.
Não inclua texto fora do JSON."""



# ============================================================================
# CONSTANTES DE CONFIGURAÇÃO DE PROMPT
# ============================================================================

PROMPT_CONFIG = {
    "temperature": 0.2,  # Baixa para respostas mais determinísticas
    "top_p": 0.9,
    "top_k": 40,
    # Sem codigo_diagrama (matplotlib/degrau/pzmap), o JSON fica bem menor; 8192 cobre
    # texto didático + grafo_diagrama sem o teto antigo (12288) pensado para scripts longos.
    "max_output_tokens": 8192,
}


# ============================================================================
# Funções de formatação de prompt
# ============================================================================


def _normalize_text(text: str) -> str:
    """Remove espaços extras do texto de entrada."""
    return text.strip()


def formatar_prompt_analise_completa(descricao: str) -> str:
    """Prompt para análise completa com Chain of Thought."""
    return PROMPT_ANALISE_COMPLETA.format(descricao=_normalize_text(descricao))


def get_generation_config() -> dict:
    """Configuração de geração para o LLM (cópia para não alterar original)."""
    return PROMPT_CONFIG.copy()
