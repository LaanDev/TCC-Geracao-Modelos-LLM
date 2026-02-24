"""
Script de Verificação de Instalação
Verifica se o ambiente está configurado corretamente para executar o projeto.
Execute na raiz do projeto: python scripts/verificar_instalacao.py
"""

import sys
import os
from pathlib import Path

def _raiz_projeto():
    """Retorna o Path da raiz do projeto (onde estão main.py e .env)."""
    script_dir = Path(__file__).resolve().parent
    # Se o pai do script tem main.py, é a raiz
    if (script_dir.parent / "main.py").exists():
        return script_dir.parent
    return Path(os.getcwd())

def verificar_python():
    """Verifica versão do Python."""
    print("🐍 Verificando Python...")
    versao = sys.version_info
    print(f"   Versão encontrada: {versao.major}.{versao.minor}.{versao.micro}")
    
    if versao.major < 3 or (versao.major == 3 and versao.minor < 11):
        print("   ❌ ERRO: Python 3.11 ou superior é necessário!")
        print("   📖 Consulte: docs/INSTALACAO_PYTHON.md")
        return False
    else:
        print("   ✅ Python OK!")
        return True

def verificar_pip():
    """Verifica se pip está disponível."""
    print("\n📦 Verificando pip...")
    try:
        import subprocess
        resultado = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                 capture_output=True, text=True)
        if resultado.returncode == 0:
            print(f"   ✅ pip OK: {resultado.stdout.strip()}")
            return True
        else:
            print("   ❌ pip não encontrado!")
            return False
    except Exception as e:
        print(f"   ❌ Erro ao verificar pip: {e}")
        return False

def verificar_dependencias():
    """Verifica se as dependências principais estão instaladas."""
    print("\n📚 Verificando dependências...")
    dependencias = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "pydantic": "Pydantic",
        "google.generativeai": "Google Generative AI",
        "dotenv": "python-dotenv",
        "control": "python-control"
    }
    
    faltando = []
    for modulo, nome in dependencias.items():
        try:
            __import__(modulo)
            print(f"   ✅ {nome}")
        except ImportError:
            print(f"   ❌ {nome} NÃO instalado")
            faltando.append(nome)
    
    if faltando:
        print(f"\n   ⚠️  Dependências faltando: {', '.join(faltando)}")
        print("   💡 Execute: pip install -r requirements.txt")
        return False
    else:
        print("   ✅ Todas as dependências instaladas!")
        return True

def verificar_arquivo_env():
    """Verifica se o arquivo .env existe e tem a chave necessária."""
    print("\n🔐 Verificando configuração (.env)...")
    raiz = _raiz_projeto()
    env_path = raiz / ".env"
    
    if not env_path.exists():
        print("   ⚠️  Arquivo .env não encontrado")
        print("   💡 Execute: copy .env.example .env")
        print("   💡 Depois edite o .env e adicione sua GOOGLE_API_KEY")
        return False
    
    # Verificar se tem GOOGLE_API_KEY
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            conteudo = f.read()
            if "GOOGLE_API_KEY" in conteudo:
                # Verificar se não está vazio ou com placeholder
                linhas = conteudo.split("\n")
                for linha in linhas:
                    if linha.startswith("GOOGLE_API_KEY"):
                        valor = linha.split("=", 1)[1].strip().strip('"').strip("'")
                        if valor and valor != "sua_chave_api_aqui" and len(valor) > 10:
                            print("   ✅ GOOGLE_API_KEY configurada")
                            return True
                        else:
                            print("   ⚠️  GOOGLE_API_KEY está vazia ou com placeholder")
                            print("   💡 Edite o .env e adicione sua chave real")
                            return False
                print("   ⚠️  GOOGLE_API_KEY não encontrada no .env")
                return False
            else:
                print("   ⚠️  GOOGLE_API_KEY não encontrada no .env")
                return False
    except Exception as e:
        print(f"   ❌ Erro ao ler .env: {e}")
        return False

def verificar_estrutura_projeto():
    """Verifica se os arquivos principais do projeto existem."""
    print("\n📁 Verificando estrutura do projeto...")
    base = _raiz_projeto()
    arquivos_necessarios = [
        "main.py",
        "config.py",
        "schemas.py",
        "prompts.py",
        "llm_service.py",
        "requirements.txt"
    ]
    
    faltando = []
    for arquivo in arquivos_necessarios:
        if (base / arquivo).exists():
            print(f"   ✅ {arquivo}")
        else:
            print(f"   ❌ {arquivo} NÃO encontrado")
            faltando.append(arquivo)
    
    if faltando:
        print(f"\n   ⚠️  Arquivos faltando: {', '.join(faltando)}")
        return False
    else:
        print("   ✅ Estrutura do projeto OK!")
        return True

def main():
    """Executa todas as verificações."""
    print("=" * 60)
    print("🔍 VERIFICAÇÃO DE INSTALAÇÃO - TCC API de Modelagem")
    print("=" * 60)
    
    resultados = []
    
    resultados.append(("Python", verificar_python()))
    resultados.append(("pip", verificar_pip()))
    resultados.append(("Estrutura", verificar_estrutura_projeto()))
    resultados.append(("Dependências", verificar_dependencias()))
    resultados.append(("Configuração", verificar_arquivo_env()))
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO")
    print("=" * 60)
    
    todos_ok = True
    for nome, status in resultados:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {nome}")
        if not status:
            todos_ok = False
    
    print("=" * 60)
    
    if todos_ok:
        print("\n🎉 TUDO PRONTO! Você pode executar o projeto:")
        print("   python main.py")
        print("\n📖 Depois acesse: http://127.0.0.1:8000/docs")
    else:
        print("\n⚠️  Alguns itens precisam de atenção.")
        print("📖 Consulte o README.md ou docs/INSTALACAO_PYTHON.md para mais detalhes.")
    
    return 0 if todos_ok else 1

if __name__ == "__main__":
    sys.exit(main())
