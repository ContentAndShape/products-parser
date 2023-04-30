from threading import Thread
from typing import List, Dict, Tuple
from queue import Queue

from loguru import logger
import ujson
from slugify import slugify

from enums import Category, Sex, CODE_TO_COLOR, JSONFieldNames


class JsonParser:
    def __init__(self, json_file: str, max_threads: int, queue: Queue) -> None:
        self._json_file = json_file
        self._max_threads = max_threads
        self._queue = queue
        self._out_of_stock = 0

    def run(self) -> None:
        with open(self._json_file) as file:
            products = ujson.load(file)

        logger.debug(f"Total json products quantity: {len(products)}")
        slices = self._get_products_slices(products)

        threads: List[Thread] = []

        for slice in slices:
            thread = Thread(target=self._parse_slice, args=(slice,))
            threads.append(thread)

        logger.debug(f"Parsing {len(slices)} slices with {len(slices[0])} products each")
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        logger.info(f"Products out of stock: {self._out_of_stock}")

    def _get_products_slices(self, products_list: List[Dict]) -> List[List]:
        """Делит список товаров на подсписок для каждого потока"""
        prods_len = len(products_list)
        slices = [
            [products_list.pop() for _ in range(prods_len // self._max_threads)] for _ in range(self._max_threads)
        ]
        if len(products_list) == 1:
            slices[0].append(products_list[0])
        
        return slices

    def _parse_slice(self, slice: List[Dict]) -> None:
        """Парсит и публикует товары в очередь"""
        for prod in slice:
            logger.debug(f"Parsing prod: {prod}")
            parsed_prod = self._parse_product(prod)

            # В случае когда поступил новый неизвестный id 
            # которого нет в словарях. Или в полях товара присутствует ошибка
            if parsed_prod is None:
                continue

            self._queue.put(parsed_prod)
            logger.debug(f"Put prod: {parsed_prod}")

    def _parse_product(self, product: Dict) -> Dict | None:
        category_obj = self._get_category_object(product)

        if category_obj["name"] is None:
            logger.warning(f"Unknown product category: {product}")
            return
        
        # Проверка наличия товара в leftovers
        leftovers = []
        for prod in product[JSONFieldNames.leftovers.value]:
            if prod[JSONFieldNames.quantity.value] == 0:
                continue

            if category_obj["name"] != Category.perfumery.name:
                leftover_size = prod[JSONFieldNames.size.value]
            else:
                leftover_size = ""

            leftover = {
                "size": leftover_size,
                "quantity": prod[JSONFieldNames.quantity.value],
            }
            leftovers.append(leftover)

        if len(leftovers) == 0:
            logger.warning(f"Product is out of stock: {product}")
            self._out_of_stock += 1
            return
        
        sex_name = self._get_prod_sex(product)
        price, discount_price = self._get_price_and_discount_price(product)
        if category_obj["name"] != Category.perfumery.name:
            color, color_code = self._get_prod_color_and_color_code(product)
        else:
            color, color_code = "", ""
        
        # Под каждый размер из остатка создается отдельный объект товара, 
        # в объект также записывается оставшееся кол-во единиц товара
        for leftover in leftovers:
            try:
                parsed_prod = {
                    "title": product[JSONFieldNames.title.value],
                    "sku": product[JSONFieldNames.id.value], # TODO process id or maybe not
                    "color": color, # id цвета заменен на название
                    "color_code": color_code, # взята первая часть поля
                    "brand": self._get_brand_obj(
                        product=product, 
                        color_code=color_code, 
                        color=color, 
                        sku=product[JSONFieldNames.id.value],
                    ),
                    "sex": sex_name, # id пола заменен на название
                    "root_category": category_obj,
                    "price": price,
                    "discount_price": discount_price,
                    "in_the_sale": product[JSONFieldNames.in_the_sale.value],
                    "size_table_type": product[JSONFieldNames.size_table_type.value],
                    "size": leftover["size"],
                    "quantity": leftover["quantity"],
                }
                return parsed_prod
            except KeyError:
                # Не удалось прочитать какое-либо поле в json товара - объект пропускается
                logger.warning(f"Malformed product object {product}")
                return None


    def _get_category_object(self, product: Dict) -> Dict | None:
        """
        Возвращает объект категории. 
        Имя категории определяется по id в Enum
        """
        category_id = product[JSONFieldNames.category.value]

        try:
            category_name = Category(category_id).name
        except ValueError:
            logger.warning(
                f"Product: {product}. \n\"{JSONFieldNames.category.value}\" id is unknown"
            )
            return

        return {
            "name": category_name,
            "slug": slugify(category_name),
        }
    
    def _get_brand_obj(
        self, 
        product: Dict, 
        color_code: str, 
        color: str, 
        sku: str
    ) -> Dict | None:
        """Возвращает объект бренда. Именем бренда является его id"""
        brand_id = product[JSONFieldNames.brand.value]

        return {
            "name": brand_id,
            "slug": slugify(
                f"{brand_id}+{color_code}+{color}+{sku}"
            ),
        }
        
    def _get_prod_sex(self, product: Dict) -> str | None:
        """Возвращает название пола, соответствующего id в Enum"""
        sex_id = product[JSONFieldNames.sex.value]
        try:
            return Sex(sex_id).name
        except ValueError:
            logger.warning(
                f"Product: {product}. \n\"{JSONFieldNames.sex.value}\" id is unknown"
            )
    
    def _get_prod_color_and_color_code(
        self, 
        product: Dict
    ) -> Tuple[str, str] | None:
        """
        Возвращает название цвета, соответствующего id в в Enum. 
        Возвращает (color, color_code)
        """
        color_id = product[JSONFieldNames.color.value]
        color_code = product[JSONFieldNames.color_code.value].split("/")[0]
        try:
            return (CODE_TO_COLOR[color_id], color_code)
        except KeyError:
            logger.warning(
                f"Product: {product}. \n\"{JSONFieldNames.color.value}\" id is unknown"
            )
    
    def _get_price_and_discount_price(
        self, 
        product: Dict
    ) -> Tuple[int, int]:
        """
        Реализует логику присвоения цен товару. 
        Возваращает (price, discount_price)
        """
        price = product[JSONFieldNames.price.value]
        discount_price = product[JSONFieldNames.discount_price.value]

        if discount_price > 0 and discount_price <= price:
            return (discount_price, discount_price)
        else:
            return (price, 0)
