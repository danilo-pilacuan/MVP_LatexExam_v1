# Playground — Generador de Exámenes (MVP_v1)

Prototipo (MVP) de un **generador de exámenes asistido por agentes de IA**.

## Árbol de `MVP_v1`

```
MVP_v1/
├── .env                          # Variables de entorno (DB, API keys, URLs)
├── .gitignore
├── alembic.ini                   # Configuración de migraciones Alembic
├── main.py                       # Punto de entrada de la aplicación (vacío por ahora)
├── requirements.txt              # Dependencias Python
│
├── data/                         # Datos en tiempo de ejecución
│   ├── agent_outputs/            # PDFs generados por los agentes
│   │   └── ab85b632-...pdf       # Ejemplo de examen compilado
│   └── inputs/                   # Entradas (silabarios, temas, etc.)
│
├── docker/                       # Contenedores auxiliares
│   ├── docker-compose.yml        # Orquesta Postgres (pgvector) + compilador LaTeX
│   └── latex-compiler/           # Microservicio de compilación LaTeX
│       ├── app.py                # API FastAPI: POST /compile (pdflatex)
│       └── Dockerfile
│
└── src/                          # Código fuente de la aplicación
    ├── config.py                 # Configuración central (Settings con pydantic-settings)
    ├── agents/                   # Agentes (LangGraph/LangChain) — vacío
    ├── schemas/                  # Esquemas Pydantic — vacío
    ├── templates/                # Plantillas (ej. plantillas LaTeX) — vacío
    ├── utils/                    # Utilidades — vacío
    │
    └── database/                 # Capa de persistencia
        ├── connection.py         # Motor SQLAlchemy y sesión
        ├── models.py             # Modelos: Subject, SyllabusTopic, GeneratedQuestion
        └── migrations/           # Migraciones Alembic
            ├── env.py
            ├── README
            ├── script.py.mako
            └── versions/
                └── 5230ab459f09_initial_schema_with_pgvector.py   # Esquema inicial
```

## Descripción

**MVP_v1** es un prototipo (MVP) de un **generador de exámenes asistido por agentes de IA**. La arquitectura se organiza en tres capas principales:

**1. Orquestación de agentes (`src/agents/`, `main.py`)**: Aunque los directorios `agents/`, `schemas/`, `templates/` y `utils/` aún están vacíos, el proyecto está preparado para usar **LangGraph/LangChain** (según `requirements.txt`) para coordinar agentes que generen preguntas de examen. El `main.py` es el punto de entrada que dará vida a este flujo.

**2. Persistencia con PostgreSQL + pgvector (`src/database/`)**: La base de datos guarda **materias** (`Subject`), **temas del silabario** (`SyllabusTopic`) y **preguntas generadas** (`GeneratedQuestion`). Cada pregunta almacena su **embedding vectorial** (dimensión 1536) mediante la extensión **pgvector**, lo que permite búsquedas semánticas y deduplicación de preguntas similares (umbral de similitud configurable en `config.py`). Las migraciones están gestionadas con **Alembic**.

**3. Servicios auxiliares en Docker (`docker/`)**: El `docker-compose.yml` levanta dos contenedores:
- **Postgres con pgvector** (puerto 5432) para la base de datos.
- **Compilador LaTeX** (puerto 8080), un microservicio FastAPI que recibe código LaTeX vía `POST /compile` y produce un PDF usando `pdflatex`, guardando el resultado en `data/agent_outputs/`.

En resumen, el flujo previsto es: los **agentes de IA** generan preguntas → se almacenan con sus **embeddings** en Postgres/pgvector → se ensamblan en un documento **LaTeX** → el **compilador Docker** lo convierte a **PDF**. El proyecto está en una fase temprana: la infraestructura (DB, migraciones, compilador, configuración) ya está montada, pero la lógica de agentes aún no se ha implementado.
