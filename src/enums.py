from enum import Enum


class JSONFieldNames(Enum):
    """
    Маппинг программных названий полей товара к реальным из JSON. 
    На случай если названия полей в JSON будут меняться их можно будет 
    отредактировать здесь
    """
    title = "title"
    id = "sku"
    category = "root_category"
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


class Colors(Enum):
    black = "black"
    red = "red"
    white = "white"
    grey = "grey"
    green = "green"
    yellow = "yellow"
    orange = "orange"
    pink = "pink"
    blue = "blue"
    violet = "violet"
    beige = "beige"
    brown = "brown"
    multicolor = "multicolor"


# Маппинг кода цвета к имени
CODE_TO_COLOR = {
    32222: Colors.black.value, # Черный
    32829: Colors.black.value, # Графитовый
    33317: Colors.red.value, # Красный
    32228: Colors.red.value, # красный
    32395: Colors.red.value, # корал
    32226: Colors.red.value, # Бордо
    32337: Colors.red.value, # Бордовый
    33140: Colors.red.value, # бардовый ???
    32227: Colors.white.value, # Белый
    32235: Colors.white.value, # Молочный
    32254: Colors.white.value, # черно-белый
    32223: Colors.grey.value, # Серый
    32224: Colors.grey.value, # Темно-серый
    32325: Colors.grey.value, # бежево-серый
    32475: Colors.grey.value, # черно-серый
    32231: Colors.brown.value, # Коричневый
    32312: Colors.brown.value, # Светло-коричневый
    32245: Colors.brown.value, # темно-коричневый
    33517: Colors.brown.value, # Кумин
    32242: Colors.grey.value, # Светло-серый
    32225: Colors.green.value, # Зеленый
    32232: Colors.green.value, # светло-зеленый
    32272: Colors.green.value, # Мятный
    32309: Colors.green.value, # Оливковый
    32310: Colors.green.value, # Милитари
    32253: Colors.green.value, # Хаки
    33415: Colors.green.value, # Темно-хаки
    33061: Colors.green.value, # камуфляж
    32349: Colors.green.value, # черно-зеленый
    32333: Colors.green.value, # темно-зеленый
    32248: Colors.yellow.value, # Желтый
    32261: Colors.yellow.value, # Песочный
    32233: Colors.yellow.value, # Лимонный
    32317: Colors.yellow.value, # светло-желтый
    32260: Colors.yellow.value, # Золотой
    33311: Colors.orange.value, # Оранжевый
    32241: Colors.orange.value, # оранжевый
    32356: Colors.orange.value, # Персиковый
    32297: Colors.orange.value, # Охра
    32240: Colors.pink.value, # Розовый
    32273: Colors.pink.value, # Бледно-розовый
    32221: Colors.blue.value, # Синий
    33308: Colors.blue.value, # Синий
    32236: Colors.blue.value, # Темно-синий
    32255: Colors.blue.value, # Бирюзовый
    32229: Colors.blue.value, # голубой
    33309: Colors.blue.value, # Голубой
    32239: Colors.blue.value, # Бело-синий
    32298: Colors.blue.value, # туркез
    32427: Colors.blue.value, # Лаванда
    33462: Colors.blue.value, # Лазурный
    32321: Colors.violet.value, # Фиолетовый
    33514: Colors.violet.value, # Циклин
    32230: Colors.beige.value, # Бежевый
    32264: Colors.multicolor.value, # Мультиколор
}

# Маппинг id товара из json к желаемым именам в БД


class Sex(Enum):
    male = 235
    female = 236
    unisex = 240


class Category(Enum):
    perfumery = 23177
    clothing = 23144
    shoes = 23125
    hats = 23093
    bags = 23179


class Country(Enum):
    ...


class BrandCode(Enum):
    ...
