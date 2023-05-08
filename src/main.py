from multiprocessing import Process, Queue

from loguru import logger
from pymongo.collection import Collection

from settings import get_settings
from db import get_db
from json_parser import JsonParser


JSON_PATH = "../work.json"
PRODUCTS_COLLECTION = "products"


def main() -> None:
    settings = get_settings()
    db = get_db(settings)
    logger.debug(db)
    products_collection: Collection = db[PRODUCTS_COLLECTION]
    logger.debug(products_collection)
    queue = Queue()

    parser = JsonParser(json_file=JSON_PATH, queue=queue)    
    parser.run()

    got_products = 0

    while True:
        try:
            prod = queue.get(timeout=5)
            products_collection.insert_one(prod)
            got_products += 1
        except:
            logger.info(f"Successfully got products: {got_products}")
            break


if __name__ == "__main__":
    main()



