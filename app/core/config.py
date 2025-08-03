"""
Configuration settings for AEON
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4"
    openai_embedding_model: str = "text-embedding-ada-002"
    
    # Database Configuration
    database_url: str = "sqlite:///./aeon.db"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "aeon123456"
    neo4j_database: str = "neo4j"
    
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    
    # Application Configuration
    app_name: str = "AEON"
    app_version: str = "0.1.0"
    debug: bool = True
    log_level: str = "INFO"
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # Development
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 