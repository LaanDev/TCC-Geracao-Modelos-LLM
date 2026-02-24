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
7. Forneça código Python funcional e bem comentado"""


# ============================================================================
# PROMPT: GERAR APENAS FUNÇÃO DE TRANSFERÊNCIA
# ============================================================================

PROMPT_APENAS_FT = """## Tarefa
Analise o sistema dinâmico descrito e determine sua função de transferência G(s).

## Processo de Raciocínio (execute mentalmente)
1. Identifique o tipo de sistema (mecânico, elétrico, térmico, hidráulico, etc.)
2. Determine a entrada e a saída do sistema
3. Identifique a lei física aplicável
4. Derive a EDO do sistema
5. Aplique a Transformada de Laplace
6. Isole G(s) = Saída(s) / Entrada(s)
7. Simplifique a expressão final

---

## Exemplos de Referência

### Exemplo 1: Sistema de Primeira Ordem (RC)
**Entrada:** "Circuito com resistor R e capacitor C em série. Entrada: tensão da fonte Vin. Saída: tensão no capacitor Vc."
**Saída:**
```json
{{"funcao_transferencia": "G(s) = 1 / (RCs + 1)"}}
```

### Exemplo 2: Sistema de Segunda Ordem (Massa-Mola-Amortecedor)
**Entrada:** "Bloco de massa M conectado a mola K e amortecedor B. Entrada: força F. Saída: deslocamento x."
**Saída:**
```json
{{"funcao_transferencia": "G(s) = 1 / (Ms² + Bs + K)"}}
```

### Exemplo 3: Sistema de Segunda Ordem (RLC)
**Entrada:** "Circuito RLC série. Entrada: tensão Vin. Saída: tensão no capacitor Vc."
**Saída:**
```json
{{"funcao_transferencia": "G(s) = 1 / (LCs² + RCs + 1)"}}
```

### Exemplo 4: Sistema com Zero (RL)
**Entrada:** "Circuito RL série. Entrada: tensão Vin. Saída: tensão no indutor VL."
**Saída:**
```json
{{"funcao_transferencia": "G(s) = Ls / (Ls + R)"}}
```

### Exemplo 5: Sistema Térmico
**Entrada:** "Corpo com capacitância térmica C e resistência térmica R ao ambiente. Entrada: potência de aquecimento P. Saída: temperatura T."
**Saída:**
```json
{{"funcao_transferencia": "G(s) = R / (RCs + 1)"}}
```

---

## Problema a Resolver

**Descrição do Sistema:**
"{descricao}"

---

## Formato de Resposta OBRIGATÓRIO

Responda APENAS com um objeto JSON válido contendo UMA única chave:
- "funcao_transferencia": string com G(s) no formato "G(s) = numerador / denominador"

Não inclua explicações, comentários ou texto adicional. Apenas o JSON."""


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
- Identifique a forma padrão (1ª ordem, 2ª ordem, etc.)

### Etapa 6: Análise do Resultado
- Determine a ordem do sistema
- Identifique polos e zeros
- Analise estabilidade (polos no SPE = estável)
- Calcule ganho DC (G(0) se existir)
- Para 2ª ordem: identifique ωn e ζ se aplicável

### Etapa 7: Código Python
- Gere código funcional usando biblioteca `control`
- Inclua: criação da FT, resposta ao degrau, gráfico
- Adicione comentários explicativos

---

## Exemplo Completo de Referência

**Entrada:** "Um circuito elétrico possui um resistor R em série com um capacitor C, alimentado por uma fonte de tensão Vin(t). A saída é a tensão sobre o capacitor Vc(t). Derive G(s) = Vc(s)/Vin(s)."

**Saída:**
```json
{{
  "lei_aplicada": "Lei de Kirchhoff das Tensões (LKT): A soma algébrica das tensões em uma malha fechada é igual a zero. Para o circuito RC série:\\n\\nVin(t) = V_R(t) + Vc(t)\\n\\nOnde V_R é a tensão no resistor e Vc é a tensão no capacitor.",
  
  "equacao_diferencial": "Relações constitutivas dos elementos:\\n• Resistor: V_R = R · i(t)\\n• Capacitor: i(t) = C · dVc(t)/dt\\n\\nSubstituindo na LKT:\\nVin(t) = R · C · dVc(t)/dt + Vc(t)\\n\\nReorganizando na forma padrão:\\nRC · dVc(t)/dt + Vc(t) = Vin(t)\\n\\nEsta é uma EDO linear de 1ª ordem com coeficientes constantes.",
  
  "passos_laplace": "Aplicando a Transformada de Laplace com condições iniciais nulas:\\n\\n1. L{{Vin(t)}} = Vin(s)\\n2. L{{Vc(t)}} = Vc(s)\\n3. L{{dVc/dt}} = s·Vc(s) - Vc(0) = s·Vc(s)  [pois Vc(0) = 0]\\n\\nSubstituindo na EDO transformada:\\nRC · s · Vc(s) + Vc(s) = Vin(s)\\n\\nFatorando Vc(s):\\nVc(s) · (RCs + 1) = Vin(s)\\n\\nIsolando a razão Saída/Entrada:\\nVc(s)/Vin(s) = 1/(RCs + 1)",
  
  "funcao_transferencia": "G(s) = Vc(s)/Vin(s) = 1 / (RCs + 1)\\n\\nForma padrão de 1ª ordem: G(s) = K / (τs + 1)\\nOnde: K = 1 (ganho DC) e τ = RC (constante de tempo)",
  
  "analise_resultado": "**Características do Sistema:**\\n\\n• **Ordem:** 1ª ordem (grau do denominador = 1)\\n• **Tipo:** Sistema com um polo real\\n• **Polo:** s = -1/RC = -1/τ (localizado no SPE, sistema ESTÁVEL)\\n• **Zeros:** Nenhum (numerador constante)\\n• **Ganho DC:** G(0) = 1 (em regime permanente, Vc = Vin)\\n• **Constante de tempo:** τ = RC segundos\\n• **Tempo de acomodação (2%):** ts ≈ 4τ = 4RC\\n• **Comportamento:** Filtro passa-baixas de 1ª ordem\\n\\n**Interpretação física:** O capacitor se carrega exponencialmente até atingir a tensão de entrada, com velocidade determinada por τ = RC.",
  
  "codigo_diagrama": "import numpy as np\\nimport matplotlib.pyplot as plt\\nimport control as ctrl\\n\\n# === PARÂMETROS DO SISTEMA ===\\nR = 1000      # Resistência em Ohms (1 kΩ)\\nC = 1e-6      # Capacitância em Farads (1 µF)\\ntau = R * C   # Constante de tempo\\n\\nprint(f'Constante de tempo τ = {{tau*1000:.2f}} ms')\\n\\n# === FUNÇÃO DE TRANSFERÊNCIA ===\\n# G(s) = 1 / (RCs + 1) = 1 / (τs + 1)\\nnum = [1]           # Numerador: 1\\nden = [tau, 1]      # Denominador: τs + 1\\nG = ctrl.TransferFunction(num, den)\\n\\nprint('\\\\nFunção de Transferência:')\\nprint(G)\\n\\n# === ANÁLISE DE POLOS E ZEROS ===\\npolos = ctrl.poles(G)\\nzeros = ctrl.zeros(G)\\nprint(f'\\\\nPolos: {{polos}}')\\nprint(f'Zeros: {{zeros}}')\\nprint(f'Sistema estável: {{all(p.real < 0 for p in polos)}}')\\n\\n# === RESPOSTA AO DEGRAU ===\\nt = np.linspace(0, 5*tau, 1000)\\nt_out, y_out = ctrl.step_response(G, t)\\n\\nplt.figure(figsize=(10, 6))\\nplt.plot(t_out*1000, y_out, 'b-', linewidth=2, label='Resposta ao Degrau')\\nplt.axhline(y=0.632, color='r', linestyle='--', alpha=0.7, label=f'63.2% (t = τ = {{tau*1000:.2f}} ms)')\\nplt.axhline(y=0.98, color='g', linestyle='--', alpha=0.7, label=f'98% (t = 4τ = {{4*tau*1000:.2f}} ms)')\\nplt.axvline(x=tau*1000, color='r', linestyle=':', alpha=0.5)\\nplt.axvline(x=4*tau*1000, color='g', linestyle=':', alpha=0.5)\\nplt.xlabel('Tempo (ms)')\\nplt.ylabel('Vc(t) / Vin')\\nplt.title('Resposta ao Degrau - Circuito RC (1ª Ordem)')\\nplt.legend()\\nplt.grid(True, alpha=0.3)\\nplt.xlim([0, 5*tau*1000])\\nplt.ylim([0, 1.1])\\nplt.show()"
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
4. "funcao_transferencia" - G(s) final com forma padrão identificada
5. "analise_resultado" - Análise completa (ordem, polos, zeros, estabilidade, ganho DC)
6. "codigo_diagrama" - Código Python completo e funcional

Use \\n para quebras de linha dentro das strings.
Não inclua texto fora do JSON."""


# ============================================================================
# PROMPT: VALIDAR RESPOSTA DO USUÁRIO (MODO TUTOR)
# ============================================================================

PROMPT_VALIDAR_RESPOSTA = """## Tarefa
Você é um tutor avaliando a resposta de um aluno. Seja construtivo e educativo.

---

## Processo de Avaliação (Chain of Thought)

### Passo 1: Resolva o problema você mesmo
- Siga toda a metodologia de modelagem
- Obtenha a função de transferência correta

### Passo 2: Compare com a resposta do aluno
- Verifique equivalência matemática (formas diferentes podem ser equivalentes!)
- Considere simplificações válidas
- Identifique erros específicos se houver

### Passo 3: Elabore feedback construtivo
- Se CORRETO: Elogie e reforce o que foi bem feito
- Se INCORRETO: Identifique o erro específico, explique onde ocorreu, dê dicas para correção

---

## Critérios de Equivalência Matemática

As seguintes formas são EQUIVALENTES e devem ser consideradas CORRETAS:
- `1/(s+1)` = `1/(1+s)` (ordem dos termos)
- `1/(RCs+1)` = `1/(1+RCs)` = `1/(τs+1)` onde τ=RC
- `K/(s+a)` = `(K/a)/(s/a+1)` (formas diferentes de normalização)
- `1/(s²+2s+1)` = `1/(s+1)²` (forma fatorada)

---

## Exemplos de Avaliação

### Exemplo 1: Resposta Correta
**Sistema:** "Circuito RC série, saída no capacitor"
**Resposta do aluno:** "G(s) = 1 / (1 + RCs)"
**Avaliação:**
```json
{{
  "resposta_correta": true,
  "feedback": "Excelente trabalho! Sua resposta está perfeitamente correta. Você aplicou corretamente a Lei de Kirchhoff das Tensões e derivou a função de transferência de forma adequada. A forma 1/(1+RCs) é matematicamente equivalente à forma padrão 1/(RCs+1). Continue assim!",
  "solucao_correta": "G(s) = 1 / (RCs + 1)"
}}
```

### Exemplo 2: Resposta Incorreta - Erro no Numerador
**Sistema:** "Circuito RC série, saída no capacitor"
**Resposta do aluno:** "G(s) = R / (RCs + 1)"
**Avaliação:**
```json
{{
  "resposta_correta": false,
  "feedback": "Sua resposta está incorreta. O erro está no NUMERADOR.\\n\\n**O que aconteceu:** Você colocou R no numerador, mas a tensão no capacitor não depende diretamente de R dessa forma.\\n\\n**Revisão do conceito:**\\n1. LKT: Vin = V_R + Vc\\n2. V_R = R·i e i = C·dVc/dt\\n3. Vin = RC·dVc/dt + Vc\\n4. Aplicando Laplace: Vin(s) = RCs·Vc(s) + Vc(s)\\n5. G(s) = Vc(s)/Vin(s) = 1/(RCs+1)\\n\\n**Dica:** O numerador representa como a saída responde à entrada. Para o capacitor, em regime permanente (s→0), G(0)=1, ou seja, Vc = Vin.",
  "solucao_correta": "G(s) = 1 / (RCs + 1)"
}}
```

### Exemplo 3: Resposta Incorreta - Erro na Ordem
**Sistema:** "Sistema massa-mola-amortecedor"
**Resposta do aluno:** "G(s) = 1 / (Ms + Bs + K)"
**Avaliação:**
```json
{{
  "resposta_correta": false,
  "feedback": "Sua resposta está incorreta. O erro está no TERMO DE MASSA.\\n\\n**O que aconteceu:** Você escreveu Ms em vez de Ms². A aceleração é a segunda derivada do deslocamento, não a primeira.\\n\\n**Revisão do conceito:**\\n1. 2ª Lei de Newton: ΣF = M·a = M·d²x/dt²\\n2. Forças no sistema: F - Kx - B·dx/dt = M·d²x/dt²\\n3. Aplicando Laplace: F(s) - Kx(s) - Bs·X(s) = Ms²·X(s)\\n4. G(s) = X(s)/F(s) = 1/(Ms² + Bs + K)\\n\\n**Dica:** Lembre-se que L{{d²f/dt²}} = s²F(s) para condições iniciais nulas.",
  "solucao_correta": "G(s) = 1 / (Ms² + Bs + K)"
}}
```

---

## Problema a Avaliar

**Descrição do Sistema:**
"{descricao}"

**Função de Transferência do Aluno:**
"{funcao_transferencia_usuario}"

---

## Formato de Resposta OBRIGATÓRIO

Responda com um objeto JSON válido contendo EXATAMENTE estas 3 chaves:
1. "resposta_correta" - boolean (true ou false)
2. "feedback" - string com avaliação detalhada e construtiva
3. "solucao_correta" - string com a FT correta no formato "G(s) = ..."

Use \\n para quebras de linha dentro das strings.
Seja encorajador mesmo quando o aluno errar - o objetivo é ensinar!
Não inclua texto fora do JSON."""


# ============================================================================
# CONSTANTES DE CONFIGURAÇÃO DE PROMPT
# ============================================================================

PROMPT_CONFIG = {
    "temperature": 0.2,  # Baixa para respostas mais determinísticas
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 8192,  # Aumentado para respostas completas
}


# ============================================================================
# Funções de formatação de prompt
# ============================================================================


def _normalize_text(text: str) -> str:
    """Remove espaços extras do texto de entrada (DRY)."""
    return text.strip()


def formatar_prompt_ft(descricao: str) -> str:
    """Prompt para gerar apenas a função de transferência."""
    return PROMPT_APENAS_FT.format(descricao=_normalize_text(descricao))


def formatar_prompt_analise_completa(descricao: str) -> str:
    """Prompt para análise completa com Chain of Thought."""
    return PROMPT_ANALISE_COMPLETA.format(descricao=_normalize_text(descricao))


def formatar_prompt_validacao(descricao: str, funcao_transferencia_usuario: str) -> str:
    """Prompt para validação da resposta do aluno (modo tutor)."""
    return PROMPT_VALIDAR_RESPOSTA.format(
        descricao=_normalize_text(descricao),
        funcao_transferencia_usuario=_normalize_text(funcao_transferencia_usuario),
    )


def get_generation_config() -> dict:
    """Configuração de geração para o LLM (cópia para não alterar original)."""
    return PROMPT_CONFIG.copy()
