"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, field_validator
from typing import Annotated

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    NoDecode,
)


class Settings(BaseSettings):
    """Application settings loaded from the .env file."""

    # ==========================================================
    # Database Configuration
    # ==========================================================

    database_url: str

    # ==========================================================
    # JWT Configuration
    # ==========================================================

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # ==========================================================
    # OpenRouter Configuration
    # ==========================================================

    openrouter_base_url: str

    openrouter_api_keys: Annotated[
    list[str],
    NoDecode,
    ] = Field(default_factory=list)

    ai_models: Annotated[
    list[str],
    NoDecode,
    ] = Field(default_factory=list)

    # ==========================================================
    # AI Generation Configuration
    # ==========================================================

    ai_temperature: float
    ai_max_tokens: int
    ai_max_retries: int

    # ==========================================================
    # AI Networking Configuration
    # ==========================================================

    ai_timeout: float
    ai_connect_timeout: float
    ai_write_timeout: float
    ai_pool_timeout: float

    ai_max_connections: int
    ai_max_keepalive: int

    ai_backoff_base_seconds: float

    # ==========================================================
    # OpenRouter Optional Headers
    # ==========================================================

    openrouter_site_url: str = ""
    openrouter_site_name: str = ""

    user_agent: str = "CareerPilotAI/1.0"

    # ==========================================================
    # NVIDIA Embedding Configuration
    # ==========================================================

    # Primary NVIDIA API Key
    nvidia_primary_api_key: str

    # Fallback NVIDIA API Key
    nvidia_fallback_api_key: str

    # NVIDIA Embedding Endpoint
    nvidia_embedding_api_url: str = (
        "https://integrate.api.nvidia.com/v1/embeddings"
    )
    # Future extensibility
    embedding_provider: str = "nvidia"
    # Primary embedding model
    embedding_primary_model: str = (
        "nvidia/nemotron-3-embed-1b"
    )
    # Automatic fallback model
    embedding_fallback_model: str = (
        "nvidia/llama-nemotron-embed-1b-v2"
    )
    # Embedding generation
    embedding_batch_size: int = 100
    embedding_max_retries: int = 3
    embedding_timeout: float = 30.0
    embedding_backoff_base_seconds: float = 1.0
    # Storage
    embedding_storage_directory: str = (
        "data/embeddings"
    )
    # Search
    embedding_similarity_top_k: int = 20


    # ==========================================================
    # Validators
    # ==========================================================

    @field_validator("openrouter_api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, value):
        """
        Convert comma-separated API keys into a list.
        """
        if isinstance(value, str):
            return [
                key.strip()
                for key in value.split(",")
                if key.strip()
            ]
        return value

    @field_validator("ai_models", mode="before")
    @classmethod
    def parse_models(cls, value):
        """
        Convert comma-separated AI models into a list.
        """
        if isinstance(value, str):
            return [
                model.strip()
                for model in value.split(",")
                if model.strip()
            ]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Create and cache the application settings.
    """
    return Settings()


settings = get_settings()