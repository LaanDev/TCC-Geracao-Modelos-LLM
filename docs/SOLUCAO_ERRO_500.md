# Solução: Erro 500 ao Chamar a API

Se você recebe **500 Internal Server Error** ao testar os endpoints (`/gerar-apenas-ft`, `/gerar-analise-completa`, etc.), siga estes passos.

---

## 1. Ver a Mensagem de Erro Real

A API foi ajustada para retornar o erro em JSON. Ao receber 500:

1. No Swagger UI, role até **"Response body"**
2. Você deve ver algo como: `{"sucesso": false, "erro": "mensagem do erro aqui"}`

**Anote a mensagem em "erro"** – ela indica a causa.

---

## 2. Causas Comuns e Soluções

### Erro relacionado ao modelo (ex.: "model not found", "404 is not found for API version v1beta")

**Causa:** O modelo configurado no `.env` não existe mais ou não está disponível na API atual. Modelos como `gemini-1.5-flash` foram descontinuados na v1beta.

**Solução:** Use um modelo atual no arquivo `.env`:

```env
# Modelos atuais (Google AI Studio) – use um destes:
LLM_MODEL=gemini-2.0-flash
```

Ou:

```env
LLM_MODEL=gemini-2.5-flash
```

Ou:

```env
LLM_MODEL=gemini-2.5-pro
```

**Modelos atuais suportados (2025):**
- `gemini-2.0-flash` – rápido e estável
- `gemini-2.5-flash` – bom custo-benefício
- `gemini-2.5-pro` – mais capaz
- `gemini-3-flash-preview` – preview mais recente

**Importante:** Não use o prefixo `models/` no nome – a API adiciona automaticamente.

Depois de alterar o `.env`, **reinicie a API** (pare com Ctrl+C e rode de novo `python main.py`).

---

### Erro de API key (ex.: "invalid api key", "403", "401")

**Causa:** Chave inválida, expirada ou sem permissão.

**Solução:**

1. Acesse: https://aistudio.google.com/app/apikey  
2. Faça login com a conta Google  
3. Crie uma nova chave (**Create API Key**)  
4. Copie a chave e atualize no `.env`:
   ```env
   GOOGLE_API_KEY=sua_nova_chave_aqui
   ```
5. Reinicie a API

---

### Erro de quota / limite (ex.: "quota exceeded", "429")

**Causa:** Limite de uso da API foi atingido.

**Solução:**

- Aguarde alguns minutos e tente de novo  
- No Google AI Studio, confira os limites do seu plano  
- Use um modelo mais leve (ex.: `gemini-1.5-flash`) para gastar menos quota  
- Veja também: [QUOTA_API.md](QUOTA_API.md)

---

### Erro de JSON ou "resposta inválida"

**Causa:** O modelo às vezes devolve texto que não é JSON válido.

**Solução:**

- Tente de novo (a API faz retry automático em alguns casos)  
- Use uma descrição um pouco mais clara e objetiva  
- Se continuar, troque para outro modelo (ex.: `gemini-1.5-pro`)  

---

### Erro de timeout

**Causa:** Resposta do modelo demorou mais que o limite.

**Solução:** Aumente o timeout no `.env`:

```env
LLM_TIMEOUT=120
```

Reinicie a API após alterar.

---

## 3. Ver Logs no Terminal

Com a API rodando no terminal, qualquer erro também aparece nos logs.

- Procure linhas em vermelho ou que comecem com `ERROR` ou `Traceback`
- A última linha do traceback costuma indicar a causa (modelo, API key, JSON, etc.)

---

## 4. Checklist Rápido

- [ ] Vi a mensagem em `erro` no corpo da resposta 500  
- [ ] Confirmei que `GOOGLE_API_KEY` no `.env` está correta e ativa  
- [ ] Testei outro modelo no `.env` (ex.: `gemini-1.5-flash`)  
- [ ] Reiniciei a API depois de mudar o `.env`  
- [ ] Verifiquei os logs no terminal onde a API está rodando  

---

## 5. Ainda com Erro?

Se depois disso ainda receber 500:

1. Copie a mensagem que aparece em **"erro"** no corpo da resposta  
2. Copie as últimas linhas de erro que aparecem no terminal da API  
3. Use essas informações para buscar o erro na documentação do Google AI ou para pedir ajuda (incluindo esse texto).

Documentação oficial: https://ai.google.dev/docs
