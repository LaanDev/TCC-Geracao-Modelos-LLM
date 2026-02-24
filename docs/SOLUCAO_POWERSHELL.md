# Solução: Erro de Execução de Scripts no PowerShell

O erro ocorre porque o PowerShell bloqueia a execução de scripts por padrão (política de segurança).

## Solução Rápida 1: Usar Prompt de Comando (CMD) ✅

**Mais simples e não requer mudanças de segurança:**

1. Abra o **Prompt de Comando** (CMD) em vez do PowerShell:
   - Pressione `Win + R`
   - Digite: `cmd` e pressione Enter
   - Navegue até a pasta do projeto:
     ```cmd
     cd "C:\Users\laanc\OneDrive\Documentos\Repositórios\TCC-Geracao-Modelos-LLM"
     ```

2. Ative o ambiente virtual:
   ```cmd
   venv\Scripts\activate
   ```

   **Nota:** No CMD não precisa do `.\` antes do caminho.

3. Agora você pode usar `pip` diretamente:
   ```cmd
   pip install -r requirements.txt
   ```

---

## Solução Rápida 2: Alterar Política do PowerShell (Temporária)

Execute no PowerShell **como Administrador**:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois tente novamente:
```powershell
.\venv\Scripts\activate
```

**O que isso faz:**
- Permite executar scripts locais (como o activate.ps1)
- Aplica apenas ao seu usuário (não afeta outros usuários)
- É seguro para desenvolvimento

---

## Solução Rápida 3: Bypass Temporário (Apenas para esta sessão)

Execute no PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

Depois ative o venv:
```powershell
.\venv\Scripts\activate
```

**Nota:** Isso só funciona para a sessão atual. Ao fechar o PowerShell, volta ao padrão.

---

## Solução Rápida 4: Ativar Manualmente (Sem Script)

Se não quiser alterar políticas, você pode ativar o ambiente manualmente:

```powershell
# No PowerShell, execute:
$env:VIRTUAL_ENV = "C:\Users\laanc\OneDrive\Documentos\Repositórios\TCC-Geracao-Modelos-LLM\venv"
$env:PATH = "$env:VIRTUAL_ENV\Scripts;$env:PATH"
```

Depois verifique:
```powershell
python --version
pip --version
```

---

## Recomendação

**Para desenvolvimento, recomendo a Solução 1 (usar CMD)** - é mais simples e não requer mudanças de segurança.

Ou use a **Solução 2** se preferir continuar no PowerShell - é segura e permanente para seu usuário.

---

## Verificar Política Atual

Para ver qual é a política atual:

```powershell
Get-ExecutionPolicy -List
```

---

## Depois de Ativar o Ambiente Virtual

Independente do método usado, quando o ambiente estiver ativo, você verá `(venv)` no início da linha:

```
(venv) PS C:\Users\...\TCC-Geracao-Modelos-LLM>
```

Ou no CMD:
```
(venv) C:\Users\...\TCC-Geracao-Modelos-LLM>
```

Agora você pode:
```cmd
pip install -r requirements.txt
python main.py
```
