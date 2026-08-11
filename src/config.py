from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    latex_compiler_url: str
    openai_api_key: str = "no-key"  # placeholder; la infra local no valida keys reales

    # --- Proveedor LLM (infra local OpenAI-compatible) ---
    llm_model: str = "deepseek-ai/DeepSeek-V4-Flash-0731"
    llm_base_url: str = "http://172.28.230.10:12555/v1"
    llm_temperature: float = 0.7
    # El servidor vLLM acepta hasta ~100k+ tokens de salida (probado) y el
    # modelo soporta ~384k de salida con 1M de contexto. 65536 da margen
    # amplio para generar el examen completo en una sola pasada o ítems
    # muy elaborados, sin acercarse a los límites del servidor.
    llm_max_tokens: int = 65536
    # Nivel de razonamiento por nodo. El servidor soporta 7 niveles:
    # none | minimal | low | medium | high | xhigh | max
    # IMPORTANTE (vLLM + modelos de razonamiento): si un nodo usa
    # `with_structured_output` (response_format json), el razonamiento
    # consume los tokens de salida y deja `content` vacío → JSON inválido.
    # Por eso Generador y Evaluador usan `none` para producir JSON en content.
    llm_reasoning_generator: str = "none"
    llm_reasoning_evaluator: str = "none"
    # Temperatura más baja para el evaluador (juicio más determinista).
    llm_temperature_evaluator: float = 0.2

    # --- Contexto del modelo (1M tokens) ---
    # Fracción del syllabus que se inyecta como contexto en cada llamada.
    max_context_chars: int = 6000

    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    dedup_similarity_threshold: float = 0.82

    # --- Límites de seguridad del grafo ---
    max_item_retries: int = 3
    max_total_llm_calls: int = 200
    max_compilation_attempts: int = 3

settings = Settings()