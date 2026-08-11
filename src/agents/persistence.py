"""Persistencia de resultados del pipeline en la BD.

Guarda los ítems generados (aprobados y rechazados) junto con sus embeddings
en `generated_questions`, y registra las métricas del examen.
"""
import uuid

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from src.database.connection import SessionLocal
from src.database.models import GeneratedQuestion
from src.embeddings import embedder


def persist_generated_items(
    subject_id: str,
    items: list,
    rejection_log: list,
    total_llm_calls: int,
) -> dict:
    """Guarda los ítems aprobados en `generated_questions` con sus embeddings.

    Devuelve un resumen de lo persistido.
    """
    if not items:
        return {"saved": 0, "subject_id": subject_id}

    # Generar embeddings para todos los ítems aprobados
    texts = [i.statement for i in items]
    vectors = embedder.embed(texts)

    db = SessionLocal()
    saved = 0
    try:
        sid = uuid.UUID(subject_id)
        for item, vec in zip(items, vectors):
            db.add(GeneratedQuestion(
                subject_id=sid,
                topic=item.topic,
                bloom_level=item.bloom_level.value,
                difficulty=item.difficulty.value,
                question_text=item.statement,
                embedding=vec,
            ))
            saved += 1
        db.commit()
    finally:
        db.close()

    return {
        "saved": saved,
        "subject_id": subject_id,
        "rejections": len(rejection_log),
        "total_llm_calls": total_llm_calls,
    }
