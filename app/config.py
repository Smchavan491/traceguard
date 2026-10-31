from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_user: str = "traceguard"
    postgres_password: str = "traceguard"
    postgres_db: str = "traceguard"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    runbook_chunk_size: int = Field(default=500, ge=1)
    runbook_chunk_overlap: int = Field(default=80, ge=0)
    rag_top_k: int = Field(default=4, ge=1)
    # Reserved for Part 3b; Part 3a records scores without applying a threshold.
    rag_min_score: float | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
