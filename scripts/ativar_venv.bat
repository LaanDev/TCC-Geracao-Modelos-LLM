@echo off
REM Script para ativar o ambiente virtual no Windows (CMD)
REM Pode ser executado da raiz: scripts\ativar_venv.bat
REM Ou de dentro de scripts: ativar_venv.bat (sobe para a raiz do projeto)

cd /d "%~dp0.."
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo.
    echo Ambiente virtual ativado!
    echo Agora voce pode usar: pip install -r requirements.txt
    echo.
) else (
    echo ERRO: Ambiente virtual nao encontrado!
    echo Execute primeiro: python -m venv venv
    pause
    exit /b 1
)
