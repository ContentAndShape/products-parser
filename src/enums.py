from enum import Enum


class JSONFieldNames(Enum):
    """
    Маппинг программных названий полей товара к реальным из JSON. 
    На случай если названия полей в JSON будут меняться их можно будет 
    отредактировать здесь
    """
    title = "title"
    id = "sku"
    root_category = "root_category"
    sex = "sex"
    color = "color"
    color_code = "color_code"
    brand = "brand"
    price = "price"
    discount_price = "discount_price"
    size_table_type = "size_table_type"
    in_the_sale = "in_the_sale"
    leftovers = "leftovers"
    # leftovers objects
    quantity = "count"
    size = "size"


# Маппинг id товара из json к желаемым именам в БД


class Sex(Enum):
    male = "м"
    female = "ж"
    unisex = "у"


class Category(Enum):
    perfumery = "Парфюмерия"
