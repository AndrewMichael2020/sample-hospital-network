"""
Configuration settings for the extended API.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Database settings
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "lm_synth"
    
    # API settings
    api_title: str = "Healthcare Scenarios API"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    debug: bool = False
    
    # CORS settings
    cors_origins: list = ["*"]
    
    class Config:
        env_file = ".env"
        env_prefix = ""


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get database connection URL."""
    return (
        f"mysql+asyncmy://{settings.mysql_user}:{settings.mysql_password}@"
        f"{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
    )