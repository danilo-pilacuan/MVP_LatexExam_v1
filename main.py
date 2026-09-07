"""API de disponibilización del generador de exámenes.

Endpoints:
  - POST /subjects            : registrar una materia
  - POST /subjects/{id}/index : indexar material (RAG) de una materia
  - POST /exams/generate      : generar un examen a partir de un blueprint
  - GET  /health              : estado del servicio

Uso:
    uvicorn main:app --host 0.0.0.0 --port 8000
"""
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from src.database.connection import SessionLocal  # noqa: E402
from src.database.models import Subject  # noqa: E402
from src.schemas.exam import ExamBlueprint  # noqa: E402
from src.templates.registry import TemplateId  # noqa: E402
from src.api.chat import router as chat_router  # noqa: E402

app = FastAPI(title="Generador de Exámenes API", version="0.1.0")

# Router del agente conversacional (OpenAI-compatible para OpenWebUI).
app.include_router(chat_router)

# Directorio de salida de PDFs (compartido con el latex-compiler vía volumen).
# En el contenedor se monta en /app/output; localmente es data/agent_outputs.
_CANDIDATE_OUTPUT = [
    Path("/app/output"),  # contenedor (volumen compartido con latex-compiler)
    Path(__file__).resolve().parent / "data" / "agent_outputs",  # desarrollo local
]
OUTPUT_DIR = next((p for p in _CANDIDATE_OUTPUT if p.exists()), _CANDIDATE_OUTPUT[-1])
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/output/{filename}")
def download_output(filename: str):
    """Sirve un PDF generado (examen) para descargarlo desde el navegador."""
    # Evitar path traversal: solo el nombre base del archivo.
    safe = Path(filename).name
    file_path = OUTPUT_DIR / safe
    if not file_path.exists() or file_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=safe,
    )


# ---------------------------------------------------------------------------
# Schemas de entrada
# ---------------------------------------------------------------------------
class SubjectIn(BaseModel):
    name: str
    id: str | None = None


class IndexRequest(BaseModel):
    materials: list[str] = Field(
        ..., description="Patrones glob o rutas a los archivos de material"
    )
    clear: bool = False


class ExamRequest(BaseModel):
    subject_id: str
    blueprint: ExamBlueprint
    template_id: str = "base_exam"
    persist: bool = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/subjects")
def create_subject(req: SubjectIn):
    """Registra una materia (o devuelve la existente)."""
    db = SessionLocal()
    try:
        subject = db.query(Subject).filter(Subject.name == req.name).first()
        if subject is None:
            subject = Subject(
                id=uuid.UUID(req.id) if req.id else uuid.uuid4(),
                name=req.name,
            )
            db.add(subject)
            db.commit()
            db.refresh(subject)
            return {"id": str(subject.id), "name": subject.name, "created": True}
        return {"id": str(subject.id), "name": subject.name, "created": False}
    finally:
        db.close()


@app.post("/subjects/{subject_id}/index")
def index_subject(subject_id: str, req: IndexRequest):
    """Indexa el material de una materia (genera chunks + embeddings)."""
    from scripts.index_material import chunk_text, extract_file, resolve_materials

    files = resolve_materials(req.materials)
    if not files:
        raise HTTPException(status_code=400, detail="No se encontraron archivos")

    all_chunks: list[tuple[str, int, str]] = []
    for f in files:
        try:
            text = extract_file(f)
            chunks = chunk_text(text)
            for i, c in enumerate(chunks):
                all_chunks.append((f, i, c))
        except Exception as e:
            print(f"  ⚠️ {f}: {e}")

    if not all_chunks:
        raise HTTPException(status_code=400, detail="No se pudo extraer texto")

    from src.embeddings import embedder
    from src.database.models import MaterialChunk

    contents = [c for _, _, c in all_chunks]
    vectors = embedder.embed(contents)

    db = SessionLocal()
    try:
        sid = uuid.UUID(subject_id)
        subject = db.get(Subject, sid)
        if subject is None:
            raise HTTPException(status_code=404, detail="Materia no existe")

        if req.clear:
            db.query(MaterialChunk).filter(MaterialChunk.subject_id == sid).delete()

        for (src, idx, content), vec in zip(all_chunks, vectors):
            db.add(MaterialChunk(
                subject_id=sid, source_file=src, chunk_index=idx,
                content=content, embedding=vec,
            ))
        db.commit()
        return {"subject_id": subject_id, "indexed_chunks": len(all_chunks)}
    finally:
        db.close()


@app.post("/exams/generate")
def generate_exam(req: ExamRequest):
    """Genera un examen a partir de un blueprint."""
    from src.agents.graph import run_exam_pipeline

    # Resolver template_id
    try:
        template = TemplateId(req.template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Template inválido: {req.template_id}")

    # Obtener el nombre de la materia
    db = SessionLocal()
    try:
        subject = db.get(Subject, uuid.UUID(req.subject_id))
        subject_name = subject.name if subject else "Materia"
    finally:
        db.close()

    result = run_exam_pipeline(
        subject_id=req.subject_id,
        subject_name=subject_name,
        template_id=template,
        raw_materials_paths=[],  # el RAG usa la BD, no archivos directos
        blueprint=req.blueprint,
        persist=req.persist,
    )
    return result
