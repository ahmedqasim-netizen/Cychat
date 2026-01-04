import redis.asyncio as aioredis
import os
from pathlib import (
    Path,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from tempfile import (
    gettempdir,
)
from urllib.parse import quote_plus

TEMP_DIR = Path(gettempdir())


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"
    REDIS_USERNAME: str = ""
    REDIS_PASSWORD: str = ""
    

    DB_TYPE: str = "sqlserver"  
    DB_HOST: str = "localhost\\SQLEXPRESS"
    DB_PORT: str = ""
    DB_USERNAME: str = ""
    DB_PASSWORD: str = ""
    DB_NAME: str = "ChatDB"
    DB_DRIVER: str = "ODBC Driver 17 for SQL Server"
    

    SINGLESTORE_HOST: str = ""
    SINGLESTORE_PORT: str = ""
    SINGLESTORE_USERNAME: str = ""
    SINGLESTORE_PASSWORD: str = ""
    SINGLESTORE_DATABASE: str = ""
    
    JWT_SECRET_KEY: str = "super-secret-key-change-in-production"
    DETA_PROJECT_KEY: str = ""
    DEBUG: str = "info"
    CORS_ORIGINS: str = ""
    PROMETHEUS_DIR: Path = TEMP_DIR / "prom"

    @property
    def db_url(self) -> str:

        db_name = "test" if self.DEBUG == "test" else self.DB_NAME


        if self.SINGLESTORE_HOST and not os.getenv("DB_TYPE"):
            return (
                "mysql+aiomysql://"
                + self.SINGLESTORE_USERNAME
                + ":"
                + self.SINGLESTORE_PASSWORD
                + "@"
                + self.SINGLESTORE_HOST
                + ":"
                + self.SINGLESTORE_PORT
                + "/"
                + (self.SINGLESTORE_DATABASE if self.DEBUG != "test" else "test")
            )

        if self.DB_TYPE == "sqlserver":

            driver = quote_plus(self.DB_DRIVER)
            

            if self.DB_USERNAME and self.DB_PASSWORD:

                connection_string = (
                    f"mssql+aioodbc://{self.DB_USERNAME}:{quote_plus(self.DB_PASSWORD)}"
                    f"@{self.DB_HOST}/{db_name}"
                    f"?driver={driver}&TrustServerCertificate=yes"
                )
            else:

                connection_string = (
                    f"mssql+aioodbc://@{self.DB_HOST}/{db_name}"
                    f"?driver={driver}&TrustServerCertificate=yes&Trusted_Connection=yes"
                )
            
            return connection_string
        else:

            return (
                f"mysql+aiomysql://{self.DB_USERNAME}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{db_name}"
            )

    @property
    def cors_origins(self) -> list[str]:

        return (
            [url.strip() for url in self.CORS_ORIGINS.split(",") if url]
            if self.CORS_ORIGINS
            else []
        )

    async def redis_conn(self):

        try:
            if self.REDIS_USERNAME and self.REDIS_PASSWORD:
                url = (
                    f"redis://{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}"
                    f"@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
                )
            else:
                url = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
            
            conn = aioredis.from_url(url, decode_responses=True)

            await conn.ping()
            return conn
        except Exception:

            from app.utils.memory_pubsub import InMemoryRedis
            return InMemoryRedis()


settings = Settings()


__all__ = ["settings"]
