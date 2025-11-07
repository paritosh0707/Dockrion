from pydantic import BaseSettings

class Settings(BaseSettings):
    langfuse_public: str | None = None
    langfuse_secret: str | None = None
    api_key: str | None = None

settings = Settings()
