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
  
  "codigo_diagrama": "import numpy as np\\nimport matplotlib.pyplot as plt\\nimport control as ctrl\\n\\n# === PARÂMETROS DO SISTEMA ===\\nR = 1000      # Resistência em Ohms (1 kΩ)\\nC = 1e-6      # Capacitância em Farads (1 µF)\\ntau = R * C   # Constante de tempo\\n\\nprint(f'Constante de tempo τ = {{tau*1000:.2f}} ms')\\n\\n# === FUNÇÃO DE TRANSFERÊNCIA ===\\n# G(s) = 1 / (RCs + 1) = 1 / (τs + 1)\\nnum = [1]           # Numerador: 1\\nden = [tau, 1]      # Denominador: τs + 1\\nG = ctrl.TransferFunction(num, den)\\n\\nprint('\\\\nFunção de Transferência:')\\nprint(G)\\n\\n# === ANÁLISE DE POLOS E ZEROS ===\\npolos = ctrl.poles(G)\\nzeros = ctrl.zeros(G)\\nprint(f'\\\\nPolos: {{polos}}')\\nprint(f'Zeros: {{zeros}}')\\nprint(f'Sistema estável: {{all(p.real < 0 for p in polos)}}')\\n\\n# === RESPOSTA AO DEGRAU ===\\nt = np.linspace(0, 5*tau, 1000)\\nt_out, y_out = ctrl.step_response(G, t)\\n\\nplt.figure(figsize=(10, 6))\\nplt.plot(t_out*1000, y_out, 'b-', linewidth=2, label='Resposta ao Degrau')\\nplt.axhline(y=0.632, color='r', linestyle='--', alpha=0.7, label=f'63.2% (t = τ = {{tau*1000:.2f}} ms)')\\nplt.axhline(y=0.98, color='g', linestyle='--', alpha=0.7, label=f'98% (t = 4τ = {{4*tau*1000:.2f}} ms)')\\nplt.axvline(x=tau*1000, color='r', linestyle=':', alpha=0.5)\\nplt.axvline(x=4*tau*1000, color='g', linestyle=':', alpha=0.5)\\nplt.xlabel('Tempo (ms)')\\nplt.ylabel('Vc(t) / Vin')\\nplt.title('Resposta ao Degrau - Circuito RC (1ª Ordem)')\\nplt.legend()\\nplt.grid(True, alpha=0.3)\\nplt.xlim([0, 5*tau*1000])\\nplt.ylim([0, 1.1])\\nplt.show()",

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

Responda com um objeto JSON válido contendo EXATAMENTE estas 7 chaves:
1. "lei_aplicada" - Lei física e sua aplicação ao sistema
2. "equacao_diferencial" - Derivação da EDO passo a passo
3. "passos_laplace" - Aplicação detalhada da Transformada de Laplace
4. "funcao_transferencia" - G(s) final com forma padrão identificada
5. "analise_resultado" - Análise completa (ordem, polos, zeros, estabilidade, ganho DC)
6. "codigo_diagrama" - Código Python completo e funcional
7. "grafo_diagrama" - MESMA topologia de "codigo_diagrama" como grafo, para verificação
   automática por redução algébrica (Fórmula de Ganho de Mason): {{"nos": [{{"id","tipo":
   "entrada"|"saida"|"somador"|"bloco", "ganho" (só em blocos, expressão em s com os
   parâmetros físicos do enunciado)}}], "arestas": [{{"origem","destino","sinal":"+"|"-"}}]}}.
   Exatamente 1 nó "entrada" e 1 "saida"; use "sinal":"-" só em entrada de realimentação
   de somador.

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
# PROMPT: GERAR DIAGRAMA DE BLOCOS A PARTIR DA FT
# ============================================================================

PROMPT_DIAGRAMA_POR_FT = """## Tarefa
Você receberá uma função de transferência em texto (G(s), relação Y/U, etc.).
Gere um programa Python único e executável com DUAS partes:

**(1) Diagrama de blocos completo em matplotlib:** setas, retângulos (`FancyBboxPatch`),
somador circular (`Circle`, fundo branco, "+" e "-" nas entradas), realimentação com
trechos ortogonais quando houver malha fechada, rótulos de sinais (ex.: r"$U(s)$").

**(2) `control` + gráfico de apoio:** construa `tf` só se houver coeficientes numéricos na
entrada (não invente valores só para simular). Caso só existam símbolos (M, K, ...),
entregue o diagrama simbólico e mensagens nos `print`, sem TF numérica.
Com FT numérica, inclua pelo menos resposta ao degrau OU pzmap.

**Interpretação apenas com a FT:** além do caminho U->[G(s)]->Y, desenhe em **outro subplot**
ou **outra figura** uma malha **equivalente** com realimentação unitária H(s)=1:
referência -> somador -> [G(s)] -> saída, com Y entrando na entrada "-" do somador.
No título explique que H=1 é **didático** quando não há sensor físico na FT fornecida.
Cascata G1, G2 só se inequívoco na expressão.

**API:** responda somente JSON com a chave "codigo_diagrama"; o valor é uma string com o
código completo; use \\n para novas linhas no JSON.
Finalize com um `plt.show()` OU `plt.savefig("diagrama_blocos.png", dpi=150, bbox_inches="tight")` + `print`.
Use `matplotlib.patches`: `FancyBboxPatch`, `FancyArrowPatch`, `Circle`.
**Setas (obrigatório):** `FancyArrowPatch(..., arrowstyle='-|>', mutation_scale=14, lw=1.5,
color='black')`. NÃO use `mutation_scale` acima de ~18 nem `lw` acima de ~2 — pontas de seta
maiores que isso cobrem os rótulos de texto dos blocos.
O servidor **executa** o código automaticamente em ambiente **sem tela** (Agg): `plt.show()`
vira captura de PNG; arquivos `.png` escritos no diretório atual do script também são coletados.

**matplotlib / mathtext (obrigatório):**
- Dentro de mathtext, **não** use comandos iniciados por barra dentro de `"$ ... $"` com aspas
  duplas comuns (ex.: string com frac sem barra escape dupla vira erro: Python trata o par `\\barra`+`f` como **avanço de formulário**).
  Use sempre string **bruta** com comandos matemáticos, por exemplo
  **`r'$\\frac{{X_1(s)}}{{U(s)}}$'`** (no `.py` isso aparece como dólar‑frac‑chaves bem formadas),
  ou escapes duplicados antes de comandos iniciados por barra se usar aspas duplas.
- `plt.tight_layout()` pode falhar com `aspect='equal'` e texto mathtext; prefira omitir ou
  `try: plt.tight_layout(); except Exception: pass`.
- **Strings Python:** nunca quebre um literal entre aspas simples ou duplas em várias linhas
  físicas do `.py` (isso gera SyntaxError). Textos longos em `ax.text(...)` ficam em **uma linha**
  ou use `\\n` dentro da string; comentários didáticos vão em `# comentário`, não dentro de strings multilinha.

## Grafo estruturado do diagrama (obrigatório)
Além do código, descreva como um grafo em "grafo_diagrama" APENAS o caminho direto
U -> [G(s)] -> Y (o primeiro subplot/figura), para permitir verificação automática por
redução algébrica (Fórmula de Ganho de Mason):
- "nos": lista de {{"id": "...", "tipo": "entrada"|"saida"|"somador"|"bloco", "ganho": "..."}}.
  "ganho" só se aplica a tipo="bloco" e deve ser uma expressão em s usando os MESMOS símbolos
  da função de transferência (ex.: "1/(R*C*s+1)"). Nós "entrada"/"saida"/"somador" não têm ganho.
- "arestas": lista de {{"origem": "id", "destino": "id", "sinal": "+"|"-"}}. "sinal" só importa
  nas entradas de um somador (realimentação negativa = "-"); nas demais conexões use "+".
- Exatamente 1 nó "entrada" e 1 nó "saida". O grafo, reduzido pela Fórmula de Mason, deve
  produzir uma expressão equivalente à função de transferência fornecida.
- **IMPORTANTE — leia com atenção:** o código Python pode (e deve) desenhar DOIS subplots/figuras
  (caminho direto + malha ilustrativa H(s)=1), mas "grafo_diagrama" descreve **só o primeiro**.
  Regra estrutural simples: se a função de transferência fornecida **não tem** um somador real
  nela (não é uma razão do tipo G_dir/(1+G_dir) explícita no enunciado), então "grafo_diagrama"
  **não deve conter nenhum nó do tipo "somador"** — apenas entrada -> bloco(s) -> saída em
  cascata direta. NÃO junte os nós/arestas dos dois subplots em uma única lista — isso duplica
  nós "entrada"/"saida" e quebra a verificação. A malha H(s)=1 é só para a figura; ela não entra
  no "grafo_diagrama" de forma alguma.
- **Denominador polinomial (2ª ordem ou mais) NÃO é realimentação:** se a FT fornecida é do tipo
  `1/(M*s^2 + B*s + K)` ou qualquer razão de polinômios em `s` com coeficientes (R, L, C, M, B,
  K, ...), isso é **um único bloco em malha aberta**, mesmo que o denominador tenha vários termos.
  Não interprete os termos do denominador como ramos de realimentação nem crie um "somador" para
  "montá-los" — o "grafo_diagrama" correto tem só 3 nós: entrada, um bloco com
  `"ganho": "1/(M*s**2+B*s+K)"` (a fração inteira, tal como fornecida), e saída.
  Antes de responder, se o seu "grafo_diagrama" tiver um nó "somador", pergunte-se: "o enunciado
  ou a FT fornecida mostra explicitamente uma subtração/realimentação?" Se não, remova o somador.

### Exemplo (sem realimentação, caminho direto U -> G(s) -> Y)
FT: "G(s) = 1 / (RCs + 1)"
```json
{{
  "codigo_diagrama": "...",
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

### ❌ NÃO faça isto (grafo da malha ilustrativa H(s)=1 — errado, não use como modelo)
O código Python pode desenhar a malha unitária didática no segundo subplot, mas o
"grafo_diagrama" NUNCA deve ser assim — reduzir isto por Mason dá `G_dir/(1+G_dir)`,
que não bate com a função de transferência fornecida:
```json
{{
  "grafo_diagrama": {{
    "nos": [
      {{"id": "r", "tipo": "entrada"}},
      {{"id": "soma", "tipo": "somador"}},
      {{"id": "g", "tipo": "bloco", "ganho": "G_dir"}},
      {{"id": "y", "tipo": "saida"}}
    ],
    "arestas": [
      {{"origem": "r", "destino": "soma", "sinal": "+"}},
      {{"origem": "soma", "destino": "g", "sinal": "+"}},
      {{"origem": "g", "destino": "y", "sinal": "+"}},
      {{"origem": "y", "destino": "soma", "sinal": "-"}}
    ]
  }}
}}
```
Use sempre o padrão do exemplo anterior (caminho direto, sem somador) para "grafo_diagrama".

## Função de Transferência
"{funcao_transferencia}"

## Formato de Resposta OBRIGATÓRIO
{{
  "codigo_diagrama": "...",
  "grafo_diagrama": {{"nos": [...], "arestas": [...]}}
}}"""


# ============================================================================
# PROMPT: GERAR FT + DIAGRAMA A PARTIR DA DESCRIÇÃO
# ============================================================================

PROMPT_FT_E_DIAGRAMA = """## Tarefa
1) A partir da descrição, derive a função de transferência pedida (string "G(s) = ...").
2) Produza código Python único executável que:
   - Desenhe o diagrama de blocos completo alinhado à física e à topologia inferidas
     (planta, controlador prévio, sensor, distúrbio, somadores e realimentação **somente**
     quando o enunciado suportar; **não** invente malha fechada se for malha aberta explícita).
   - Mesmo estilo matplotlib de PROMPT_DIAGRAMA_POR_FT (`FancyBboxPatch`,
     `FancyArrowPatch`, `Circle`, `ax.axis("off")`). Setas: `mutation_scale` entre 10 e 18,
     `lw` entre 1 e 2 — pontas grandes demais cobrem os rótulos de texto.
   - `control.tf` apenas com parâmetros numéricos no texto; senão diagrama simbólico + prints
     pedindo valores.
   - Com FT numérica, gráfico de apoio (degrau e/ou pzmap).

## Layout obrigatório: sistema mecânico translacional (massa(s), mola(s), amortecedor(es))
Se o enunciado mencionar **massa(s)**, **mola(s)** e/ou **amortecedor(es)** (ou amortecimento viscoso)
e for modelagem **translacional** (deslocamento/posição x, força de entrada F, etc.):

1. Use **exatamente dois painéis lado a lado** no **mesmo** `Figure`, por exemplo:
   `fig, (ax_phy, ax_blk) = plt.subplots(1, 2, figsize=(14, 5.5))` (ou tamanho equivalente).
2. **Painel esquerdo `ax_phy` — esquema físico “de livro”:**
   - Massas como blocos/retângulos com rótulos **M₁, M₂, ...** (ou M1, M2 se subscrito for incômodo).
   - Molas em zigue-zague entre referência fixa e massas; **k₁, k₂** nos trechos.
   - Amortecedores estilo pistão **ou** `|===` com **b₁, b₂**.
   - Setas de deslocamento **x₁, x₂** e força de entrada **F** coerentes com o enunciado.
   - `ax_phy.set_title(...)` deixando claro que é o **esquema físico**.
3. **Painel direito `ax_blk` — diagrama de blocos / fluxo de sinais:**
   - Mostrar o caminho **entrada → saída** pedido (ex.: **F(s)** até **X₁(s)** ou **X₂(s)**),
     com blocos, somadores e realimentações **coerentes com o graus de liberdade** descritos.
   - **Não** substituir todo o sistema multi-massa por um único bloco agregado **G(s)** **se** o texto
     descreve **duas ou mais massas acopladas**; use blocos em cascata / somadores que reflitam x₁, x₂.
   - Para **uma única** massa-mola-amortecedor clássica, um bloco **G(s)** explícito no painel direito é aceitável,
     desde que o painel esquerdo mostre o desenho físico completo.
4. Se o enunciado estiver **ambíguo** (entradas/saídas não definidas, ligações desconhecidas), seja **conservador**:
   produza a melhor hipótese **explícita** em `print(...)` e evite afirmar topologia não dada.

## Grafo estruturado do diagrama (obrigatório)
Além da FT e do código, descreva a MESMA topologia desenhada como um grafo em
"grafo_diagrama", para permitir verificação automática por redução algébrica
(Fórmula de Ganho de Mason) — ela confirma que o diagrama desenhado **de fato reduz**
à função de transferência declarada, e não só "parece" certo:
- "nos": lista de {{"id": "...", "tipo": "entrada"|"saida"|"somador"|"bloco", "ganho": "..."}}.
  "ganho" só se aplica a tipo="bloco" e deve ser uma expressão em s usando os MESMOS símbolos
  físicos do enunciado (ex.: "1/(R*C*s+1)", nunca valores numéricos inventados).
- "arestas": lista de {{"origem": "id", "destino": "id", "sinal": "+"|"-"}}. Use "sinal": "-"
  apenas na entrada de realimentação de um somador; nas demais conexões use "+".
- Exatamente 1 nó "entrada" e 1 nó "saida". Se o diagrama tiver mais de um bloco (cascata,
  realimentação, múltiplas massas), o grafo deve refletir a MESMA topologia — não colapse
  tudo em um único bloco G(s) se o diagrama desenhado tem mais estrutura que isso.

### Exemplo (RC série, caminho direto sem realimentação)
```json
{{
  "funcao_transferencia": "G(s) = 1 / (RCs + 1)",
  "codigo_diagrama": "...",
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

## Regras de saída (API)
1. JSON somente com "funcao_transferencia", "codigo_diagrama" e "grafo_diagrama".
2. codigo_diagrama é uma string única com \\n dentro do JSON.
3. O servidor executa o código em modo **headless**: `plt.show()` e `savefig(...)` produzem PNG automaticamente.
4. **Mathtext:** preferir strings brutas tipo `ax.text(..., r'$\\frac{{a}}{{b}}$')` ou barras doubled em aspas não-brutas.
5. **`plt.tight_layout()`**: omitir ou `try`/`except` (pode falhar com `aspect='equal'`).

## Descrição do Sistema
"{descricao}"

## Formato de Resposta OBRIGATÓRIO
{{
  "funcao_transferencia": "G(s) = ...",
  "codigo_diagrama": "...",
  "grafo_diagrama": {{"nos": [...], "arestas": [...]}}
}}"""


# ============================================================================
# PROMPTS: RETRY CURTO PÓS-VERIFICAÇÃO (ReAct-lite)
# ============================================================================

PROMPT_CORRECAO_APENAS_FT = """## Correção exigida (verificação automática)
A saída anterior **não passou** em checagens determinísticas (parse simbólico e/ou gabarito canônico).

**Problemas detectados:**
{problemas}

**Descrição original:**
"{descricao}"

**Sua resposta anterior (corrija ou explique lacunas com conservadorismo):**
{funcao_transferencia_anterior}

## Instruções
1. Corrija a **função de transferência** para ser **simbolicamente consistente** com o enunciado.
2. Se o enunciado for **insuficiente** para um modelo único, **não invente** detalhes: devolva a melhor
   forma simbólica possível e acrescente na própria string uma frase curta final: `Nota: parâmetro ambíguo — ...`
   listando o que falta (sem JSON extra).
3. Responda **somente** JSON com a mesma chave que o endpoint /gerar-apenas-ft:
{{"funcao_transferencia": "G(s) = ..."}}"""


PROMPT_CORRECAO_FT_E_DIAGRAMA = """## Correção exigida (verificação automática)
A saída anterior falhou em checagens determinísticas (FT e/ou layout físico+blocos).

**Problemas detectados:**
{problemas}

**Descrição original:**
"{descricao}"

**FT anterior:**
{funcao_transferencia_anterior}

**Código de diagrama anterior (trecho inicial, referência):**
{codigo_diagrama_trecho}

## Instruções
1. Corrija **funcao_transferencia**, **codigo_diagrama** e **grafo_diagrama** de forma **coerente** entre si
   (o grafo — nós "entrada"/"saida"/"somador"/"bloco" com "ganho", arestas com "sinal" — deve reduzir,
   pela Fórmula de Ganho de Mason, à FT corrigida).
2. Se o texto for mecânico translacional com molas/amortecedores, **obrigatoriamente** `plt.subplots(1, 2, ...)`
   com esquema físico à esquerda e blocos à direita (ver regras longas do prompt principal).
3. Se houver ambiguidade real, seja conservador: `print` com hipóteses e, se necessário, nota curta na string da FT
   com prefixo `Nota: parâmetro ambíguo —`.
4. Responda **somente** JSON com as três chaves:
{{"funcao_transferencia": "G(s) = ...", "codigo_diagrama": "...", "grafo_diagrama": {{"nos": [...], "arestas": [...]}}}}"""


PROMPT_CORRECAO_DIAGRAMA_POR_FT = """## Correção exigida (FT ilegível para o verificador)
A função de transferência textual usada como base **não pôde ser interpretada** como expressão racional
em **s** (ex.: falta de `G(s) =`, trecho extra, divisão ambígua).

**Problemas:**
{problemas}

**FT anterior (contexto):**
{funcao_transferencia_anterior}

## Instruções
1. Gere de novo o **código Python** do diagrama, **ainda alinhado** à intenção dessa FT malformada quando possível,
   mas se a FT for irrecuperável produza um diagrama mínimo válido com mensagens `print` explicando o que faltou.
2. Descreva a mesma topologia em **grafo_diagrama** (nós "entrada"/"saida"/"somador"/"bloco" com "ganho",
   arestas com "sinal") quando a FT permitir; se for irrecuperável, omita "grafo_diagrama".
3. Responda **somente** JSON com as chaves `codigo_diagrama` e, quando possível, `grafo_diagrama`.

Responda **somente**:
{{"codigo_diagrama": "...", "grafo_diagrama": {{"nos": [...], "arestas": [...]}}}}"""


# ============================================================================
# CONSTANTES DE CONFIGURAÇÃO DE PROMPT
# ============================================================================

PROMPT_CONFIG = {
    "temperature": 0.2,  # Baixa para respostas mais determinísticas
    "top_p": 0.9,
    "top_k": 40,
    # Endpoints com código de diagrama + grafo_diagrama no mesmo JSON aproximam-se do teto
    # antigo (8192) e produzem string JSON truncada ("unterminated string"). 16384 corrigiu a
    # truncagem, mas pareceu aumentar a taxa de timeout do lado do servidor (504
    # DEADLINE_EXCEEDED) — 12288 é o meio-termo em avaliação.
    "max_output_tokens": 12288,
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


def formatar_prompt_diagrama_por_ft(funcao_transferencia: str) -> str:
    """Prompt para gerar código de diagrama de blocos a partir da FT."""
    return PROMPT_DIAGRAMA_POR_FT.format(
        funcao_transferencia=_normalize_text(funcao_transferencia),
    )


def formatar_prompt_ft_e_diagrama(descricao: str) -> str:
    """Prompt para gerar FT e código de diagrama a partir da descrição."""
    return PROMPT_FT_E_DIAGRAMA.format(descricao=_normalize_text(descricao))


def _bulleted_lines(items: list[str]) -> str:
    return "\n".join(f"- {x}" for x in items)


def formatar_prompt_correcao_apenas_ft(
    descricao: str, problemas: list[str], funcao_transferencia_anterior: str
) -> str:
    """Retry curto após falha do verificador no endpoint apenas-FT."""
    return PROMPT_CORRECAO_APENAS_FT.format(
        problemas=_bulleted_lines(problemas),
        descricao=_normalize_text(descricao),
        funcao_transferencia_anterior=_normalize_text(funcao_transferencia_anterior),
    )


def formatar_prompt_correcao_ft_e_diagrama(
    descricao: str,
    problemas: list[str],
    funcao_transferencia_anterior: str,
    codigo_diagrama_anterior: str,
    codigo_max_chars: int = 900,
) -> str:
    """Retry curto após falha do verificador no endpoint FT + diagrama."""
    code = _normalize_text(codigo_diagrama_anterior)
    if len(code) > codigo_max_chars:
        code = code[:codigo_max_chars] + "\n... [truncado]"
    trecho = code.replace("{", "{{").replace("}", "}}")
    return PROMPT_CORRECAO_FT_E_DIAGRAMA.format(
        problemas=_bulleted_lines(problemas),
        descricao=_normalize_text(descricao),
        funcao_transferencia_anterior=_normalize_text(funcao_transferencia_anterior),
        codigo_diagrama_trecho=trecho,
    )


def formatar_prompt_correcao_diagrama_por_ft(
    problemas: list[str], funcao_transferencia_anterior: str
) -> str:
    """Retry opcional quando a FT de entrada não faz parse racional."""
    return PROMPT_CORRECAO_DIAGRAMA_POR_FT.format(
        problemas=_bulleted_lines(problemas),
        funcao_transferencia_anterior=_normalize_text(funcao_transferencia_anterior),
    )


def get_generation_config() -> dict:
    """Configuração de geração para o LLM (cópia para não alterar original)."""
    return PROMPT_CONFIG.copy()
