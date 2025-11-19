from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb+srv://infozodex_db:%40Zodex0@zodex.h0qhx59.mongodb.net/satkamatka?retryWrites=true&w=majority"
    JWT_SECRET: str = "changeme-please-set-in-env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60*24*7

    class Config:
        env_file = ".env"

settings = Settings()
