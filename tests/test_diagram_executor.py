"""Testes do executor de código de diagramas (subprocesso)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("matplotlib")

os.environ.setdefault("GOOGLE_API_KEY", "fake-key-for-tests")


def test_execute_diagram_python_captura_show():
    from diagram_executor import execute_diagram_python

    code = (
        "import matplotlib.pyplot as plt\n"
        "plt.figure()\n"
        "plt.plot([0, 1], [0, 1])\n"
        "plt.show()"
    )
    result = execute_diagram_python(code)
    assert result.execucao_ok is True
    assert len(result.diagramas_png_base64) >= 1


def test_sanitize_latex_frac_formfeed():
    from diagram_executor import _sanitize_latex_frac_escapes

    # Simula \"$\\frac...\" onde Python interpretou \\f como chr(12)
    bad = 'ax.text("$' + chr(12) + 'rac{X}{Y}$")'
    good = _sanitize_latex_frac_escapes(bad)
    assert "\\frac{X}{Y}" in good
    assert chr(12) not in good


def test_execute_diagram_python_autoflush_sem_show():
    """Figura montada mas sem plt.show()/savefig — epílogo do executor deve gravar PNG."""
    from diagram_executor import execute_diagram_python

    code = (
        "import matplotlib.pyplot as plt\n"
        "plt.figure()\n"
        "plt.plot([0, 1], [2, 3])\n"
    )
    result = execute_diagram_python(code)
    assert result.execucao_ok is True
    assert len(result.diagramas_png_base64) >= 1
