from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LIINE_",
        extra="ignore",
    )

    app_env: str = Field(default="dev")
    database_url: str = Field(default="sqlite:////data/restaurants.db")
    test_database_url: str = Field(default="sqlite:////tmp/liine-test.db")
    csv_path: Path = Field(default=Path("/app/restaurants.csv"))
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")

    def database_url_for(self, *, test: bool = False) -> str:
        return self.test_database_url if test else self.database_url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
