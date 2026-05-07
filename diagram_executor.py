"""
Execução isolada do código Python gerado pelo LLM para diagramas (matplotlib).

Roda em subprocesso com timeout, backend Agg (sem display) e coleta arquivos .png
produzidos no diretório de trabalho (savefig do usuário ou plt.show() interceptado).
"""

from __future__ import annotations

import base64
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from config import settings

logger = logging.getLogger("diagram_executor")

# Força Agg e redireciona plt.show() para PNG no diretório de trabalho (cwd do subprocess).
_PRELUDE = """
import os as _os
import sys as _sys

_DIAG_DIR = _os.environ.get("TCC_DIAGRAM_OUT", _os.getcwd())

import matplotlib as _mpl
_mpl.use("Agg", force=True)

import matplotlib.pyplot as _plt

_tcc_n = [0]
_tcc_show_orig = _plt.show

def _tcc_show(*args, **kwargs):
    _tcc_n[0] += 1
    _path = _os.path.join(_DIAG_DIR, "tcc_show_%d.png" % _tcc_n[0])
    try:
        _plt.savefig(_path, dpi=150, bbox_inches="tight")
    except Exception as _e:
        _sys.stderr.write("TCC_DIAGRAM savefig: %s\\n" % _e)
    finally:
        _plt.close("all")

_plt.show = _tcc_show
""".lstrip()

# Figuras ainda abertas ao fim do script viram PNG (código gerado que não chama show/savefig).
_EPILOGUE = """
try:
    import matplotlib.pyplot as _plt_eof
    import os as _ose
    import os.path as _opj

    _d = _ose.environ.get("TCC_DIAGRAM_OUT", _ose.getcwd())
    _nums = sorted(_plt_eof.get_fignums())
    for _i, _n in enumerate(_nums, start=1):
        _plt_eof.figure(_n)
        _plt_eof.savefig(
            _opj.join(_d, "tcc_autoflush_%d.png" % _i),
            dpi=150,
            bbox_inches="tight",
        )
    _plt_eof.close("all")
except BaseException as _eof_e:
    import sys as _sy_eof

    _sy_eof.stderr.write("TCC_DIAGRAM autoflush: %s\\n" % _eof_e)
""".lstrip()


@dataclass(frozen=True)
class DiagramExecResult:
    diagramas_png_base64: list[str]
    execucao_ok: bool
    log_execucao: str


def _collect_pngs(workdir: Path) -> list[bytes]:
    paths = sorted(workdir.glob("*.png"), key=lambda p: (p.stat().st_mtime, p.name))
    return [p.read_bytes() for p in paths]


def _truncate_log(text: str, max_len: int = 12000) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _sanitize_latex_frac_escapes(code: str) -> str:
    """
    Corrige saídas comuns do LLM onde \"...\"$\\\\frac aparece literalmente como
    \"$\\\\frac mas Python interpretou \\\\f como caractere de avanço de formulário.

    `$\\frac{X}{Y}$` gerado assim vira caracter `\\x0c` antes de rac (sem backslash antes de frac).
    """
    if "\x0c" not in code:
        return code
    return code.replace("\x0crac{", "\\frac{")


def execute_diagram_python(code: str) -> DiagramExecResult:
    """
    Executa o código em diretório temporário; retorna PNGs em Base64 (URLs data: prontas).
    """
    if not settings.execute_diagram_code:
        return DiagramExecResult(
            diagramas_png_base64=[],
            execucao_ok=False,
            log_execucao="Execução automática desabilitada (execute_diagram_code=false).",
        )

    stripped = _sanitize_latex_frac_escapes((code or "").strip())
    if not stripped:
        return DiagramExecResult([], False, "codigo_diagrama vazio.")

    workdir = Path(tempfile.mkdtemp(prefix="tcc_diagram_"))
    script_path = workdir / "_tcc_user_diagram.py"
    try:
        full_source = _PRELUDE + "\n\n" + stripped + "\n\n" + _EPILOGUE
        script_path.write_text(full_source, encoding="utf-8")

        env = os.environ.copy()
        env["TCC_DIAGRAM_OUT"] = str(workdir)
        env["MPLBACKEND"] = "Agg"
        env.setdefault("PYTHONUTF8", "1")

        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(workdir),
            env=env,
            capture_output=True,
            text=True,
            timeout=settings.diagram_execution_timeout,
            check=False,
        )

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        log = _truncate_log(f"=== returncode {proc.returncode} ===\n--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}")

        raw_pngs = _collect_pngs(workdir)
        b64_list = [base64.standard_b64encode(blob).decode("ascii") for blob in raw_pngs]

        ok = proc.returncode == 0 and bool(b64_list)
        if proc.returncode != 0 and not b64_list:
            logger.warning("Diagram script failed: %s", log[:500])
        elif proc.returncode != 0 and b64_list:
            ok = True
            log = _truncate_log(
                log + "\n(Aviso: processo retornou código != 0, mas imagens foram geradas.)"
            )
        elif proc.returncode == 0 and not b64_list:
            log = _truncate_log(
                log
                + "\n(Nenhum PNG coletado após script com exit 0. Reinicie o backend após atualizar "
                "`diagram_executor.py` — o epílogo `tcc_autoflush_*.png` captura figuras sem plt.show(); "
                "verifique também `EXECUTE_DIAGRAM_CODE=true`.)"
            )

        return DiagramExecResult(
            diagramas_png_base64=b64_list,
            execucao_ok=ok,
            log_execucao=log,
        )
    except subprocess.TimeoutExpired:
        logger.error("Diagram script timeout after %ss", settings.diagram_execution_timeout)
        return DiagramExecResult(
            [],
            False,
            f"Timeout após {settings.diagram_execution_timeout}s na execução do código.",
        )
    except OSError as e:
        logger.exception("Falha ao executar diagrama")
        return DiagramExecResult([], False, f"Erro do sistema ao executar: {e}")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
