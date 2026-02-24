# 🎉 Próximos Passos - API Funcionando!

Parabéns! Sua API está rodando com sucesso. Agora vamos explorar e usar o sistema.

---

## ✅ O Que Você Já Tem Funcionando

- ✅ Python instalado e configurado
- ✅ Ambiente virtual criado e ativado
- ✅ Todas as dependências instaladas
- ✅ Arquivo `.env` configurado com sua chave da API
- ✅ API rodando em http://127.0.0.1:8000

---

## 🚀 Passo 1: Explorar a Documentação Interativa

### 1.1 Acessar Swagger UI

Com a API rodando, abra seu navegador e acesse:

👉 **http://127.0.0.1:8000/docs**

Você verá a interface Swagger com todos os endpoints disponíveis.

### 1.2 Explorar os Endpoints

A API tem **3 endpoints principais**:

1. **`GET /`** - Health check (verifica se a API está online)
2. **`POST /gerar-apenas-ft`** - Gera apenas a função de transferência
3. **`POST /gerar-analise-completa`** - Análise completa com explicação didática
4. **`POST /validar-minha-resposta`** - Valida resposta do aluno (modo tutor)

### 1.3 Testar um Endpoint

1. Clique em **`POST /gerar-apenas-ft`**
2. Clique em **"Try it out"**
3. No campo `descricao`, cole este exemplo:
   ```
   Um circuito elétrico é composto por um resistor R e um capacitor C em série. 
   A entrada é a tensão da fonte Vin(t) e a saída é a tensão no capacitor Vc(t). 
   Encontre G(s) = Vc(s)/Vin(s).
   ```
4. Clique em **"Execute"**
5. Veja a resposta com a função de transferência!

---

## 🧪 Passo 2: Testar Problemas Clássicos

Teste com diferentes tipos de sistemas:

### 2.1 Sistema RC (1ª Ordem)
```
Um circuito RC série com resistor R e capacitor C. 
Entrada: tensão Vin. Saída: tensão no capacitor Vc.
```

### 2.2 Sistema Massa-Mola-Amortecedor (2ª Ordem)
```
Um sistema mecânico possui massa M, mola K e amortecedor B. 
Entrada: força F(t). Saída: deslocamento x(t).
```

### 2.3 Circuito RLC (2ª Ordem)
```
Circuito RLC série com resistor R, indutor L e capacitor C. 
Entrada: tensão Vin. Saída: tensão no capacitor Vc.
```

### 2.4 Sistema de Tanque (Processos)
```
Um tanque cilíndrico com área A e resistência hidráulica R. 
Entrada: vazão qi(t). Saída: altura h(t).
```

---

## 📊 Passo 3: Usar o Endpoint de Análise Completa

O endpoint `/gerar-analise-completa` retorna:

1. **Lei Aplicada** - Qual lei física foi usada
2. **Equação Diferencial** - A EDO do sistema
3. **Passos Laplace** - Transformada de Laplace passo a passo
4. **Função de Transferência** - G(s) final
5. **Análise do Resultado** - Interpretação (polos, zeros, estabilidade)
6. **Código Python** - Código para gerar diagrama de blocos

**Teste:**
1. Acesse `/gerar-analise-completa` no Swagger
2. Use qualquer descrição de sistema
3. Veja a análise completa e didática!

---

## 🎓 Passo 4: Testar o Modo Tutor

O endpoint `/validar-minha-resposta` funciona como um tutor:

1. Você envia:
   - Descrição do problema
   - Sua função de transferência calculada

2. A IA retorna:
   - Se está correto ou não
   - Feedback construtivo
   - Solução correta

**Exemplo de teste:**
- **Descrição:** "Circuito RC série, saída no capacitor"
- **Sua resposta:** "G(s) = 1 / (RCs + 1)"
- Veja o feedback da IA!

---

## 💻 Passo 5: Usar o Código Python Gerado

Quando usar `/gerar-analise-completa`, você receberá código Python no campo `codigo_diagrama`.

### 5.1 Copiar o Código

1. Copie o código do campo `codigo_diagrama`
2. Salve em um arquivo `teste_diagrama.py`
3. Execute: `python teste_diagrama.py`

### 5.2 Ver o Gráfico

O código gera gráficos de resposta ao degrau usando `matplotlib`. 
Certifique-se de ter a biblioteca instalada (já está no requirements.txt).

---

## 🔧 Passo 6: Explorar o Código do Projeto

Agora que está funcionando, explore a estrutura:

### 6.1 Arquivos Principais

- **`main.py`** - Rotas da API FastAPI
- **`config.py`** - Configurações centralizadas
- **`schemas.py`** - Modelos de dados (Pydantic)
- **`prompts.py`** - Engenharia de prompt (few-shot examples)
- **`llm_service.py`** - Comunicação com o LLM (timeout, retry, logging)

### 6.2 Entender o Fluxo

1. Cliente faz requisição → `main.py`
2. `main.py` formata prompt → `prompts.py`
3. `prompts.py` envia ao LLM → `llm_service.py`
4. `llm_service.py` retorna resposta → `main.py`
5. `main.py` valida com → `schemas.py`
6. Resposta JSON → Cliente

---

## 📝 Passo 7: Executar Testes (Opcional)

Se quiser verificar que tudo está funcionando corretamente:

```cmd
# Com o ambiente virtual ativado
pytest tests/ -v
```

Isso executa todos os testes automatizados.

---

## 🎨 Passo 8: Próxima Fase do TCC - Frontend

O frontend React já está na pasta **`frontend/`**.

### 8.1 Rodar o Frontend

```bash
cd frontend
npm install
npm run dev
```

Acesse http://localhost:3000. A API deve estar rodando em outro terminal (`python main.py`).

### 8.2 Documentação

Consulte **`frontend/README.md`** e [FRONTEND_NO_MESMO_REPO.md](FRONTEND_NO_MESMO_REPO.md) para mais detalhes.

---

## 🔍 Passo 9: Melhorias e Expansões

### 9.1 Melhorias de Prompt

- Testar diferentes modelos LLM
- Ajustar temperatura e parâmetros
- Adicionar mais exemplos few-shot

### 9.2 Funcionalidades Extras

- Cache de respostas (economizar chamadas à API)
- Histórico de problemas resolvidos
- Exportar análise em PDF
- Integração com LaTeX para fórmulas

### 9.3 Performance

- Adicionar rate limiting
- Implementar fila de requisições
- Otimizar chamadas ao LLM

---

## 📚 Passo 10: Documentação do TCC

Agora que o sistema está funcionando, você pode:

1. **Documentar os resultados:**
   - Testar com vários problemas canônicos
   - Comparar respostas da IA com soluções manuais
   - Avaliar qualidade das explicações

2. **Coletar dados para o TCC:**
   - Screenshots da API funcionando
   - Exemplos de respostas geradas
   - Métricas de tempo de resposta

3. **Escrever a seção de resultados:**
   - Apresentar casos de teste
   - Analisar qualidade das respostas
   - Discutir limitações e melhorias

---

## 🎯 Checklist de Próximos Passos

- [ ] Explorar http://127.0.0.1:8000/docs
- [ ] Testar endpoint `/gerar-apenas-ft` com problema RC
- [ ] Testar endpoint `/gerar-analise-completa` com problema massa-mola
- [ ] Testar endpoint `/validar-minha-resposta` como tutor
- [ ] Executar código Python gerado e ver gráfico
- [ ] Explorar código fonte (`main.py`, `prompts.py`, etc.)
- [ ] Executar testes: `pytest tests/ -v`
- [ ] Rodar o frontend em `frontend/`
- [ ] Documentar resultados para o TCC

---

## 🆘 Precisa de Ajuda?

- **Problemas com a API?** Verifique os logs no terminal
- **Erro ao chamar LLM?** Verifique sua `GOOGLE_API_KEY` no `.env`
- **Dúvidas sobre endpoints?** Consulte a documentação em `/docs`
- **Quer melhorar algo?** Explore o código e faça ajustes!
- **Documentação:** veja a pasta [docs/](.) (PASSO_A_PASSO, QUOTA_API, SOLUCAO_ERRO_500, etc.)

---

## 🎉 Parabéns!

Você tem uma API completa e funcional para seu TCC! 

Agora é hora de:
- ✅ Testar e validar
- ✅ Desenvolver o frontend
- ✅ Coletar dados para o trabalho
- ✅ Escrever a documentação

**Boa sorte com seu TCC! 🚀**
