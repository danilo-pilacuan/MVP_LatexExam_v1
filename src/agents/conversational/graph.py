"""Grafo conversacional del agente con human-in-the-loop.

Flujo:
  - El LLM recibe el historial (`messages`) y el system prompt.
  - Puede invocar tools (buscar, generar, guardar, confirmar verificación).
  - Las tools de ESCRITURA (`guardar_pregunta`, `confirmar_verificacion_humana`)
    pasan por un nodo de confirmación humana con `interrupt`: el grafo PAUSA
    y espera la aprobación del humano antes de ejecutarlas.
  - El checkpointer persiste el estado entre turnos.

El grafo se expone como endpoint OpenAI-compatible para conectarlo a OpenWebUI.
"""
from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from langchain_core.messages import ToolMessage

from src.agents.conversational.prompts import SYSTEM_PROMPT
from src.agents.conversational.state import ConversationalState
from src.agents.conversational.tools import (
    buscar_preguntas,
    confirmar_verificacion_humana,
    generar_examen_pdf,
    generar_pregunta,
    guardar_pregunta,
    listar_materias,
)
from src.agents.llm import get_llm
from src.config import settings

TOOLS = [
    listar_materias,
    buscar_preguntas,
    generar_pregunta,
    guardar_pregunta,
    confirmar_verificacion_humana,
    generar_examen_pdf,
]
TOOL_BY_NAME = {t.name: t for t in TOOLS}

# Tools que implican ESCRITURA en la BD → requieren confirmación humana.
WRITE_TOOLS = {"guardar_pregunta", "confirmar_verificacion_humana"}


def _make_llm():
    """LLM del agente conversacional con las tools vinculadas.

    IMPORTANTE: se usa `reasoning_effort="none"` (igual que el pipeline batch).
    DeepSeek-V4-Flash es un modelo de razonamiento: con reasoning_effort > none,
    vLLM pone el output en el campo `reasoning` y deja `content` VACÍO, lo que
    hace que las respuestas del chat vuelvan vacías. Con `none`, el contenido
    sale en `content` y el chat funciona correctamente.
    """
    llm = get_llm(reasoning_effort="none", temperature=0.4)
    return llm.bind_tools(TOOLS)


def _assistant_node(state: ConversationalState) -> dict:
    """Nodo principal: el LLM decide responder o llamar a una tool."""
    llm = _make_llm()
    response = llm.invoke(
        [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
    )
    return {"messages": [response]}


def _call_tools_node(state: ConversationalState) -> dict:
    """Ejecuta las tool calls del último mensaje, con human-in-the-loop.

    Para las tools de escritura, se usa `interrupt` para pausar el grafo y
    pedir confirmación humana. Si se reanuda sin aprobación, no se ejecuta.
    """
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", []) or []
    if not tool_calls:
        return {"messages": []}

    results: list[ToolMessage] = []
    for tool_call in tool_calls:
        name = tool_call["name"]
        args = tool_call.get("args", {})
        tool_id = tool_call["id"]

        # Guardrail: ¿es una tool de escritura?
        if name in WRITE_TOOLS:
            # Pausar y pedir confirmación humana.
            decision = interrupt(
                {
                    "type": "confirm_write",
                    "tool": name,
                    "args": args,
                    "message": (
                        "¿Confirmas esta acción de escritura en el banco de preguntas? "
                        "Responde 'sí' para aprobar o 'no' para cancelar."
                    ),
                }
            )
            approved = bool(decision) and decision.get("approved", False)
            if not approved:
                results.append(
                    ToolMessage(
                        content=(
                            "Acción de escritura cancelada por el profesor. "
                            "No se realizó ningún cambio en el banco."
                        ),
                        tool_call_id=tool_id,
                    )
                )
                continue

        # Ejecutar la tool (aprobada o de solo lectura).
        tool = TOOL_BY_NAME[name]
        try:
            content = tool.invoke(args)
        except Exception as e:  # noqa: BLE001
            content = f"❌ Error al ejecutar {name}: {str(e)[:200]}"
        results.append(ToolMessage(content=content, tool_call_id=tool_id))

    return {"messages": results}


def _build_postgres_checkpointer():
    """Crea un checkpointer persistente en PostgreSQL.

    Usa la misma BD del proyecto (DATABASE_URL). La tabla `checkpoints` se
    crea con `.setup()` al primer uso.
    """
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg import Connection

    dsn = settings.database_url
    conn = Connection.connect(dsn)
    saver = PostgresSaver(conn)
    saver.setup()  # crea la tabla `checkpoints` si no existe
    return saver


def build_conversational_graph(checkpointer=None):
    """Construye y compila el grafo conversacional.

    Por defecto usa un checkpointer PERSISTENTE en PostgreSQL (para retomar
    conversaciones entre reinicios). Si `checkpointer` se provee, se usa ese.
    """
    if checkpointer is None:
        try:
            checkpointer = _build_postgres_checkpointer()
        except Exception:  # noqa: BLE001
            # Fallback a memoria si no hay BD disponible.
            checkpointer = InMemorySaver()

    graph = StateGraph(ConversationalState)

    graph.add_node("assistant", _assistant_node)
    graph.add_node("tools", _call_tools_node)

    graph.add_edge(START, "assistant")
    # Si el LLM pidió tools → tools; si no, termina.
    graph.add_conditional_edges(
        "assistant",
        lambda state: "tools" if (state["messages"][-1].tool_calls) else END,
        {"tools": "tools", END: END},
    )
    graph.add_edge("tools", "assistant")

    return graph.compile(checkpointer=checkpointer)


# Singleton del grafo (reutilizable, con checkpointer en memoria por defecto).
conversational_graph = build_conversational_graph()
