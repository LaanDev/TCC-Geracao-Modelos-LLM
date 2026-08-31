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


def test_sanitize_physical_newlines_in_ax_text():
    from diagram_executor import _sanitize_llm_diagram_code

    broken = (
        "ax2.text(0.5, -1.5, 'Professor Dr. Carlos Eduardo: Como não há sensor físico especificado na FT, \n"
        "assumimos didaticamente $H(s)=1$ para ilustrar uma malha fechada básica.', \n"
        "         ha='left', va='top', fontsize=9, color='gray')"
    )
    fixed = _sanitize_llm_diagram_code(broken)
    compile(fixed, "<test>", "exec")
    assert "assumimos didaticamente" in fixed
    assert fixed.count("\n") == 0 or "ha='left'" in fixed.split("\n")[-1]


def test_sanitize_physical_newlines_aspas_duplas():
    """Mesmo bug de string quebrada, mas com aspas duplas — regressão do gap reportado."""
    from diagram_executor import _sanitize_llm_diagram_code

    broken = (
        'ax2.text(0.5, -1.5, "Nota: como nao ha sensor especificado na FT, \n'
        'assumimos H(s)=1 para ilustrar a malha fechada.", \n'
        '         ha="left", va="top", fontsize=9)'
    )
    fixed = _sanitize_llm_diagram_code(broken)
    compile(fixed, "<test>", "exec")
    assert "assumimos H(s)=1" in fixed


def test_execute_diagram_python_multiline_string_llm():
    """Código estilo LLM com string quebrada em duas linhas deve executar após sanitização."""
    from diagram_executor import execute_diagram_python

    code = (
        "import matplotlib.pyplot as plt\n"
        "fig, ax = plt.subplots()\n"
        "ax.text(0.5, 0.5, 'Linha um do texto\n"
        "linha dois do texto', ha='center')\n"
        "plt.savefig('x.png')\n"
    )
    result = execute_diagram_python(code, save_prefix="diagrama_rota3")
    assert result.execucao_ok is True
    assert len(result.diagramas_png_base64) >= 1


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


def test_save_diagram_pngs_to_disk(tmp_path, monkeypatch):
    from diagram_executor import save_diagram_pngs_to_disk

    monkeypatch.setattr("diagram_executor.settings.diagram_save_to_disk", True)
    monkeypatch.setattr("diagram_executor.settings.diagram_output_dir", "diagrams")
    monkeypatch.setattr("diagram_executor.project_root", lambda: tmp_path)

    png = b"\x89PNG\r\n\x1a\n"
    paths = save_diagram_pngs_to_disk([png], "diagrama_rota3")
    assert paths == ["diagrams/diagrama_rota3_ex1.png"]
    assert (tmp_path / "diagrams" / "diagrama_rota3_ex1.png").read_bytes() == png

    paths2 = save_diagram_pngs_to_disk([png, png], "diagrama_rota3")
    assert paths2 == ["diagrams/diagrama_rota3_ex2.png", "diagrams/diagrama_rota3_ex3.png"]

    paths3 = save_diagram_pngs_to_disk([png], "diagrama_rota4")
    assert paths3 == ["diagrams/diagrama_rota4_ex1.png"]


def test_next_ex_ignora_png_sem_padrao_ex(tmp_path, monkeypatch):
    from diagram_executor import save_diagram_pngs_to_disk

    monkeypatch.setattr("diagram_executor.settings.diagram_save_to_disk", True)
    monkeypatch.setattr("diagram_executor.settings.diagram_output_dir", "diagrams")
    monkeypatch.setattr("diagram_executor.project_root", lambda: tmp_path)

    out = tmp_path / "diagrams"
    out.mkdir(parents=True)
    (out / "diagrama_blocos.png").write_bytes(b"x")
    (out / "diagrama_rota3_ex7.png").write_bytes(b"x")

    png = b"\x89PNG\r\n\x1a\n"
    paths = save_diagram_pngs_to_disk([png], "diagrama_rota3")
    assert paths == ["diagrams/diagrama_rota3_ex8.png"]


def test_save_diagram_pngs_concurrent_sem_colisao(tmp_path, monkeypatch):
    """Chamadas concorrentes (threadpool do FastAPI) não podem gerar nomes duplicados."""
    import threading

    from diagram_executor import save_diagram_pngs_to_disk

    monkeypatch.setattr("diagram_executor.settings.diagram_save_to_disk", True)
    monkeypatch.setattr("diagram_executor.settings.diagram_output_dir", "diagrams")
    monkeypatch.setattr("diagram_executor.project_root", lambda: tmp_path)

    png = b"\x89PNG\r\n\x1a\n"
    results: list[list[str]] = []
    results_lock = threading.Lock()

    def worker():
        paths = save_diagram_pngs_to_disk([png], "diagrama_rota3")
        with results_lock:
            results.append(paths)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    all_paths = [p for paths in results for p in paths]
    assert len(all_paths) == 20
    assert len(set(all_paths)) == 20
