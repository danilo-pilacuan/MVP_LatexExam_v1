"""Indexa el material de una materia en la BD (RAG).

Uso:
    python scripts/index_material.py --subject-id <id> --name "Economía Aplicada" \
        --materials "data/inputs/Economia_Aplicada/Apuntes/*.pdf"

Este script:
  1. Registra (o actualiza) la materia en la tabla `subjects`.
  2. Lee los archivos de material y los divide en chunks.
  3. Genera embeddings para cada chunk vía el servicio local.
  4. Guarda los chunks + embeddings en `material_chunks`.
"""
import argparse
import glob
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from src.database.connection import SessionLocal  # noqa: E402
from src.database.models import Subject, MaterialChunk  # noqa: E402
from src.embeddings import embedder  # noqa: E402
from src.agents.nodes import (  # noqa: E402
    _extract_pdf,
    _extract_docx,
    _extract_pptx,
    _extract_xlsx,
    _extract_text_file,
)

CHUNK_SIZE = 1500  # caracteres por chunk
CHUNK_OVERLAP = 150  # solapamiento para no cortar ideas


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide un texto en chunks con solapamiento."""
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = end - overlap
    return [c for c in chunks if c]


def extract_file(path: str) -> str:
    """Extrae texto de un archivo según su extensión."""
    ext = path.lower().rsplit(".", 1)[-1] if "." in path else ""
    if ext == "pdf":
        return _extract_pdf(path)
    if ext == "docx":
        return _extract_docx(path)
    if ext == "pptx":
        return _extract_pptx(path)
    if ext == "xlsx":
        return _extract_xlsx(path)
    return _extract_text_file(path)


def resolve_materials(patterns: list[str]) -> list[str]:
    """Expande patrones glob a lista de rutas de archivos."""
    files: list[str] = []
    for pat in patterns:
        files.extend(str(p) for p in glob.glob(pat))
    return sorted(set(files))


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexa material de una materia en la BD")
    parser.add_argument("--subject-id", help="ID de la materia (UUID). Si no existe, se crea.")
    parser.add_argument("--name", required=True, help="Nombre de la materia")
    parser.add_argument(
        "--materials", nargs="+", required=True,
        help="Patrones glob de los archivos de material (ej. 'data/inputs/**/*.pdf')",
    )
    parser.add_argument("--clear", action="store_true", help="Borrar chunks previos de la materia")
    args = parser.parse_args()

    files = resolve_materials(args.materials)
    if not files:
        print("❌ No se encontraron archivos con los patrones dados.")
        sys.exit(1)
    print(f"📚 Archivos a indexar: {len(files)}")

    # Recolectar todos los chunks
    all_chunks: list[tuple[str, int, str]] = []  # (source_file, index, content)
    for f in files:
        try:
            text = extract_file(f)
            chunks = chunk_text(text)
            for i, c in enumerate(chunks):
                all_chunks.append((f, i, c))
            print(f"  ✅ {Path(f).name}: {len(chunks)} chunks")
        except Exception as e:
            print(f"  ⚠️ {Path(f).name}: error {e}")

    if not all_chunks:
        print("❌ No se pudo extraer ningún chunk.")
        sys.exit(1)
    print(f"\n🧩 Total chunks: {len(all_chunks)}")

    # Generar embeddings (en lotes para no exceder el timeout del servicio)
    print("🔄 Generando embeddings...")
    contents = [c for _, _, c in all_chunks]
    vectors: list[list[float]] = []
    batch = 16
    for i in range(0, len(contents), batch):
        part = contents[i:i + batch]
        vectors.extend(embedder.embed(part))
        print(f"  ... {min(i + batch, len(contents))}/{len(contents)}")
    print(f"✅ Embeddings generados: {len(vectors)} (dim={len(vectors[0]) if vectors else 0})")

    # Persistir en BD
    db = SessionLocal()
    try:
        # Registrar/obtener la materia
        if args.subject_id:
            subject = db.get(Subject, uuid.UUID(args.subject_id))
            if subject is None:
                subject = Subject(id=uuid.UUID(args.subject_id), name=args.name)
                db.add(subject)
        else:
            subject = Subject(name=args.name)
            db.add(subject)
            db.flush()  # para obtener el id

        # Limpiar chunks previos si se pide
        if args.clear:
            db.query(MaterialChunk).filter(MaterialChunk.subject_id == subject.id).delete()

        # Insertar chunks
        for (src, idx, content), vec in zip(all_chunks, vectors):
            db.add(MaterialChunk(
                subject_id=subject.id,
                source_file=src,
                chunk_index=idx,
                content=content,
                embedding=vec,
            ))
        db.commit()
        print(f"\n💾 Guardados {len(all_chunks)} chunks para la materia '{subject.name}' (id={subject.id})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
