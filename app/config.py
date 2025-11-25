from pydantic import BaseSettings, AnyUrl


class Settings(BaseSettings):
    MONGODB_URI: AnyUrl = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "evalvia_docs"
    MONGODB_COLLECTION_NAME: str = "documents"

    class Config:
        env_file = ".env"


settings = Settings()
