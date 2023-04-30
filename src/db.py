from pymongo import MongoClient

from settings import Settings


def get_db(settings: Settings) -> None:
    client = MongoClient(settings.conn_str)
    return client[settings._db_name]