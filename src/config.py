from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    latex_compiler_url: str
    openai_api_key: str

    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    dedup_similarity_threshold: float = 0.82

settings = Settings()