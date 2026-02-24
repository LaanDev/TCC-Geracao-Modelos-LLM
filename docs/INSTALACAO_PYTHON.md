# Guia de Instalação do Python - Windows

Este guia te ajudará a instalar o Python 3.11 no Windows para executar o projeto TCC.

## Método 1: Instalação via Site Oficial (Recomendado)

### Passo 1: Baixar o Python
1. Acesse: https://www.python.org/downloads/
2. Clique em **"Download Python 3.11.x"** (ou versão mais recente 3.11+)
3. O arquivo `.exe` será baixado (ex: `python-3.11.9-amd64.exe`)

### Passo 2: Instalar o Python
1. **Execute o instalador** baixado
2. **IMPORTANTE:** Marque a opção **"Add Python to PATH"** ✅
   - Isso permite usar `python` e `pip` no terminal
3. Clique em **"Install Now"**
4. Aguarde a instalação completar
5. Clique em **"Close"**

### Passo 3: Verificar Instalação
Abra o **PowerShell** ou **Prompt de Comando** e execute:

```powershell
python --version
```

Você deve ver algo como: `Python 3.11.9`

```powershell
pip --version
```

Você deve ver algo como: `pip 24.0 from ...`

**Se aparecer erro "python não é reconhecido":**
- O Python não foi adicionado ao PATH
- Reinstale o Python marcando "Add Python to PATH"
- Ou adicione manualmente ao PATH (veja Método 2)

---

## Método 2: Instalação via Microsoft Store (Alternativa)

1. Abra a **Microsoft Store**
2. Pesquise por **"Python 3.11"**
3. Clique em **"Instalar"**
4. Aguarde a instalação

**Nota:** Este método geralmente adiciona ao PATH automaticamente.

---

## Método 3: Usando Chocolatey (Para usuários avançados)

Se você tem o Chocolatey instalado:

```powershell
choco install python311
```

---

## Verificação Completa

Após instalar, verifique se tudo está funcionando:

```powershell
# Verificar versão do Python
python --version

# Verificar versão do pip
pip --version

# Atualizar pip (recomendado)
python -m pip install --upgrade pip
```

---

## Próximos Passos

Agora que o Python está instalado, você pode:

1. **Criar o ambiente virtual:**
   ```powershell
   python -m venv venv
   ```

2. **Ativar o ambiente virtual:**
   ```powershell
   .\venv\Scripts\activate
   ```

3. **Instalar dependências:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Criar arquivo .env:**
   ```powershell
   copy .env.example .env
   ```
   Depois edite o `.env` e adicione sua chave da API do Google.

5. **Executar a API:**
   ```powershell
   python main.py
   ```

---

## Solução de Problemas

### Problema: "python não é reconhecido como comando"
**Solução:**
1. Reinstale o Python marcando "Add Python to PATH"
2. Ou adicione manualmente:
   - Abra "Variáveis de Ambiente" no Windows
   - Adicione `C:\Users\SeuUsuario\AppData\Local\Programs\Python\Python311` ao PATH
   - Adicione `C:\Users\SeuUsuario\AppData\Local\Programs\Python\Python311\Scripts` ao PATH

### Problema: "pip não é reconhecido"
**Solução:**
```powershell
python -m ensurepip --upgrade
```

### Problema: Erro de permissão ao instalar pacotes
**Solução:**
```powershell
# Use o flag --user
pip install --user -r requirements.txt
```

---

## Requisitos do Projeto

- **Python:** 3.11 ou superior
- **pip:** Versão mais recente
- **Sistema:** Windows 10/11

---

## Links Úteis

- **Download Python:** https://www.python.org/downloads/
- **Documentação Python:** https://docs.python.org/3/
- **Google AI Studio (API Key):** https://aistudio.google.com/app/apikey
