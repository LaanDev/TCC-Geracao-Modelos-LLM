# Como Corrigir o Problema do pip

Se o `pip` não é reconhecido, mas o `python` funciona, siga estes passos:

## Solução 1: Usar `python -m pip` (Funciona Imediatamente)

Em vez de usar `pip`, use sempre `python -m pip`:

```powershell
# Verificar versão do pip
python -m pip --version

# Instalar pacotes
python -m pip install --upgrade pip

# Instalar dependências do projeto
python -m pip install -r requirements.txt
```

**Esta é a forma mais confiável e funciona mesmo se pip não estiver no PATH!**

---

## Solução 2: Instalar/Atualizar pip

Execute no PowerShell:

```powershell
python -m ensurepip --upgrade
```

Isso vai instalar ou atualizar o pip.

---

## Solução 3: Adicionar Scripts ao PATH (Opcional)

Se quiser usar `pip` diretamente (sem `python -m`):

1. Encontre onde o Python está instalado:
   ```powershell
   python -c "import sys; print(sys.executable)"
   ```

2. Adicione a pasta `Scripts` ao PATH:
   - Geralmente é: `C:\Users\SeuUsuario\AppData\Local\Programs\Python\Python314\Scripts`
   - Ou: `C:\Python314\Scripts` (se instalou para todos os usuários)

3. Como adicionar ao PATH:
   - Pressione `Win + R`
   - Digite: `sysdm.cpl` e pressione Enter
   - Vá em "Avançado" → "Variáveis de Ambiente"
   - Em "Variáveis do sistema", encontre "Path" e clique em "Editar"
   - Clique em "Novo" e adicione o caminho da pasta Scripts
   - Clique em "OK" em todas as janelas
   - **Feche e reabra o PowerShell**

---

## Verificação

Depois de executar a Solução 1 ou 2, teste:

```powershell
python -m pip --version
```

Você deve ver algo como: `pip 24.x from ...`

---

## Para o Projeto TCC

Use sempre `python -m pip` nos comandos:

```powershell
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
.\venv\Scripts\activate

# Instalar dependências
python -m pip install -r requirements.txt
```

**Nota:** Depois de ativar o ambiente virtual (`venv`), você pode usar `pip` diretamente, pois o venv tem seu próprio pip.
