# Generador de Exámenes en latex propulsado por agentes de IA

MVP de infraestructura + agente conversacional con OpenWebUI.

## Infraestructura del `MVP`

```
MVP_v1/
├── .env
├── .gitignore
├── alembic.ini
├── ARCHITECTURE.md
├── main.py
├── readme.md
├── requirements.txt
│
├── data/
│   ├── agent_outputs/        # PDFs de exámenes generados
│   └── inputs/               # material de las materias (PDFs, pptx, etc.)
│
├── docker/
│   ├── docker-compose.yml
│   ├── app/                  # Dockerfile + entrypoint del exam-app
│   ├── embedding-service/
│   └── latex-compiler/
│
├── scripts/
│   ├── index_material.py
│   └── run_pipeline.py
│
├── docs/                     # métricas y análisis de costos (tesis)
│   ├── metrics.md
│   └── cost_analysis.md
│
└── src/
    ├── config.py
    ├── api/
    │   ├── chat.py           # endpoint OpenAI-compatible /v1
    │   └── openwebui.py      # sube PDFs como adjuntos a OpenWebUI
    ├── agents/
    │   ├── graph.py          # pipeline batch (ingestor→...→compilador)
    │   ├── llm.py
    │   ├── nodes.py
    │   ├── persistence.py
    │   ├── retrieval.py
    │   ├── verifier.py       # verificación por IA
    │   ├── state.py
    │   └── conversational/   # agente conversacional (tools, graph, state, prompts)
    ├── bank/
    │   └── service.py        # service layer de escritura segura
    ├── embeddings/
    ├── schemas/
    │   └── exam.py
    ├── templates/
    └── database/
```

## 🚀 Uso rápido (agente conversacional)

```bash
# 1. Levantar toda la infraestructura
cd docker && docker compose up -d --build

# 2. Abrir OpenWebUI (interfaz conversacional)
#    http://localhost:3000  → modelo "exam-agent" ya configurado

# 3. Conversar con el agente
#    - "¿Qué materias tienes?"                    → listar materias
#    - "Dame preguntas sobre Estudio de Mercado"  → recuperar del banco
#    - "Genera una pregunta sobre X"              → generar nueva (RAG)
#    - "Genera un examen de 3 preguntas y dame el PDF" → genera y adjunta PDF
```

## 🧪 Pipeline batch (API tradicional)

```bash
# Indexar material de una materia (RAG)
.venv/Scripts/python.exe scripts/index_material.py \
    --name "Economía Aplicada" \
    --materials "data/inputs/Economia_Aplicada/**/*.pdf"

# Generar un examen (PDF)
.venv/Scripts/python.exe scripts/run_pipeline.py
```

                ├── 5230ab459f09_initial_schema_with_pgvector.py
                ├── a1b2c3d4e5f6_add_material_chunks_for_rag.py
                └── b2c3d4e5f6a7_adjust_embeddings_1024.py
```
