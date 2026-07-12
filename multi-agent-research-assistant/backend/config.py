"""
Central configuration for the Multi-Agent Research Assistant.
Reads settings from environment variables / .env file.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM provider
    LLM_PROVIDER: str = "openai"  # "openai" or "gemini"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Embeddings
    EMBEDDING_PROVIDER: str = "huggingface"  # "openai" or "huggingface"
    HF_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Storage
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    SQLITE_DB_PATH: str = "./data/app.db"
    UPLOAD_DIR: str = "./data/uploads"

    # Chunking / retrieval
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    RETRIEVAL_K: int = 6

    # Frontend
    BACKEND_URL: str = "http://localhost:8000"


settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.SQLITE_DB_PATH) or ".", exist_ok=True)


def get_llm(temperature: float = 0.3):
    """Return a chat LLM instance based on the configured provider."""
    if settings.LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature,
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
        )


def get_embeddings():
    """Return an embeddings instance based on the configured provider."""
    if settings.EMBEDDING_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
    else:
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=settings.HF_EMBEDDING_MODEL)
