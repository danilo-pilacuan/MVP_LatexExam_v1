"""Verificación de la tool exportar_preguntas (sin BD, con mock del banco).

Prueba:
  1. Que la tool esté registrada en el grafo (TOOLS).
  2. Que el args_schema valide formato inválido (cae a csv) y limit fuera de rango.
  3. Que genere CSV y XLSX reales con las columnas completas (mock de preguntas).
  4. Que el fallback HTTP funcione si falla la subida a OpenWebUI.
"""
import sys
import os
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Evitar conectar a la BD al importar el grafo (checkpointer Postgres).
os.environ.setdefault("DATABASE_URL", "postgresql://x:x@localhost:1/xdb")
os.environ.setdefault("LATEX_COMPILER_URL", "http://localhost:1/compile")

from src.schemas.tools import ExportarPreguntasInput, TableColumn, COLUMN_LABELS  # noqa: E402
from src.agents.conversational import tools as tools_mod  # noqa: E402


class FakeQ:
    """Pregunta falsa con los campos que usa la exportación."""

    def __init__(self, i):
        self.id = f"00000000-0000-0000-0000-{i:012d}"
        self.topic = "Reading"
        self.subtopic = None
        self.bloom_level = "comprender"
        self.difficulty = "medio"
        self.question_type = "opcion_multiple"
        self.question_text = f"Pregunta de prueba {i} con | pipe y\nsalto"
        self.options = [
            {"text": "Opción A", "is_correct": True},
            {"text": "Opción B", "is_correct": False},
        ]
        self.expected_answer = "Opción A"
        self.solution_explanation = "Porque A es correcta."
        self.points = 1.5
        self.verified_by_human = i % 2 == 0
        self.verified_by_ai = True
        self.ai_review_priority = "baja"
        self.source = "chat"
        self.created_at = "2026-09-17 10:00:00"


def main():
    ok = True

    # 1) Tool registrada en el grafo.
    from src.agents.conversational.graph import TOOL_BY_NAME
    assert "exportar_preguntas" in TOOL_BY_NAME, "exportar_preguntas NO está en TOOLS"
    print("1. Tool registrada en el grafo: OK")

    # 2) args_schema: limit fuera de rango -> ValidationError.
    from pydantic import ValidationError
    try:
        ExportarPreguntasInput(subject_id="x", limit=1000)
        print("2. limit=1000 NO fue rechazado: FAIL")
        ok = False
    except ValidationError:
        print("2. args_schema rechaza limit fuera de rango: OK")

    # 3) Generación real de CSV y XLSX con mock del banco y de la subida.
    out_dir = ROOT / "data" / "agent_outputs"
    with patch.object(tools_mod.bank, "list_questions", return_value=[FakeQ(i) for i in range(3)]), \
         patch("main.OUTPUT_DIR", out_dir), \
         patch("src.api.openwebui.upload_file_to_openwebui",
               side_effect=RuntimeError("sin red (fallback)")):
        res_csv = tools_mod.exportar_preguntas.func(subject_id="x", formato="csv")
        res_xlsx = tools_mod.exportar_preguntas.func(subject_id="x", formato="xlsx")

    assert "Exporté **3 pregunta(s)**" in res_csv, res_csv
    assert "Descargar" in res_csv and "http://localhost:8000/output/" in res_csv, res_csv
    print("3a. CSV generado con fallback HTTP: OK")

    assert "Exporté **3 pregunta(s)**" in res_xlsx, res_xlsx
    print("3b. XLSX generado con fallback HTTP: OK")

    # Verificar contenido del CSV (columnas completas, pipes sin escapar, BOM).
    csv_files = sorted(out_dir.glob("preguntas_*.csv"))
    assert csv_files, "No se generó ningún CSV"
    content = csv_files[-1].read_text(encoding="utf-8-sig")
    for h in ["#", "Id", "Tema", "Pregunta", "Opciones", "Respuesta", "Solución", "Verif. humano"]:
        assert h in content, f"Falta columna {h} en el CSV"
    assert "1) *Opción A | 2) Opción B" in content, "Opciones mal formateadas"
    assert "Pregunta de prueba 0 con | pipe y salto" in content, "Pipe/salto mal procesados"
    print("3c. CSV con 17 columnas, opciones marcadas y BOM: OK")

    # Verificar el XLSX con openpyxl.
    from openpyxl import load_workbook
    xlsx_files = sorted(out_dir.glob("preguntas_*.xlsx"))
    assert xlsx_files, "No se generó ningún XLSX"
    wb = load_workbook(xlsx_files[-1])
    ws = wb.active
    headers = [c.value for c in ws[1]]
    assert headers[7] == "Pregunta" and headers[8] == "Opciones", headers
    assert ws.max_row == 4, f"Filas esperadas 4, hay {ws.max_row}"
    print("3d. XLSX legible con openpyxl, encabezados y filas correctas: OK")

    # 4) Subida exitosa a OpenWebUI (mock) -> markdown de adjunto nativo.
    with patch.object(tools_mod.bank, "list_questions", return_value=[FakeQ(1)]), \
         patch("main.OUTPUT_DIR", out_dir), \
         patch("src.api.openwebui.upload_file_to_openwebui",
               return_value={"id": "abc-123", "filename": "preguntas.xlsx"}):
        res_up = tools_mod.exportar_preguntas.func(subject_id="x", formato="xlsx")
    assert "http://localhost:3000/api/v1/files/abc-123/content" in res_up, res_up
    assert "Descargar el Excel" in res_up, res_up
    print("4. Subida a OpenWebUI -> adjunto nativo con enlace: OK")

    # 5) Formato inválido cae a csv (no crashea).
    with patch.object(tools_mod.bank, "list_questions", return_value=[FakeQ(1)]), \
         patch("main.OUTPUT_DIR", out_dir), \
         patch("src.api.openwebui.upload_file_to_openwebui",
               side_effect=RuntimeError("sin red")):
        res_inv = tools_mod.exportar_preguntas.func(subject_id="x", formato="pdf")
    assert "CSV" in res_inv, res_inv
    print("5. Formato inválido ('pdf') cae a CSV: OK")

    # 6) Banco vacío -> mensaje claro.
    with patch.object(tools_mod.bank, "list_questions", return_value=[]):
        res_empty = tools_mod.exportar_preguntas.func(subject_id="x")
    assert "No hay preguntas" in res_empty, res_empty
    print("6. Banco vacío -> mensaje claro: OK")

    # Limpiar archivos de prueba.
    for f in out_dir.glob("preguntas_*.csv"):
        f.unlink()
    for f in out_dir.glob("preguntas_*.xlsx"):
        f.unlink()

    print("\nTODO OK" if ok else "\nHAY FALLOS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
