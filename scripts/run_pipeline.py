"""Ejecuta el pipeline completo de generación de exámenes con una materia de prueba.

Uso:
    python scripts/run_pipeline.py

Este script:
  1. Carga los materiales de la materia "Economía Aplicada" (data/inputs).
  2. Construye un ExamBlueprint realista con distribuciones de Bloom,
     dificultad y temas.
  3. Ejecuta el grafo LangGraph completo (ingestor → ... → compilador).
  4. Muestra un resumen del resultado y guarda el PDF generado.
"""
import glob
import json
import os
import sys
from pathlib import Path

# Asegura que el módulo `src` sea importable desde la raíz del proyecto.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.agents.graph import run_exam_pipeline  # noqa: E402
from src.schemas.exam import (  # noqa: E402
    BloomLevel,
    Difficulty,
    ExamBlueprint,
)
from src.templates.registry import TemplateId  # noqa: E402

BASE_DIR = Path("data/inputs/Economia_Aplicada")


def load_materials() -> list[str]:
    """Devuelve las rutas de los materiales de la materia (todos los formatos)."""
    patterns = [
        "Apuntes/*.pdf",
        "Apuntes/*.docx",
        "Apuntes/*.pptx",
        "Filminas/*.pdf",
        "Filminas/*.pptx",
        "Practica/*.pdf",
    ]
    files: list[str] = []
    for pat in patterns:
        files.extend(str(p) for p in glob.glob(str(BASE_DIR / pat)))
    # Deduplicar y ordenar
    return sorted(set(files))


def build_blueprint(total_questions: int = 8) -> ExamBlueprint:
    """Construye un blueprint realista para Economía Aplicada."""
    return ExamBlueprint(
        subject_id="economia-aplicada-test",
        total_questions=total_questions,
        bloom_distribution={
            BloomLevel.RECORDAR: 0.25,
            BloomLevel.COMPRENDER: 0.25,
            BloomLevel.APLICAR: 0.25,
            BloomLevel.ANALIZAR: 0.25,
        },
        difficulty_distribution={
            Difficulty.FACIL: 0.4,
            Difficulty.MEDIO: 0.4,
            Difficulty.DIFICIL: 0.2,
        },
        topics_weight={
            "Estudio de Mercado": 0.3,
            "Flujos Financieros": 0.3,
            "Análisis Económico-Financiero": 0.25,
            "Fijación de Precios": 0.15,
        },
        estimated_duration_minutes=90,
    )


def main() -> None:
    materials = load_materials()
    print(f"📚 Materiales cargados: {len(materials)} archivos")
    for m in materials:
        print(f"   - {Path(m).name}")

    blueprint = build_blueprint(total_questions=8)
    print(f"\n📋 Blueprint: {blueprint.total_questions} preguntas")
    print(f"   Bloom: { {k.value: v for k, v in blueprint.bloom_distribution.items()} }")
    print(f"   Dificultad: { {k.value: v for k, v in blueprint.difficulty_distribution.items()} }")

    print("\n🚀 Ejecutando pipeline...")
    result = run_exam_pipeline(
        subject_id=blueprint.subject_id,
        subject_name="Economía Aplicada",
        template_id=TemplateId.BASE_EXAM,
        raw_materials_paths=materials,
        blueprint=blueprint,
    )

    print("\n=== RESULTADO ===")
    print(f"Status: {result.get('status')}")
    print(f"Error: {result.get('error_message')}")
    print(f"Chunks indexados: {result.get('indexed_chunks_count')}")
    print(f"Ítems aprobados: {len(result.get('approved_items', []))}")
    print(f"Rechazos: {len(result.get('rejection_log', []))}")
    print(f"Llamadas LLM: {result.get('total_llm_calls')}")
    print(f"Intentos compilación: {result.get('compilation_attempts')}")

    # Guardar resumen en JSON para inspección
    out_dir = Path("data/agent_outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": result.get("status"),
        "error_message": result.get("error_message"),
        "indexed_chunks_count": result.get("indexed_chunks_count"),
        "approved_items": [i.model_dump() for i in result.get("approved_items", [])],
        "rejection_log": result.get("rejection_log", []),
        "total_llm_calls": result.get("total_llm_calls"),
        "compilation_attempts": result.get("compilation_attempts"),
        "compilation_log": result.get("compilation_log", []),
        "pdf_path": result.get("compiled_exam").pdf_path if result.get("compiled_exam") else None,
    }
    summary_path = out_dir / "pipeline_result.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n📄 Resumen guardado en: {summary_path}")

    if result.get("compiled_exam") and result["compiled_exam"].pdf_path:
        print(f"✅ PDF generado en: {result['compiled_exam'].pdf_path}")


if __name__ == "__main__":
    main()
