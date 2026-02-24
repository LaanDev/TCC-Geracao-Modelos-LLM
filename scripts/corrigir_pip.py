"""
Script para corrigir/verificar instalação do pip
Execute na raiz do projeto: python scripts/corrigir_pip.py
"""

import sys
import subprocess
import os

def verificar_pip():
    """Verifica se pip está disponível."""
    print("🔍 Verificando pip...")
    
    # Tentar python -m pip
    try:
        resultado = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if resultado.returncode == 0:
            print(f"   ✅ pip encontrado via 'python -m pip'")
            print(f"   {resultado.stdout.strip()}")
            return True
    except Exception as e:
        print(f"   ❌ Erro ao verificar pip: {e}")
    
    return False

def instalar_pip():
    """Tenta instalar/atualizar pip."""
    print("\n📦 Tentando instalar/atualizar pip...")
    
    try:
        resultado = subprocess.run(
            [sys.executable, "-m", "ensurepip", "--upgrade"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if resultado.returncode == 0:
            print("   ✅ pip instalado/atualizado com sucesso!")
            return True
        else:
            print(f"   ⚠️  Código de saída: {resultado.returncode}")
            if resultado.stderr:
                print(f"   Erro: {resultado.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Erro ao instalar pip: {e}")
        return False

def atualizar_pip():
    """Atualiza pip para a versão mais recente."""
    print("\n⬆️  Atualizando pip...")
    
    try:
        resultado = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if resultado.returncode == 0:
            print("   ✅ pip atualizado com sucesso!")
            # Mostrar nova versão
            verificar_pip()
            return True
        else:
            print(f"   ⚠️  Não foi possível atualizar pip")
            if resultado.stderr:
                print(f"   Erro: {resultado.stderr[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Erro ao atualizar pip: {e}")
        return False

def mostrar_instrucoes():
    """Mostra instruções de uso."""
    print("\n" + "=" * 60)
    print("💡 INSTRUÇÕES")
    print("=" * 60)
    print("\nComo o 'pip' não está no PATH, use sempre:")
    print("   python -m pip <comando>")
    print("\nExemplos:")
    print("   python -m pip --version")
    print("   python -m pip install --upgrade pip")
    print("   python -m pip install -r requirements.txt")
    print("\n📖 Consulte: docs/CORRIGIR_PIP.md para mais detalhes")

def main():
    """Executa correção do pip."""
    print("=" * 60)
    print("🔧 CORREÇÃO DO PIP")
    print("=" * 60)
    print(f"\nPython encontrado: {sys.executable}")
    print(f"Versão: {sys.version}")
    
    # Verificar se pip já funciona
    if verificar_pip():
        print("\n✅ pip já está funcionando!")
        resposta = input("\nDeseja atualizar o pip para a versão mais recente? (s/n): ")
        if resposta.lower() in ['s', 'sim', 'y', 'yes']:
            atualizar_pip()
        return 0
    
    # Tentar instalar pip
    print("\n⚠️  pip não encontrado. Tentando instalar...")
    if instalar_pip():
        # Verificar novamente
        if verificar_pip():
            print("\n✅ pip instalado com sucesso!")
            atualizar_pip()
            return 0
    
    # Se chegou aqui, pip não foi instalado
    print("\n❌ Não foi possível instalar pip automaticamente.")
    mostrar_instrucoes()
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
