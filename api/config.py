"""
Configuration settings for the extended API.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


# Attempt to load a repository-local .env file into os.environ early so that
# BaseSettings will pick up expected values even when the process current
# working directory differs (this happens in Codespaces / preview servers
# which may start uvicorn from a different CWD). This avoids falling back to
# unintended defaults such as root/no-password.
try:
    repo_root = Path(__file__).resolve().parents[1]
    env_path = repo_root / '.env'
    if env_path.exists():
        for raw in env_path.read_text(encoding='utf-8').splitlines():
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            # Do not overwrite existing environment variables set by the host
            if k not in os.environ:
                os.environ[k] = v
        # Helpful debug print during startup
        if 'MYSQL_USER' in os.environ:
            print(f"[ENV LOAD] Loaded .env from {env_path} MYSQL_USER={os.environ.get('MYSQL_USER')}")
except Exception:
    # Never crash app startup due to .env parsing issues
    pass


class Settings(BaseSettings):
    """Application settings."""
    
    # Database settings
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    # Use the docker-compose seeded user by default to avoid unauthenticated
    # connections as root. These can be overridden with environment variables.
    mysql_user: str = "hospital_user"
    mysql_password: str = "devpassword"
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

# Warn when running with the default root/no-password (catch common misconfigurations)
if settings.mysql_user == 'root' and not settings.mysql_password:
    print('[CONFIG WARNING] Using root with no password for MySQL connection - this is insecure and may fail in many environments')


def get_database_url() -> str:
    """Get database connection URL."""
    return (
        f"mysql+asyncmy://{settings.mysql_user}:{settings.mysql_password}@"
        f"{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
    )