"""
Execução isolada do código Python gerado pelo LLM para diagramas (matplotlib).

Roda em subprocesso com timeout, backend Agg (sem display) e coleta arquivos .png
produzidos no diretório de trabalho (savefig do usuário ou plt.show() interceptado).
"""

from __future__ import annotations

import base64
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
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


def project_root() -> Path:
    """Raiz do repositório (onde está diagram_executor.py)."""
    return Path(__file__).resolve().parent


def _next_ex_index(out_dir: Path, prefix: str) -> int:
    """Próximo índice exN disponível para arquivos {prefix}_exN.png."""
    pattern = re.compile(rf"^{re.escape(prefix)}_ex(\d+)\.png$", re.IGNORECASE)
    max_n = 0
    for path in out_dir.glob("*.png"):
        m = pattern.match(path.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


# Endpoints do FastAPI rodam em threadpool (def síncrono); sem lock, duas requisições
# concorrentes calculariam o mesmo índice e uma sobrescreveria o PNG da outra.
_save_lock = threading.Lock()


def save_diagram_pngs_to_disk(png_blobs: list[bytes], prefix: str) -> list[str]:
    """
    Grava PNGs em settings.diagram_output_dir sem sobrescrever.
    Nomes: {prefix}_ex1.png, {prefix}_ex2.png, ... (continua a partir do maior ex existente).
    Retorna caminhos relativos à raiz do projeto.
    """
    if not settings.diagram_save_to_disk or not png_blobs:
        return []

    out_dir = project_root() / settings.diagram_output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    root = project_root()
    with _save_lock:
        start = _next_ex_index(out_dir, prefix)
        filenames = [f"{prefix}_ex{start + i}.png" for i in range(len(png_blobs))]
        for name, blob in zip(filenames, png_blobs, strict=True):
            path = out_dir / name
            path.write_bytes(blob)
            saved.append(str(path.relative_to(root)).replace("\\", "/"))
            logger.info("Diagrama salvo em %s", saved[-1])
    return saved


@dataclass(frozen=True)
class DiagramExecResult:
    diagramas_png_base64: list[str]
    execucao_ok: bool
    log_execucao: str
    diagramas_arquivos: list[str]


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


def _unescaped_quote_count(line: str, quote_char: str) -> int:
    """Conta ocorrências não escapadas de `quote_char` (heurística para string aberta)."""
    count = 0
    i = 0
    while i < len(line):
        if line[i] == "\\" and i + 1 < len(line):
            i += 2
            continue
        if line[i] == quote_char:
            count += 1
        i += 1
    return count


def _has_open_string(line: str) -> bool:
    """True se `line` termina com uma string '...' ou "..." ainda aberta."""
    return (
        _unescaped_quote_count(line, "'") % 2 == 1
        or _unescaped_quote_count(line, '"') % 2 == 1
    )


def _sanitize_physical_newlines_in_strings(code: str) -> str:
    """
    Une linhas quando o LLM quebra um literal '...' ou "..." em várias linhas físicas
    (SyntaxError: unterminated string literal).
    """
    lines = code.splitlines()
    if not lines:
        return code

    merged: list[str] = []
    i = 0
    while i < len(lines):
        current = lines[i]
        while _has_open_string(current) and i + 1 < len(lines):
            i += 1
            current = current.rstrip() + " " + lines[i].lstrip()
        merged.append(current)
        i += 1
    return "\n".join(merged)


def _sanitize_llm_diagram_code(code: str) -> str:
    """Pipeline de correções leves antes de executar código gerado pelo LLM."""
    code = _sanitize_latex_frac_escapes(code)
    return _sanitize_physical_newlines_in_strings(code)


def execute_diagram_python(
    code: str,
    *,
    save_prefix: str = "diagrama_rota3",
) -> DiagramExecResult:
    """
    Executa o código em diretório temporário; retorna PNGs em Base64 (URLs data: prontas).
    Se diagram_save_to_disk=true, grava cópias em diagrams/ com o prefixo informado.
    """
    if not settings.execute_diagram_code:
        return DiagramExecResult(
            diagramas_png_base64=[],
            execucao_ok=False,
            log_execucao="Execução automática desabilitada (execute_diagram_code=false).",
            diagramas_arquivos=[],
        )

    stripped = _sanitize_llm_diagram_code((code or "").strip())
    if not stripped:
        return DiagramExecResult([], False, "codigo_diagrama vazio.", [])

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
            encoding="utf-8",
            errors="replace",
            timeout=settings.diagram_execution_timeout,
            check=False,
        )

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        log = _truncate_log(f"=== returncode {proc.returncode} ===\n--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}")

        raw_pngs = _collect_pngs(workdir)
        b64_list = [base64.standard_b64encode(blob).decode("ascii") for blob in raw_pngs]
        saved_paths = save_diagram_pngs_to_disk(raw_pngs, save_prefix)

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
            diagramas_arquivos=saved_paths,
        )
    except subprocess.TimeoutExpired:
        logger.error("Diagram script timeout after %ss", settings.diagram_execution_timeout)
        return DiagramExecResult(
            [],
            False,
            f"Timeout após {settings.diagram_execution_timeout}s na execução do código.",
            [],
        )
    except OSError as e:
        logger.exception("Falha ao executar diagrama")
        return DiagramExecResult([], False, f"Erro do sistema ao executar: {e}", [])
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
