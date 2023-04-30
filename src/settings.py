import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    _db_user: str = os.getenv("DB_USERNAME")
    _db_pass: str = os.getenv("DB_PASSWORD")
    _db_name: str = os.getenv("DB_NAME")

    @property
    def conn_str(self) -> str:
        return f"mongodb://{self._db_user}:{self._db_pass}@127.0.0.1/{self._db_name}?authSource=admin"

def get_settings() -> Settings:
    return Settings()