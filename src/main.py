from loguru import logger
from queue import Queue
from pymongo.collection import Collection

from settings import get_settings
from db import get_db
from json_parser import JsonParser


JSON_PATH = "../test.json"
PRODUCTS_COLLECTION = "products"


def main() -> None:
    """
    Парсит json-файл в N потоках, 
    отправляет сформированные объекты в очередь. 
    Объкты из очереди в БД пишет главный поток.
    """
    settings = get_settings()
    db = get_db(settings)
    logger.debug(db)
    products_collection: Collection = db[PRODUCTS_COLLECTION]
    logger.debug(products_collection)
    queue = Queue()

    parser = JsonParser(json_file=JSON_PATH, max_threads=4, queue=queue)    
    parser.run()

    got_products = 0

    while True:
        try:
            try:
                prod = queue.get(timeout=10)
                products_collection.insert_one(prod)
                got_products += 1
            except:
                logger.info(f"Successfully got products: {got_products}")
                break
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()



