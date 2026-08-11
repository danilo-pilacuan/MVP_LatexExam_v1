# Generador de Exámenes en latex propulsado por agentes de IA

MVP de infraestructura.

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
│   ├── agent_outputs/
│   └── inputs/
│
├── docker/
│   ├── docker-compose.yml
│   ├── embedding-service/
│   │   ├── app.py
│   │   └── Dockerfile
│   └── latex-compiler/
│       ├── app.py
│       └── Dockerfile
│
├── scripts/
│   ├── index_material.py
│   └── run_pipeline.py
│
└── src/
    ├── config.py
    ├── agents/
    │   ├── graph.py
    │   ├── llm.py
    │   ├── nodes.py
    │   ├── persistence.py
    │   ├── retrieval.py
    │   └── state.py
    ├── embeddings/
    │   └── __init__.py
    ├── schemas/
    │   └── exam.py
    ├── templates/
    │   ├── base_exam.tex.jinja
    │   └── registry.py
    ├── utils/
    │   └── latex_templates.py
    │
    └── database/
        ├── connection.py
        ├── models.py
        └── migrations/
            ├── env.py
            ├── README
            ├── script.py.mako
            └── versions/
                ├── 5230ab459f09_initial_schema_with_pgvector.py
                ├── a1b2c3d4e5f6_add_material_chunks_for_rag.py
                └── b2c3d4e5f6a7_adjust_embeddings_1024.py
```
