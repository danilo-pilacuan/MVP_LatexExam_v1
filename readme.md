# Generador de Exámenes en latex propulsado por agentes de IA

MVP de infraestructura.

## Infraestructura del `MVP`

```
MVP_v1/
├── .env                          
├── .gitignore
├── alembic.ini                   
├── main.py                       
├── requirements.txt              
│
├── data/                         
│   ├── agent_outputs/            
│   │   └── ab85b632-...pdf       
│   └── inputs/                   
│
├── docker/                       
│   ├── docker-compose.yml        
│   └── latex-compiler/           
│       ├── app.py                
│       └── Dockerfile
│
└── src/                          
    ├── config.py                 
    ├── agents/                   
    ├── schemas/                  
    ├── templates/                
    ├── utils/                    
    │
    └── database/                 
        ├── connection.py         
        ├── models.py             
        └── migrations/           
            ├── env.py
            ├── README
            ├── script.py.mako
            └── versions/
                └── 5230ab459f09_initial_schema_with_pgvector.py   
```
