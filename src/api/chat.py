"""API OpenAI-compatible para el agente conversacional.

Expone el agente como un proveedor OpenAI-compatible para que OpenWebUI se
conecte. Endpoints:
  - GET  /v1/models             : lista los modelos disponibles (el agente).
  - POST /v1/chat/completions   : conversación con el agente.

Para el human-in-the-loop, la respuesta puede contener un bloque
`confirmation_required` (con `thread_id` y `interrupt_id`) indicando que el
agente pausó esperando la aprobación del profesor. El cliente (OpenWebUI vía
una tool/acción, o un script) debe reanudar con `Command(resume=...)`.

Uso de streaming: se emite el contenido en chunks SSE (`text/event-stream`).
"""
from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.agents.conversational.graph import conversational_graph
from src.agents.conversational.state import ConversationalState
from langgraph.types import Command

router = APIRouter(prefix="/v1")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "exam-agent"
    messages: list[ChatMessage]
    stream: bool = False
    thread_id: str | None = Field(default=None, description="ID de conversación persistente")
    resume: dict | None = Field(
        default=None,
        description="Para reanudar un interrupt (human-in-the-loop): {'approved': bool}",
    )


def _to_langgraph_messages(messages: list[ChatMessage]) -> list[dict]:
    """Convierte mensajes del formato OpenAI al formato de LangGraph."""
    out = []
    for m in messages:
        if m.role in ("system", "user", "assistant", "tool"):
            out.append({"role": m.role, "content": m.content})
    return out


@router.get("/models")
def list_models():
    """Lista el modelo del agente (formato OpenAI-compatible)."""
    return {
        "object": "list",
        "data": [
            {
                "id": "exam-agent",
                "object": "model",
                "created": 0,
                "owned_by": "tesis-usfq",
            }
        ],
    }


@router.post("/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    """Conversa con el agente. Devuelve la respuesta (streaming o JSON)."""
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Reanudar un interrupt (confirmación humana) o iniciar turno nuevo.
    if req.resume is not None:
        try:
            result = conversational_graph.invoke(
                Command(resume=req.resume),
                config=config,
            )
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Error al reanudar: {str(e)[:200]}")
    else:
        messages = _to_langgraph_messages(req.messages)
        initial: ConversationalState = {
            "messages": messages,
            "subject_id": None,
            "subject_name": None,
            "pending_item": None,
            "pending_question_id": None,
        }
        try:
            result = conversational_graph.invoke(initial, config=config)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Error del agente: {str(e)[:200]}")

    # Extraer el texto de la respuesta final.
    final_messages = result.get("messages", [])
    content = ""
    if final_messages:
        last = final_messages[-1]
        content = getattr(last, "content", "") or ""

    # Detectar si quedó un interrupt pendiente (confirmación humana).
    pending_interrupt = None
    if getattr(result, "interrupts", None):
        pending_interrupt = {
            "thread_id": thread_id,
            "interrupts": [
                {
                    "type": i.type if hasattr(i, "type") else "confirm_write",
                    "value": getattr(i, "value", {}),
                }
                for i in result.interrupts
            ],
        }

    payload = {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "thread_id": thread_id,
        "confirmation_required": pending_interrupt,
    }

    if req.stream:
        async def event_stream():
            # Chunk de rol (inicio de la respuesta).
            yield (
                "data: " + json.dumps({
                    "id": payload["id"],
                    "object": "chat.completion.chunk",
                    "model": req.model,
                    "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
                }, ensure_ascii=False) + "\n\n"
            )
            # Emitir el contenido en trozos (compatible con OpenAI streaming).
            if content:
                for i in range(0, len(content), 20):
                    chunk_text = content[i:i + 20]
                    yield (
                        "data: " + json.dumps({
                            "id": payload["id"],
                            "object": "chat.completion.chunk",
                            "model": req.model,
                            "choices": [{"index": 0, "delta": {"content": chunk_text}, "finish_reason": None}],
                        }, ensure_ascii=False) + "\n\n"
                    )
            # Chunk final.
            yield (
                "data: " + json.dumps({
                    "id": payload["id"],
                    "object": "chat.completion.chunk",
                    "model": req.model,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }, ensure_ascii=False) + "\n\n"
            )
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return payload
