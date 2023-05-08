import time
import sys
import re
from multiprocessing import Queue
from typing import List, Dict, Tuple
from pprint import pformat

from loguru import logger
import ujson
from slugify import slugify

from enums import Sex, JSONFieldNames


DUPLICATE_ENDING = "-([0-9]|r|p|R|P)$"
DUPLICATE_REGEX = re.compile(f"^.*{DUPLICATE_ENDING}")
NON_COLORED_CATEGORIES = (
    "Косметика",
    "Парфюмерия",
    "Парфюмерия без маркировки",
    "Парфюмерия с маркировкой",
    "Аксессуары",
    "Текстиль для дома",
    "Текстиль для дома #Маркировка",
)


class JsonParser:
    def __init__(
        self, 
        json_file: str,
        queue: Queue,
    ) -> None:
        self._json_file = json_file
        self._queue = queue
        self.loaded_prods: List[Dict]

        # id Уже найденных дубликатов
        self.seen_common_ids: List[str] = []

        logger.configure(handlers=[{"level": "INFO", "sink": sys.stdout}])

    def run(self) -> None:
        start = time.perf_counter()

        with open(self._json_file) as file:
            self.loaded_prods = ujson.load(file)

        logger.debug(f"Total json products quantity: {len(self.loaded_prods)}")

        for product in self.loaded_prods:
            # logger.debug(f"Processing product: {product}")
            parsed_prod = self.parse_product(product)
            if parsed_prod is None:
                continue

            prod_id = parsed_prod[JSONFieldNames.id.value]
            filtered_prod_id = self.filter_id(prod_id)
            # Если id товара попадает под вид дубликата 
            # и id товара до этого не встречался - ищем его дубликаты
            if (
                self.id_match_duplicate(prod_id) and
                filtered_prod_id not in self.seen_common_ids
            ):
                duplicates = self.find_duplicates(
                    filtered_id=filtered_prod_id,
                    products=self.loaded_prods,
                    skip_ids=[prod_id], # Пропустить id текущего товара
                )
                logger.debug(f"Found duplicates for {pformat(parsed_prod)}: {len(duplicates)} - {duplicates}")
                self.seen_common_ids.append(filtered_prod_id)

                found_leftovers = [dupl[JSONFieldNames.leftovers.value] for dupl in duplicates]
                found_leftovers.append(parsed_prod[JSONFieldNames.leftovers.value])
                total_leftovers = self._merge_leftovers(
                    found_leftovers, 
                    price=parsed_prod[JSONFieldNames.price.value]
                )
                parsed_prod[JSONFieldNames.leftovers.value] = total_leftovers
                parsed_prod[JSONFieldNames.id.value] = filtered_prod_id

            self._queue.put(parsed_prod)
        
        logger.info(f"Total parse time: {time.perf_counter() - start:.2f}")

    def parse_product(self, product: Dict) -> Dict | None:
        filtered_id = self.filter_id(product[JSONFieldNames.id.value])
        category_obj = self._get_category_object(product)
        sex_name = self._get_prod_sex(product)
        if sex_name is None:
            return
        price, discount_price = self._get_price_and_discount_price(
            price=product[JSONFieldNames.price.value],
            discount_price=product[JSONFieldNames.discount_price.value],
        )
        splitted = self._get_prod_color_and_color_code(product)
        if splitted is None:
            return
        
        color, color_code = splitted
        try:
            parsed_prod = {
                "title": product[JSONFieldNames.title.value],
                "sku": product[JSONFieldNames.id.value],
                "color": color,
                "color_code": color_code,
                "brand": self._get_brand_obj(
                    product=product,
                    color_code=color_code, 
                    color=color, 
                    sku=filtered_id,
                ),
                "sex": sex_name,
                "root_category": category_obj,
                "price": price,
                "discount_price": discount_price,
                "in_the_sale": product[JSONFieldNames.in_the_sale.value],
                "size_table_type": product[JSONFieldNames.size_table_type.value],
                "leftovers": product[JSONFieldNames.leftovers.value],
            }
            return parsed_prod
        except KeyError:
            # Не удалось прочитать какое-либо поле в json товара - объект пропускается
            logger.warning(f"Malformed product object {product}")
            return None
        
    def filter_id(self, id: str) -> str:
        """
        Удаляет окончания -1, -2, -r и т.д. если они есть
        """
        return re.sub(DUPLICATE_ENDING, "", id)
    
    def id_match_duplicate(self, id: str) -> bool:
        return True if re.fullmatch(DUPLICATE_REGEX, id) else False
    
    def find_duplicates(
            self, 
            filtered_id: str, 
            products: List[Dict],
            skip_ids: List[str] = [],
        ) -> List[Dict]:
        """
        Поочередно фильтрует id товаров из products и возвращает товары, чьи id совпали с filtered_id
        """
        res = []
        for product in products:
            product_id = product[JSONFieldNames.id.value]
            if product_id in skip_ids:
                continue
            if self.filter_id(product_id) == filtered_id:
                res.append(product)

        return res

    def _get_category_object(self, product: Dict) -> Dict:
        category_name = product[JSONFieldNames.root_category.value]
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
        """
        Возвращает объект бренда и slug, 
        состоящий из названия бренда, кода цвета, названия цвета и артикула
        """
        brand_name = product[JSONFieldNames.brand.value]

        return {
            "name": brand_name,
            "slug": slugify(
                f"{brand_name}+{color_code}+{color}+{sku}"
            ),
        }
    
    def _merge_leftovers(self, leftovers_lists: List, price: int) -> List[Dict]:
        # O(n)
        sizes_to_quantity = {}

        for leftover_list in leftovers_lists:
            for l_over in leftover_list:
                size = l_over[JSONFieldNames.size.value]
                quantity = l_over[JSONFieldNames.quantity.value]
                price = l_over[JSONFieldNames.price.value]

                if size not in sizes_to_quantity.keys():
                    sizes_to_quantity[size] = 0
                sizes_to_quantity[size] += quantity

        res = []
        for size, quantity in sizes_to_quantity.items():
            res.append(
                {
                    JSONFieldNames.size.value: size,
                    JSONFieldNames.quantity.value: quantity,
                    JSONFieldNames.price.value: price,
                }
            )
        return res
        
    def _get_prod_sex(self, product: Dict) -> str | None:
        """Возвращает название пола, соответствующего id в Enum"""
        try:
            sex_id = product[JSONFieldNames.sex.value].lower()
        except AttributeError:
            sex_id = ""
        try:
            return Sex(sex_id).name
        except ValueError:
            logger.warning(
                f"Product: {product}. \n\"{JSONFieldNames.sex.value}\" id is unknown"
            )
    
    def _get_prod_color_and_color_code(
        self, 
        product: Dict,
    ) -> Tuple[str, str] | None:
        """
        Возвращает название цвета, соответствующего id в в Enum. 
        Возвращает: (color, color_code) | None
        """
        if product[JSONFieldNames.root_category.value] in NON_COLORED_CATEGORIES:
            return ("", "")
        
        try:
            splitted_code_n_color = product[JSONFieldNames.color.value].split("/")
            return (splitted_code_n_color[1], splitted_code_n_color[0])
        except IndexError:
            logger.warning(f"Unknown color delimiter: {product}")
    
    def _get_price_and_discount_price(
        self, 
        price: int,
        discount_price: int,
    ) -> Tuple[int, int]:
        """
        Реализует логику присвоения цен товару. 
        Возваращает (price, discount_price)
        """
        if discount_price > 0 and discount_price < price:
            return (discount_price, discount_price)
        elif discount_price <= 0:
            return (price, 0)
        elif discount_price >= price:
            return (discount_price, 0)
