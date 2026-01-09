from functools import lru_cache

from pydantic import BaseModel, Field


class Settings(BaseModel):
    database_url: str = Field(..., alias="DATABASE_URL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.model_validate({})
