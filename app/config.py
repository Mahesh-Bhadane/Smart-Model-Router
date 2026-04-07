# config.py — Load settings from your .env file
#
# WHAT IS THIS?
# pydantic-settings reads your .env file and puts each value into
# a typed Python variable. If a required variable is missing, it
# will raise a clear error at startup instead of crashing later.

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI — used for complex prompts (GPT-4o)
    openai_api_key: str

    # Groq — used for simple and medium prompts (free, fast Llama 3 models)
    groq_api_key: str

    # PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "smart_router_db"
    db_user: str = "postgres"
    db_password: str = ""

    class Config:
        env_file = ".env"          # Load from .env file in project root
        env_file_encoding = "utf-8"


# Create a single shared instance — import this everywhere
# e.g.  from app.config import settings
#        print(settings.openai_api_key)
settings = Settings()
