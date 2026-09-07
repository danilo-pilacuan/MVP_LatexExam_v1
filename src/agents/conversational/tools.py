"""Herramientas (tools) del agente conversacional.

Cada tool encapsula UNA acción acotada sobre el banco de preguntas. El LLM
las invoca mediante tool-calling. Toda escritura pasa por el service layer
(`src/bank/service.py`), nunca por SQL directo.

Guardrails aplicados aquí:
  - `_validate_exam_topic()`: rechaza temas fuera del ámbito de exámenes
    (hiperespecialización).
  - Generación de a UNA pregunta por llamada.
  - Confirmación humana explícita para marcar `verified_by_human`.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from src.agents.llm import generator_llm
from src.agents.retrieval import retrieve_chunks, format_context
from src.bank import service as bank
from src.schemas.exam import GeneratedItem, RetrievalConfig

# Temas que quedan FUERA del ámbito del agente (hiperespecialización).
_OFF_TOPIC_KEYWORDS = [
    "receta", "cocina", "película", "cine", "fútbol", "deporte", "noticia",
    "chisme", "política general", "clima", "viaje", "música", "videojuego",
]


def _validate_exam_topic(topic: str) -> str | None:
    """Devuelve un mensaje de rechazo si el tema está fuera del ámbito, o None."""
    t = topic.lower()
    for kw in _OFF_TOPIC_KEYWORDS:
        if kw in t:
            return (
                f"Lo siento, no puedo ayudarte con '{topic}': está fuera de mi función. "
                "Soy un asistente especializado en generar y gestionar preguntas de examen "
                "a partir del material de tus materias. ¿Quieres que te ayude con un tema "
                "de tus apuntes?"
            )
    return None


def _render_item_for_chat(item: GeneratedItem) -> str:
    """Formatea un ítem generado para mostrarlo en el chat (sin LaTeX)."""
    lines = [f"📝 **{item.statement}**"]
    if item.options:
        for i, o in enumerate(item.options, start=1):
            lines.append(f"   {i}. {o.text}")
    lines.append(f"✅ **Respuesta esperada:** {item.expected_answer}")
    if item.solution_explanation:
        lines.append(f"💡 **Explicación:** {item.solution_explanation}")
    lines.append(
        f"🏷 Tema: {item.topic} · Nivel: {item.bloom_level.value} · "
        f"Dificultad: {item.difficulty.value} · Tipo: {item.question_type.value}"
    )
    return "\n".join(lines)


@tool
def buscar_preguntas(
    subject_id: str,
    topic: str | None = None,
    limit: int = 20,
) -> str:
    """Recupera preguntas YA EXISTENTES del banco (no genera nuevas).

    Úsala cuando el profesor pida 'dame N preguntas de estos temas' sin querer
    generar nuevas. Devuelve las preguntas almacenadas.
    """
    rejection = _validate_exam_topic(topic or "")
    if rejection:
        return rejection

    questions = bank.list_questions(
        subject_id=subject_id,
        topic=topic,
        limit=limit,
    )
    if not questions:
        return (
            f"No hay preguntas en el banco para el tema '{topic or 'todas'}' "
            "de esta materia. Puedo generar una nueva si me lo pides."
        )

    lines = [f"📚 Encontré {len(questions)} pregunta(s) del banco:"]
    for i, q in enumerate(questions, start=1):
        verified = "✅ verificado humano" if q.verified_by_human else "⏳ sin verificar humano"
        lines.append(f"{i}. {q.question_text}  [{q.topic} · {q.difficulty} · {verified}]")
        if q.expected_answer:
            lines.append(f"   → Respuesta: {q.expected_answer}")
    return "\n".join(lines)


@tool
def generar_pregunta(
    subject_id: str,
    subject_name: str,
    topic: str,
    difficulty: str = "medio",
) -> str:
    """Genera UNA pregunta nueva sobre un tema, usando RAG sobre el material.

    Genera de a UNA pregunta (nunca varias). NO guarda todavía: devuelve la
    pregunta para que el profesor la revise y confirme antes de guardar.
    """
    rejection = _validate_exam_topic(topic)
    if rejection:
        return rejection

    # RAG: recuperar chunks relevantes al tema desde el material indexado.
    retrieval_cfg = RetrievalConfig(top_k=3, min_score=0.15, use_rag=True)
    context = ""
    try:
        chunks = retrieve_chunks(
            query=topic,
            subject_id=subject_id,
            top_k=retrieval_cfg.top_k,
            min_score=retrieval_cfg.min_score,
        )
        if chunks:
            context = format_context(chunks)
    except Exception:  # noqa: BLE001
        context = ""

    prompt = (
        "Eres un generador de ítems de examen. Genera EXACTAMENTE UNA pregunta "
        f"sobre el tema '{topic}' de la materia '{subject_name}', con dificultad "
        f"'{difficulty}'. Usa el contexto del material si está disponible.\n\n"
        f"{context or 'Sin contexto adicional del material.'}\n\n"
        "Devuelve solo la estructura solicitada."
    )

    try:
        structured = generator_llm.with_structured_output(GeneratedItem)
        item: GeneratedItem = structured.invoke(prompt)
    except Exception as e:  # noqa: BLE001
        return f"❌ No pude generar la pregunta: {str(e)[:200]}"

    # No se guarda aún: se devuelve para revisión humana (HITL).
    return (
        "Generé esta pregunta (aún NO está guardada):\n\n"
        f"{_render_item_for_chat(item)}\n\n"
        "¿La guardo en el banco? Responde **sí** para guardarla como verificada, "
        "o dime qué ajustar."
    )


@tool
def guardar_pregunta(
    subject_id: str,
    topic: str,
    bloom_level: str,
    difficulty: str,
    question_text: str,
    question_type: str,
    options: list[dict] | None = None,
    expected_answer: str | None = None,
    solution_explanation: str | None = None,
    subtopic: str | None = None,
    points: float = 1.0,
) -> str:
    """Guarda una pregunta en el banco (con verificación por IA).

    ⚠️ Esta tool NO marca `verified_by_human`. La verificación humana se hace
    por separado tras la confirmación explícita del profesor.
    """
    # Embedding para guardar (RAG de preguntas).
    from src.embeddings import embedder

    vec = embedder.embed([question_text])[0]

    # Verificación por IA ANTES de persistir (para marcar prioridad de revisión).
    from src.agents.verifier import review_question

    item_for_review = {
        "topic": topic,
        "bloom_level": bloom_level,
        "difficulty": difficulty,
        "question_type": question_type,
        "statement": question_text,
        "options": options,
        "expected_answer": expected_answer,
        "solution_explanation": solution_explanation,
    }
    review = review_question(item_for_review)

    q = bank.create_question(
        subject_id=subject_id,
        topic=topic,
        bloom_level=bloom_level,
        difficulty=difficulty,
        question_text=question_text,
        embedding=vec,
        question_type=question_type,
        options=options,
        expected_answer=expected_answer,
        solution_explanation=solution_explanation,
        subtopic=subtopic,
        points=points,
        source="chat",
        created_by="agent",
        verified_by_ai=review.verified_by_ai,
        ai_review_notes=review.notes,
        ai_review_priority=review.priority,
    )
    review_note = (
        f"\n🔍 **Verificación por IA:** {'aprobada' if review.verified_by_ai else 'requiere revisión'} "
        f"(prioridad {review.priority}). {review.notes}"
        if review.notes
        else ""
    )
    return (
        f"✅ Pregunta guardada en el banco (id: {q.id}).{review_note}\n"
        "Aún NO está marcada como verificada por humano. "
        "¿La confirmas como verificada?"
    )


@tool
def confirmar_verificacion_humana(question_id: str) -> str:
    """Marca una pregunta como VERIFICADA POR HUMANO.

    ⚠️ SOLO debe invocarse tras la confirmación explícita del profesor en el
    chat (human-in-the-loop). Una vez verificada, la pregunta queda protegida
    contra modificaciones del agente.
    """
    try:
        q = bank.set_human_verification(question_id, verified=True)
    except Exception as e:  # noqa: BLE001
        return f"❌ No se pudo verificar: {str(e)[:200]}"
    return (
        f"✅ Pregunta {q.id} marcada como **verificada por humano**. "
        "A partir de ahora no podrá ser modificada por el agente."
    )


@tool
def listar_materias() -> str:
    """Lista las materias registradas en el sistema.

    Úsala cuando el profesor pregunte qué materias existen o cuáles puede
    usar. Devuelve el id y nombre de cada materia registrada.
    """
    from src.database.connection import SessionLocal
    from src.database.models import Subject

    db = SessionLocal()
    try:
        subjects = db.query(Subject).all()
    finally:
        db.close()

    if not subjects:
        return "No hay materias registradas todavía. Puedes registrar una indicándome su nombre."

    lines = ["📚 Materias registradas:"]
    for s in subjects:
        lines.append(f"- **{s.name}** (id: `{s.id}`)")
    lines.append("\nIndícame el id de la materia sobre la que quieras trabajar.")
    return "\n".join(lines)


@tool
def generar_examen_pdf(
    subject_id: str,
    subject_name: str,
    total_questions: int = 5,
    use_bank: bool = True,
) -> str:
    """Genera un examen a partir del banco de preguntas y devuelve un PDF.

    Construye un examen usando las preguntas YA EXISTENTES del banco de la
    materia (si `use_bank=True`) o generando nuevas. Compila el LaTeX a PDF
    y devuelve la ruta del PDF generado en `data/agent_outputs/`.
    """
    from src.agents.graph import run_exam_pipeline
    from src.schemas.exam import (
        BloomLevel,
        Difficulty,
        ExamBlueprint,
    )
    from src.templates.registry import TemplateId

    # Recuperar preguntas del banco para armar el examen (reutilizar, no generar).
    questions = bank.list_questions(
        subject_id=subject_id,
        limit=total_questions,
    )
    if not questions:
        return (
            f"No hay preguntas en el banco para la materia '{subject_name}'. "
            "Primero genera y guarda algunas preguntas, o pide generar un examen "
            "con preguntas nuevas."
        )

    # Construir un blueprint que pida exactamente `total_questions` preguntas,
    # distribuidas uniformemente (el pipeline las generará con RAG del material).
    blueprint = ExamBlueprint(
        subject_id=subject_id,
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
        topics_weight={"General": 1.0},
        estimated_duration_minutes=60,
    )

    try:
        result = run_exam_pipeline(
            subject_id=subject_id,
            subject_name=subject_name,
            template_id=TemplateId.BASE_EXAM,
            raw_materials_paths=[],
            blueprint=blueprint,
            persist=False,  # no duplicar: las preguntas ya están en el banco
        )
    except Exception as e:  # noqa: BLE001
        return f"❌ Error al generar el examen: {str(e)[:300]}"

    pdf_path = None
    if result.get("compiled_exam"):
        pdf_path = result["compiled_exam"].pdf_path

    if not pdf_path:
        return (
            "No se pudo compilar el PDF del examen. "
            f"Status: {result.get('status')} · Error: {result.get('error_message', 'desconocido')}"
        )

    # Subir el PDF a Open WebUI como adjunto nativo del chat.
    try:
        from src.api.openwebui import upload_file_to_openwebui, build_attachment_markdown

        upload_result = upload_file_to_openwebui(pdf_path)
        attachment_md = build_attachment_markdown(upload_result)
    except Exception as e:  # noqa: BLE001
        # Si falla la subida, caemos al enlace HTTP directo.
        filename = Path(pdf_path).name
        attachment_md = (
            f"📄 **Examen generado y compilado a PDF.**\n"
            f"- Materia: **{subject_name}**\n"
            f"- Preguntas: {len(result.get('approved_items', []))}\n"
            f"- 📥 [Descargar PDF](http://localhost:8000/output/{filename})\n\n"
            f"*(No se pudo adjuntar a Open WebUI: {str(e)[:120]})*"
        )

    return (
        f"✅ **Examen generado correctamente.**\n"
        f"- Materia: **{subject_name}**\n"
        f"- Preguntas: {len(result.get('approved_items', []))}\n\n"
        f"{attachment_md}"
    )
