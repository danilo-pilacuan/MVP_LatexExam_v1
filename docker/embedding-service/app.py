"""Microservicio de embeddings (OpenAI-compatible /v1/embeddings).

Sirve un modelo de embeddings open-source (sentence-transformers) en un
contenedor Docker. Expone el endpoint estándar `/v1/embeddings` para que el
pipeline lo use como si fuera OpenAI, pero corriendo localmente.

La dimensión del vector es la nativa del modelo (ej. 384 para MiniLM,
1024 para bge-m3). La base de datos se adapta a esta dimensión.
"""
import os
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI(title="Embedding Service")

# Configuración vía variables de entorno
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

print(f"🔄 Cargando modelo de embeddings: {MODEL_NAME} ...")
_model = SentenceTransformer(MODEL_NAME, device=DEVICE)
NATIVE_DIM = _model.get_sentence_embedding_dimension()
print(f"✅ Modelo cargado. Dimensión: {NATIVE_DIM}")


class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str | None = None


class EmbeddingData(BaseModel):
    object: str = "embedding"
    index: int = 0
    embedding: list[float]


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[EmbeddingData]
    model: str
    usage: dict


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME, "dim": NATIVE_DIM}


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
def embed(req: EmbeddingRequest):
    texts = req.input if isinstance(req.input, list) else [req.input]
    vectors = _model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=32,
    )
    data = [
        EmbeddingData(index=i, embedding=np.asarray(v, dtype=np.float32).tolist())
        for i, v in enumerate(vectors)
    ]
    return EmbeddingResponse(
        data=data,
        model=MODEL_NAME,
        usage={"prompt_tokens": len(texts), "total_tokens": len(texts)},
    )

