# 🏛 Arquitectura objetivo — Monorepo por apps (arquitectura limpia) + repos múltiples vía submódulos

> **Estado:** diseño aprobado, pendiente de migración. Fecha: 2026-10-04.
> **Origen:** nueva directriz — `src/` deja de ser el paquete único de Python y la raíz del repo pasa a ser la raíz de proyectos (`apps/`), donde cada aplicación tiene su propio `src`, sus tests y su tooling.
> **Control de versiones:** cada app/lib vive en **su propio repositorio Git**, orquestados por un repo raíz ("meta-repo") mediante **submódulos git** (ver §8).
> **Complementa:** [ARCHITECTURE.md](../ARCHITECTURE.md) (documentación técnica vigente) y [plan-frontendChatEmbebido.prompt.md](../plan-frontendChatEmbebido.prompt.md) (plan del frontend con chat embebido).

---

## 1. Principios

1. **Un proyecto por carpeta**: cada app es autocontenida (código, tests, Dockerfile, dependencias). Nada de un `src/` global que mezcle dominios.
2. **Arquitectura limpia por app**: capas `domain → application → interface adapters → infrastructure`, con la regla de dependencias apuntando siempre hacia adentro (el dominio no conoce FastAPI, Vue ni Docker).
3. **Convenciones del framework**: se respeta el scaffold recomendado de cada herramienta — Vite/create-vue para el frontend, la estructura oficial de FastAPI (routers/schemas/services/core) para las APIs Python.
4. **Shared kernel explícito**: lo que comparten varias apps (modelos de BD, banco de preguntas, esquemas, clientes de infraestructura) vive en `libs/core`, no se duplica.
5. **Grafo de dependencias acíclico**:

```
frontend ──> exam-app ──> agents-backend ──> libs/core
                                 │                ▲
                                 └────────────────┘
```

Ninguna capa puede importar "hacia arriba" (libs/core no conoce agents-backend; agents-backend no conoce exam-app; exam-app no conoce Vue).

---

## 2. Estructura de directorios objetivo

```
MVP_v1/
├── apps/
│   ├── frontend/                          # Vue 3 + Vite + TS + Pinia (scaffold create-vue)
│   │   ├── src/
│   │   │   ├── api/                       # clientes: http.ts (REST), sse.ts (chat), ws.ts (bus)
│   │   │   ├── assets/
│   │   │   ├── components/
│   │   │   │   ├── chat/                  # ChatPanel, MessageList, ToolActivity,
│   │   │   │   │                          # ArtifactCard, HITLButtons, FileDrop, MarkdownRenderer
│   │   │   │   └── widgets/               # QuestionCard, QuestionsTable, ArtifactDownload…
│   │   │   ├── composables/               # useChatStream, useEventBus, useThreadId
│   │   │   ├── router/                    # Vue Router (Chat · Materias · Banco · Exámenes · Material)
│   │   │   ├── stores/                    # Pinia: chat, subjects, bank, exams, material
│   │   │   ├── types/                     # schema tipado de eventos SSE/WS (versionado)
│   │   │   ├── views/                     # ChatView, SubjectsView, BankView, ExamsView, MaterialView
│   │   │   ├── App.vue
│   │   │   └── main.ts
│   │   ├── tests/                         # Vitest + Vue Test Utils
│   │   ├── Dockerfile                     # build Vite → nginx
│   │   ├── .env.development               # VITE_API_URL, VITE_WS_URL
│   │   └── package.json / vite.config.ts / tsconfig*.json
│   │
│   ├── exam-app/                          # FastAPI — API pública (BFF del frontend)
│   │   ├── src/exam_app/
│   │   │   ├── main.py                    # app factory: CORS, lifespan, montaje de routers
│   │   │   ├── api/
│   │   │   │   ├── deps.py                # dependencias (sesión BD, engine, auth futura)
│   │   │   │   └── v1/
│   │   │   │       ├── chat.py            # POST /api/chat/stream (SSE) · POST /api/chat
│   │   │   │       ├── files.py           # POST /api/files (adjuntos propios)
│   │   │   │       ├── subjects.py        # materias + indexación
│   │   │   │       ├── questions.py       # banco de preguntas
│   │   │   │       ├── exams.py           # generación de exámenes
│   │   │   │       ├── ws.py              # WS /ws (bus: notificaciones, cancelación)
│   │   │   │       └── legacy_openai.py   # /v1/chat/completions (OpenWebUI legado, intacto)
│   │   │   ├── core/                      # config (pydantic-settings), logging, CORS, lifespan
│   │   │   ├── schemas/                   # DTOs request/response + eventos SSE tipados
│   │   │   ├── services/                  # aplicación: chat_engine, file_service, event_bus
│   │   │   └── domain/                    # puertos (interfaces) hacia agents-backend y libs/core
│   │   ├── tests/
│   │   ├── Dockerfile + entrypoint.sh     # alembic upgrade head + uvicorn
│   │   └── requirements.txt (o pyproject.toml)
│   │
│   ├── agents-backend/                    # Motor LangGraph (dominio de agentes)
│   │   ├── src/agents_backend/
│   │   │   ├── exam_pipeline/             # grafo batch: nodes, state, graph, metrics
│   │   │   ├── conversational/            # grafo conversacional: graph, prompts, state, tools
│   │   │   └── shared/                    # llm.py (fábrica), retrieval.py, verifier.py,
│   │   │                                  # persistence.py (checkpointer), events.py (emisor tipado)
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── latex-compiler/                    # microservicio FastAPI + TeXLive
│   │   ├── src/latex_compiler/app.py
│   │   └── Dockerfile
│   │
│   └── embedding-service/                 # microservicio FastAPI + sentence-transformers (bge-m3)
│       ├── src/embedding_service/app.py
│       └── Dockerfile
│
├── libs/
│   └── core/                              # shared kernel (dominio + infraestructura compartida)
│       ├── src/core/
│       │   ├── config.py                  # pydantic-settings (antes src/config.py)
│       │   ├── domain/
│       │   │   ├── models.py              # entidades SQLAlchemy (Subject, Question, MaterialChunk…)
│       │   │   ├── bank/                  # service.py — escritura segura del banco
│       │   │   └── schemas/               # exam.py, tools.py (blueprints, ItemSpec, GeneratedItem)
│       │   └── infrastructure/
│       │       ├── db/                    # connection.py + migrations/ (Alembic)
│       │       ├── embeddings/            # cliente del embedding-service
│       │       ├── latex/                 # cliente del latex-compiler, templates/, utils/
│       │       └── files/                 # extract_file_text, gestión de data/inputs
│       ├── tests/
│       └── pyproject.toml
│
├── data/                                  # volúmenes: inputs/, agent_outputs/ (sin código)
├── docker/                                # docker-compose.yml de desarrollo (+ openwebui legado)
├── deploy/                                # compose de producción + up/down.sh
├── docs/
├── scripts/                               # CLI operativos: index_material.py, run_pipeline.py
├── alembic.ini                            # apunta a libs/core/src/core/infrastructure/db/migrations
└── readme.md
```

### Reglas de convivencia

- `data/`, `docker/`, `deploy/`, `docs/`, `scripts/` conservan su rol actual; solo cambian los imports de `scripts/`.
- Los Dockerfiles se mueven **dentro** de cada app (`apps/<app>/Dockerfile`); `docker/docker-compose.yml` queda como orquestador de desarrollo.
- `tests/` global desaparece: cada app/lib tiene su propio `tests/` (pytest para Python, Vitest para el frontend).
- No hay `src/` en la raíz del repo; cada `src` pertenece a exactamente una app o lib.

---

## 3. Arquitectura limpia por proyecto

### 3.1 `apps/frontend` — presentación (Vue 3 + Vite)

Scaffold oficial de **create-vue** (Vite): `src/{api, assets, components, composables, router, stores, views}`.

| Capa | Contenido |
|---|---|
| Views + components | Pantallas Materias/Banco/Exámenes/Material y el `ChatPanel` con sus widgets |
| Composables | `useChatStream` (SSE con reconexión), `useEventBus` (WS), `useThreadId` |
| Stores (Pinia) | Estado de conversaciones, materias, banco, exámenes |
| api/ | Único punto que conoce URLs del backend (`VITE_API_URL`, `VITE_WS_URL`) |

Regla: ningún componente llama a `fetch` directamente; todo pasa por `src/api/`. Los tipos de eventos SSE/WS se definen en `src/types/` y se versionan junto con el backend (ver §5).

### 3.2 `apps/exam-app` — interface adapters + aplicación (FastAPI)

Estructura recomendada por la documentación oficial de FastAPI, adaptada a arquitectura limpia:

| Capa | Carpeta | Responsabilidad |
|---|---|---|
| Interface adapters | `api/v1/` | Routers HTTP/WS/SSE. Validan entrada, delegan, formatean salida. Sin lógica de negocio. |
| DTOs | `schemas/` | Modelos Pydantic de request/response y el **schema tipado de eventos** (`token`, `tool_start`, `tool_end`, `artifact_ready`, `done`, `error`…). |
| Aplicación | `services/` | Casos de uso: `chat_engine` (orquesta `astream_events` del grafo en threadpool), `file_service` (extraer → guardar → indexar), `event_bus` (WS). |
| Dominio (puertos) | `domain/` | Interfaces (`ChatEnginePort`, `BankPort`, `FileStoragePort`) que desacoplan exam-app de las implementaciones. |
| Core | `core/` | Config con pydantic-settings, CORS, logging, lifespan. |

Regla: los routers nunca importan de `agents_backend` ni de `core` (libs) directamente; pasan por `services/`, que consume los puertos de `domain/`. Esto permite testear exam-app con dobles de prueba.

### 3.3 `apps/agents-backend` — dominio de agentes (LangGraph)

El corazón del sistema. Aquí viven los dos grafos:

| Módulo | Contenido actual que migra |
|---|---|
| `exam_pipeline/` | `src/agents/{graph,nodes,state,metrics}.py` — grafo batch de generación de exámenes |
| `conversational/` | `src/agents/conversational/{graph,prompts,state,tools}.py` — agente conversacional con HITL |
| `shared/` | `llm.py` (fábrica del LLM), `retrieval.py` (RAG), `verifier.py`, `persistence.py` (checkpointer PostgresSaver), `events.py` (**nuevo**: emisor de eventos tipados `question_generated`, `questions_listed`, `artifact_ready`, `material_indexed`) |

Reglas de arquitectura limpia:
- Los nodos/tools son funciones puras sobre el estado; la infraestructura (BD, LLM, microservicios) se inyecta o se accede vía `libs/core`.
- `events.py` es la pieza clave del plan de frontend: las tools emiten eventos tipados **en paralelo al markdown**, y exam-app los reenvía por SSE sin conocer su semántica.
- `_PENDING_ITEM` (global de módulo en `tools.py`) migra al estado del grafo (`ConversationalState`) — el checkpointer ya lo persiste por thread.

### 3.4 `libs/core` — shared kernel (dominio + infraestructura compartida)

Lo que usan exam-app y agents-backend sin duplicar:

| Capa | Contenido |
|---|---|
| Dominio | `models.py` (entidades SQLAlchemy), `bank/` (reglas de escritura segura: preguntas verificadas por humano son inmutables), `schemas/` (blueprints, ítems) |
| Infraestructura | `db/` (connection + migraciones Alembic), `embeddings/` (cliente del embedding-service), `latex/` (cliente del latex-compiler + templates Jinja2), `files/` (extracción de texto multi-formato) |
| Config | `config.py` (pydantic-settings, lee `.env`) |

Regla: `libs/core` **no depende** de ninguna app. Es la capa más interna del monorepo.

### 3.5 Microservicios (`latex-compiler`, `embedding-service`)

Ya son servicios independientes; solo se reubican a `apps/` con su propio `src/<paquete>/app.py` y Dockerfile. Sin cambios de diseño (FastAPI de un archivo es suficiente para su tamaño; si crecen, adoptan la misma estructura routers/services).

---

## 4. Mapa de migración (código actual → destino)

| Actual | Destino |
|---|---|
| `main.py` | `apps/exam-app/src/exam_app/main.py` (endpoints → routers en `api/v1/`) |
| `src/api/chat.py` | `apps/exam-app/.../api/v1/legacy_openai.py` + `services/chat_engine.py` |
| `src/api/openwebui.py` | `apps/exam-app/.../infrastructure/openwebui_client.py` (legado) |
| `src/agents/graph.py`, `nodes.py`, `state.py`, `metrics.py` | `apps/agents-backend/src/agents_backend/exam_pipeline/` |
| `src/agents/conversational/*` | `apps/agents-backend/src/agents_backend/conversational/` |
| `src/agents/{llm,retrieval,verifier,persistence}.py` | `apps/agents-backend/src/agents_backend/shared/` |
| `src/database/connection.py` | `libs/core/src/core/infrastructure/db/connection.py` |
| `src/database/migrations/*` | `libs/core/src/core/infrastructure/db/migrations/` |
| `src/database/models.py` | `libs/core/src/core/domain/models.py` |
| `src/bank/*` | `libs/core/src/core/domain/bank/` |
| `src/schemas/*` | `libs/core/src/core/domain/schemas/` |
| `src/templates/*` | `libs/core/src/core/infrastructure/latex/templates/` |
| `src/utils/latex_templates.py` | `libs/core/src/core/infrastructure/latex/utils.py` |
| `src/embeddings/` | `libs/core/src/core/infrastructure/embeddings/` |
| `src/config.py` | `libs/core/src/core/config.py` |
| `scripts/*` | `scripts/` (solo cambian imports) |
| `tests/*` | `apps/<app>/tests/` y `libs/core/tests/` según lo que prueben |
| `docker/app/Dockerfile` + `entrypoint.sh` | `apps/exam-app/Dockerfile` + `entrypoint.sh` |
| `docker/latex-compiler/*` | `apps/latex-compiler/` |
| `docker/embedding-service/*` | `apps/embedding-service/` |
| `docker/openwebui-custom/*` | `docker/openwebui/` (legado, opcional) |
| `alembic.ini` | raíz del repo, `script_location` → `libs/core/.../migrations` |

**Estrategia de migración:** mover con `git mv` para conservar historial, en un solo commit de reestructuración sin cambios de lógica; luego un commit de actualización de imports/paths; después actualizar compose/Dockerfiles y validar con la suite de tests y un pipeline end-to-end.

---

## 5. Contrato de eventos (SSE/WS) — decisión de diseño

Resuelve las decisiones abiertas del plan de frontend sobre el formato de eventos:

```jsonc
// SSE: event: <tipo> · data: <payload JSON>
{ "v": 1, "type": "token",       "thread_id": "…", "delta": "…" }
{ "v": 1, "type": "tool_start",  "thread_id": "…", "name": "buscar_preguntas", "call_id": "…" }
{ "v": 1, "type": "tool_end",    "thread_id": "…", "name": "buscar_preguntas", "call_id": "…", "result": "…" }
{ "v": 1, "type": "question_generated", "thread_id": "…", "question": { /* GeneratedItem */ } }
{ "v": 1, "type": "artifact_ready",     "thread_id": "…", "kind": "pdf|csv|xlsx", "url": "/output/…", "filename": "…" }
{ "v": 1, "type": "material_indexed",   "thread_id": "…", "chunks": 42 }
{ "v": 1, "type": "done",        "thread_id": "…" }
{ "v": 1, "type": "error",       "thread_id": "…", "message": "…" }
```

- Campo `v` para versionado del schema; los tipos viven en `apps/exam-app/.../schemas/events.py` y se espejan en `apps/frontend/src/types/events.ts`.
- El WebSocket (`/ws`) usa el mismo schema para notificaciones push y cancelación (`{ "type": "cancel", "thread_id": "…" }`).

---

## 6. Decisiones cerradas por esta arquitectura

| Decisión abierta del plan | Resolución |
|---|---|
| ¿Servir el build de Vue desde exam-app o nginx? | Contenedor **nginx separado** (`apps/frontend/Dockerfile`); en dev, Vite dev-server con proxy a exam-app. exam-app queda API-only (más limpio con la nueva estructura). |
| ¿Nombre de la carpeta del frontend? | `apps/frontend/` |
| ¿Formato de eventos SSE? | Schema versionado de §5, definido en exam-app y espejado en el frontend |
| ¿Historial de chats? | MVP: `localStorage` en el frontend; endpoint de listado de threads queda como mejora posterior en `api/v1/chat.py` |
| ¿Cancelar generación? | WS `cancel` → exam-app marca el thread como cancelado en el `event_bus` y descarta la respuesta; abortar el thread del grafo queda como mejora |
| ¿Auth mínima? | Sin auth en el MVP; `api/deps.py` queda preparado para inyectarla después |

---

## 7. Impacto en el plan de fases

El plan de [plan-frontendChatEmbebido.prompt.md](../plan-frontendChatEmbebido.prompt.md) se amplía con una **Fase 0** previa:

- **F0 — Reestructuración del monorepo** (1-2 sesiones): ejecutar el mapa de migración de §4, actualizar imports, Dockerfiles, compose, alembic y tests. Criterio de aceptación: suite de tests verde + pipeline end-to-end genera PDF + exam-app responde en el mismo puerto 8000.
- F1-F5 del plan se ejecutan **sobre la nueva estructura** (los archivos nuevos ya nacen en `apps/exam-app` y `apps/frontend`).

---

## 8. Control de versiones — repo raíz + submódulos git

Con varios proyectos en juego, un único repo dificulta el versionado independiente (un cambio en el frontend no debería forzar un release del backend, y viceversa). La solución adoptada: **cada app/lib es un repositorio Git independiente**, y un **repo raíz (meta-repo)** los encapsula como **submódulos git**, fijando qué commit de cada app compone una versión coherente del sistema.

### 8.1 Topología de repos

| Repositorio | Ruta local | Contenido |
|---|---|---|
| `MVP_LatexExam` (meta-repo) | `MVP_v1/` | Submódulos + orquestación (compose, scripts, docs, `.env.example`) |
| `mvp-frontend` | `apps/frontend/` | Vue 3 + Vite + TS + Pinia |
| `mvp-exam-app` | `apps/exam-app/` | FastAPI — API pública/BFF |
| `mvp-agents-backend` | `apps/agents-backend/` | LangGraph — grafos + eventos tipados |
| `mvp-latex-compiler` | `apps/latex-compiler/` | Microservicio TeXLive |
| `mvp-embedding-service` | `apps/embedding-service/` | Microservicio bge-m3 |
| `mvp-core` | `libs/core/` | Shared kernel: modelos, banco, migraciones, clientes |

Lo que **queda solo en el meta-repo** (no es código de ninguna app): `data/`, `docker/` (compose de desarrollo), `deploy/`, `docs/`, `scripts/` operativos, `alembic.ini`, `readme.md`, `ARCHITECTURE.md`.

### 8.2 Estructura del meta-repo

```
MVP_v1/                              # repo raíz (meta-repo)
├── apps/
│   ├── frontend/                    # → submodule mvp-frontend
│   ├── exam-app/                    # → submodule mvp-exam-app
│   ├── agents-backend/              # → submodule mvp-agents-backend
│   ├── latex-compiler/              # → submodule mvp-latex-compiler
│   └── embedding-service/           # → submodule mvp-embedding-service
├── libs/
│   └── core/                        # → submodule mvp-core
├── data/ · docker/ · deploy/ · docs/ · scripts/
├── alembic.ini · readme.md · ARCHITECTURE.md
└── .gitmodules
```

`.gitmodules` resultante:

```ini
[submodule "apps/frontend"]
	path = apps/frontend
	url = git@github.com:danilo-pilacuan/mvp-frontend.git
[submodule "apps/exam-app"]
	path = apps/exam-app
	url = git@github.com:danilo-pilacuan/mvp-exam-app.git
[submodule "apps/agents-backend"]
	path = apps/agents-backend
	url = git@github.com:danilo-pilacuan/mvp-agents-backend.git
[submodule "apps/latex-compiler"]
	path = apps/latex-compiler
	url = git@github.com:danilo-pilacuan/mvp-latex-compiler.git
[submodule "apps/embedding-service"]
	path = apps/embedding-service
	url = git@github.com:danilo-pilacuan/mvp-embedding-service.git
[submodule "libs/core"]
	path = libs/core
	url = git@github.com:danilo-pilacuan/mvp-core.git
```

### 8.3 Flujo de trabajo diario

```bash
# Clonar todo (meta-repo + submódulos)
git clone --recurse-submodules git@github.com:danilo-pilacuan/MVP_LatexExam.git
cd MVP_LatexExam
git submodule update --init --recursive        # si se olvidó --recurse

# Actualizar todos los submódulos a lo último de su rama principal
git submodule update --remote --merge

# Trabajar DENTRO de un submódulo (es un repo git normal)
cd apps/exam-app
git checkout -b feat/sse-chat
# ... cambios, commit ...
git push origin feat/sse-chat                  # push al repo de la app

# Volver al meta-repo y fijar el nuevo commit de exam-app
cd ../..
git add apps/exam-app                          # registra el nuevo SHA del submódulo
git commit -m "chore: bump exam-app a feat/sse-chat"
```

Reglas de oro:

1. **Commitear siempre en dos niveles**: primero push del submódulo, luego commit del puntero en el meta-repo. Un meta-repo con punteros a SHAs no pusheados rompe a los demás (`git status` en submódulos lo detecta: `new commits` + `modified content`).
2. **El meta-repo nunca contiene código de apps**: solo punteros, compose, docs y data.
3. **CI por repo**: cada app tiene su propio pipeline (tests/lint/build). El meta-repo tiene un pipeline de integración que construye el sistema completo con los SHAs fijados.

### 8.4 Versionado y releases

- **Cada app versiona independiente** con tags semánticos (`mvp-exam-app v1.3.0`).
- **El meta-repo fija releases del sistema** con tags (`MVP_LatexExam v0.4.0` = combinación exacta de SHAs de las 7 apps). `deploy/` compone siempre desde un tag del meta-repo → despliegues reproducibles.
- **`libs/core` es el punto crítico**: al ser dependencia de exam-app y agents-backend, sus cambios deben ser **retrocompatibles** o coordinados. Regla práctica: bump de versión mayor de core ⇒ actualizar y testear las apps que lo consumen antes de fijar el puntero en el meta-repo.

### 8.5 Alternativas consideradas

| Opción | Por qué no |
|---|---|
| Monorepo único (todo en un repo) | Versionado acoplado; el repo crece con historial mezclado de 7 proyectos; permisos/CI por app imposibles |
| Subárboles (`git subtree`) | Sin punteros visibles de versión, historial duplicado en el meta-repo, flujos de push/pull más propensos a error |
| Package managers (npm workspace / pip packages privados) | Solo resuelve dependencias de código, no la orquestación de repos ni el versionado del sistema completo |

Submódulos gana porque: punteros explícitos a commits (reproducibilidad), cada app mantiene su historial y CI limpios, y el tooling (compose, deploy) vive en un lugar neutro.

### 8.6 Impacto en la migración (F0)

La Fase 0 del plan se amplía con estos pasos al final de la reestructuración:

1. Reestructurar directorios e imports **dentro del repo actual** (como estaba planeado en §4) y validar: tests + pipeline end-to-end.
2. Crear los 7 repos remotos (`mvp-frontend`, `mvp-exam-app`, `mvp-agents-backend`, `mvp-latex-compiler`, `mvp-embedding-service`, `mvp-core`, y el meta-repo `MVP_LatexExam`).
3. Para cada app/lib: `git init` en su carpeta → commit inicial con su historial recortado (opcional: `git filter-repo` para conservar solo el historial de esa ruta) → push al remoto.
4. En el meta-repo: eliminar las carpetas del índice del repo raíz y volver a agregarlas como `git submodule add`.
5. Mover `docker/`, `deploy/`, `docs/`, `scripts/`, `alembic.ini` al meta-repo (ya están).
6. Validar clon limpio: `git clone --recurse-submodules` + `docker compose up` funcional.

> **Nota sobre `data/`**: los volúmenes con material de materias y outputs no se versionan en ningún repo (solo `.gitkeep` + `.gitignore` en el meta-repo). Si el material de la tesis debe persistir, se gestiona aparte (backup/almacenamiento institucional), no vía git.
