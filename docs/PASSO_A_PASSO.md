# 🚀 Guia Passo a Passo - Configurar o Projeto TCC

Siga estes passos na ordem para configurar seu projeto:

---

## ✅ Passo 1: Verificar Python

Abra o **Prompt de Comando (CMD)** ou **PowerShell** e execute:

```cmd
python --version
```

**Deve mostrar:** `Python 3.14.2` ou similar ✅

Se não funcionar, consulte: [INSTALACAO_PYTHON.md](INSTALACAO_PYTHON.md)

---

## ✅ Passo 2: Navegar até a Pasta do Projeto

No terminal, execute:

```cmd
cd "C:\Users\laanc\OneDrive\Documentos\Repositórios\TCC-Geracao-Modelos-LLM"
```

Ou navegue manualmente até a pasta e abra o terminal lá.

---

## ✅ Passo 3: Criar Ambiente Virtual

Execute:

```cmd
python -m venv venv
```

Aguarde alguns segundos. Isso cria a pasta `venv` com o ambiente isolado.

---

## ✅ Passo 4: Ativar o Ambiente Virtual

### Opção A: Usando CMD (Recomendado - Sem problemas de permissão)

```cmd
venv\Scripts\activate
```

### Opção B: Usando o Script Batch

```cmd
scripts\ativar_venv.bat
```

### Opção C: No PowerShell (se tiver alterado a política)

```powershell
.\venv\Scripts\activate
```

**✅ Sinal de sucesso:** Você verá `(venv)` no início da linha do terminal:

```
(venv) C:\Users\...\TCC-Geracao-Modelos-LLM>
```

> ⚠️ **Se der erro no PowerShell:** Use o CMD (Opção A) ou consulte [SOLUCAO_POWERSHELL.md](SOLUCAO_POWERSHELL.md)

---

## ✅ Passo 5: Atualizar pip

Com o ambiente virtual **ativado**, execute:

```cmd
python -m pip install --upgrade pip
```

Ou simplesmente:

```cmd
pip install --upgrade pip
```

---

## ✅ Passo 6: Instalar Dependências

Ainda com o ambiente virtual **ativado**, execute:

```cmd
pip install -r requirements.txt
```

Isso vai instalar todas as bibliotecas necessárias (FastAPI, Uvicorn, Google AI, etc.).

**Tempo estimado:** 2-5 minutos dependendo da sua internet.

---

## ✅ Passo 7: Criar Arquivo .env

### 7.1 Copiar o template

```cmd
copy .env.example .env
```

### 7.2 Editar o arquivo .env

Abra o arquivo `.env` com um editor de texto (Notepad, VS Code, etc.) e adicione sua chave da API do Google:

```env
GOOGLE_API_KEY=sua_chave_api_aqui
```

**Como obter a chave:**
1. Acesse: https://aistudio.google.com/app/apikey
2. Faça login com sua conta Google
3. Clique em **"Create API Key"**
4. Copie a chave gerada
5. Cole no arquivo `.env` substituindo `sua_chave_api_aqui`

---

## ✅ Passo 8: Verificar Instalação (Opcional)

Execute o script de verificação:

```cmd
python scripts\verificar_instalacao.py
```

Isso vai verificar se tudo está configurado corretamente.

---

## ✅ Passo 9: Executar a API

Com o ambiente virtual **ativado** e o `.env` configurado, execute:

```cmd
python main.py
```

Você deve ver algo como:

```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## ✅ Passo 10: Testar a API

Abra seu navegador e acesse:

👉 **http://127.0.0.1:8000/docs**

Você verá a documentação interativa (Swagger UI) onde pode testar todos os endpoints!

---

## 📋 Checklist Rápido

- [ ] Python instalado e funcionando
- [ ] Ambiente virtual criado (`python -m venv venv`)
- [ ] Ambiente virtual ativado (vê `(venv)` no terminal)
- [ ] pip atualizado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Arquivo `.env` criado e configurado com `GOOGLE_API_KEY`
- [ ] API rodando (`python main.py`)
- [ ] Acessou http://127.0.0.1:8000/docs no navegador

---

## 🆘 Problemas Comuns

### "pip não é reconhecido"
**Solução:** Use `python -m pip` em vez de `pip` — veja [CORRIGIR_PIP.md](CORRIGIR_PIP.md)

### "Erro ao ativar venv no PowerShell"
**Solução:** Use CMD em vez de PowerShell, ou consulte [SOLUCAO_POWERSHELL.md](SOLUCAO_POWERSHELL.md)

### "ModuleNotFoundError"
**Solução:** Certifique-se de que o ambiente virtual está ativado (deve ver `(venv)`)

### "GOOGLE_API_KEY not found"
**Solução:** Verifique se o arquivo `.env` existe e tem a chave configurada

---

## 📚 Documentação Adicional

- [INSTALACAO_PYTHON.md](INSTALACAO_PYTHON.md) - Instalar Python
- [SOLUCAO_POWERSHELL.md](SOLUCAO_POWERSHELL.md) - Problemas com PowerShell
- [CORRIGIR_PIP.md](CORRIGIR_PIP.md) - Problemas com pip
- [../README.md](../README.md) - Documentação completa do projeto

---

## 🎉 Próximos Passos

Depois que a API estiver rodando:

1. Teste os endpoints em http://127.0.0.1:8000/docs
2. Leia a documentação da API
3. Explore os exemplos de uso
4. Desenvolva o frontend (pasta `frontend/`)

**Boa sorte com seu TCC! 🚀**
