# Quota da API Google (erro 429)

Quando aparece **"Quota exceeded"** ou **429**, a cota gratuita da API foi excedida (por minuto ou por dia).

---

## Como ver se você usou toda a cota

### Passo a passo (Google AI Studio)

1. **Abra o Google AI Studio**  
   Acesse: **https://aistudio.google.com**

2. **Faça login** com a mesma conta Google da sua chave de API.

3. **Vá em Uso (Usage)**  
   - No menu lateral ou no topo, procure **"Usage"** / **"Uso"**  
   - Ou acesse direto: **https://aistudio.google.com/usage**

4. **Abra a aba "Rate limit"**  
   - Na página de uso, deve haver abas como **Usage**, **Rate limit**, **Billing**  
   - Clique em **"Rate limit"** (ou equivalente)

5. **O que aparece lá**  
   - **Seu tier:** Free, Tier 1, etc.  
   - **Limites por modelo:** RPM (requests/minuto), TPM (tokens/minuto), RPD (requests/dia)  
   - **Uso atual:** em muitos casos, quanto você já usou em relação ao limite

Se a página mostrar algo como **"0" de limite** ou **"limit: 0"** no erro que você viu, significa que a cota gratuita daquele modelo foi toda usada (por minuto ou por dia).

### Link direto para rate limits

👉 **https://aistudio.google.com/usage?timeRange=last-28-days&tab=rate-limit**

(Altere `timeRange` se quiser ver outro período.)

### Resumo dos limites (plano gratuito)

- **Por minuto:** número máximo de requisições e de tokens por minuto.  
  Se passar, aparece 429; depois de ~1 minuto costuma liberar de novo.

- **Por dia:** número máximo de requisições por dia.  
  Reseta à **meia-noite (horário do Pacífico)**.  
  Se estourar o limite diário, só volta no dia seguinte.

Se você não encontrar uma tabela de "uso atual" na tela, o próprio erro 429 já indica que algum desses limites (por minuto ou por dia) foi excedido.

---

## O que fazer agora

### 1. Aguardar e tentar de novo

A API já faz **retry automático**: em caso de 429, espera ~40–60 segundos e tenta de novo (até 3 vezes).

- **Aguarde cerca de 1 minuto** e teste de novo no Swagger.
- Se ainda der 429, espere **5–15 minutos** e tente outra vez (limite diário pode ter sido atingido).

### 2. Conferir uso e limites

- **Uso e limites:** https://ai.dev/rate-limit  
- **Documentação de quotas:** https://ai.google.dev/gemini-api/docs/rate-limits  

No plano gratuito há limite por minuto e por dia por modelo.

### 3. Testar outro modelo

Cada modelo tem cota separada. Se `gemini-2.0-flash` estiver no limite, use outro no `.env`:

```env
# Modelos com cotas separadas (escolha um):
LLM_MODEL=gemini-2.0-flash-lite
```

Ou:

```env
LLM_MODEL=gemini-2.5-flash-lite
```

Reinicie a API após alterar o `.env`.

### 4. Reduzir chamadas durante testes

- Evite clicar várias vezes em "Execute" no Swagger.
- Use primeiro o endpoint **`/gerar-apenas-ft`** (menos tokens que a análise completa).

---

## Resumo

| Ação              | O que fazer                                      |
|-------------------|---------------------------------------------------|
| Agora             | Esperar ~1 minuto e testar de novo                |
| Ainda 429         | Esperar 5–15 min ou trocar de modelo no `.env`    |
| Ver limites       | https://ai.dev/rate-limit                         |
| Menos tokens      | Usar `gemini-2.0-flash-lite` ou `gemini-2.5-flash-lite` |

O código já tenta de novo sozinho em caso de 429; se depois de esperar e/ou trocar o modelo continuar dando erro, a cota diária pode ter sido atingida e será preciso aguardar até o próximo dia.

---

## Nova API key não aumentou a cota?

**A cota é por projeto, não por chave de API.** Criar uma nova chave no **mesmo projeto** não reseta e não aumenta a cota; o limite continua o mesmo.

### Opções que funcionam

1. **Criar um novo projeto e usar a chave desse projeto**
   - Acesse: https://aistudio.google.com/app/apikey
   - Crie um **novo projeto** (ou escolha outro projeto existente).
   - Gere uma **nova API key** nesse novo projeto.
   - No seu `.env`, troque `GOOGLE_API_KEY` por essa nova chave.
   - Cada projeto tem sua própria cota gratuita.

2. **Trocar de modelo (cota separada por modelo)**
   - No `.env`, use por exemplo: `LLM_MODEL=gemini-2.0-flash-lite`
   - Reinicie a API. O modelo "lite" tem cota independente do `gemini-2.0-flash`.

3. **Aguardar o reset diário**
   - O limite **por dia** reseta à **meia-noite (horário do Pacífico)**.
   - No Brasil: por volta das 5h (horário de Brasília), dependendo do fuso.
   - Depois do reset, a cota do dia volta e você pode tentar de novo.
