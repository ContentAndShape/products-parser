import pytest
from slugify import slugify

from src.json_parser import JsonParser, NON_COLORED_CATEGORIES
from src.enums import Sex, JSONFieldNames as Field


def test_filter_id() -> None:
    """Удаление окончаний, свойственных товарам-дубликатам"""
    parser = JsonParser(..., ...)

    assert parser.filter_id("ABC-1") == "ABC"
    assert parser.filter_id("ABC-DEF-r") == "ABC-DEF"
    assert parser.filter_id("ab12cd-34ef56.gh-78-3") == "ab12cd-34ef56.gh-78"

    assert parser.filter_id("ABC") == "ABC"
    assert parser.filter_id("ABC-DEF") == "ABC-DEF"
    assert parser.filter_id("57135-20619-123") == "57135-20619-123"
    assert parser.filter_id("qwerty.qwerty-qwerty") == "qwerty.qwerty-qwerty"


def test_id_match_duplicate() -> None:
    parser = JsonParser(..., ...)

    assert parser.id_match_duplicate("ABCDE-1") is True
    assert parser.id_match_duplicate("ABC-r") is True
    assert parser.id_match_duplicate("ABCDE-") is False
    assert parser.id_match_duplicate("ABCDE-1-r") is True
    assert parser.id_match_duplicate("ABC-1r") is False
    assert parser.id_match_duplicate("ABCDE") is False
    assert parser.id_match_duplicate("ABC-DEF-G") is False
    assert parser.id_match_duplicate("-r") is True
    assert parser.id_match_duplicate("GWJTAZ-HU7IH") is False


def test_price_definition() -> None:
    """
    Если цена со скидкой > 0 то, price = discount_price Иначе price = price (discount_price установить на 0)
    если discount_price > price или price = discount_price, то цена
    обычная приравнивается к скидочной, discount_price
    устанавливаем 0
    """
    parser = JsonParser(..., ...)

    # Если disc_price > 0 и disc_price < price
    price, disc_price = parser._get_price_and_discount_price(price=100, discount_price=50)
    # TODO assert price == 100 and disc_price == 50

    # Если disc_price > 0 и disc_price > price
    price, disc_price = parser._get_price_and_discount_price(price=50, discount_price=100)
    # TODO assert price == 100 and disc_price == 0

    # Если disc_price < 0 и disc_price < price
    price, disc_price = parser._get_price_and_discount_price(price=100, discount_price=-100)
    assert price == 100 and disc_price == 0

    # Если disc_price = 0 и disc_price < price
    price, disc_price = parser._get_price_and_discount_price(price=100, discount_price=0)
    assert price == 100 and disc_price == 0

    # Если disc_price = price
    price, disc_price = parser._get_price_and_discount_price(price=100, discount_price=100)
    assert price == 100 and disc_price == 0


def test_sex_definition() -> None:
    parser = JsonParser(..., ...)

    p = {Field.sex.value: "У"}
    assert parser._get_prod_sex(p) == Sex.unisex.name

    p ={Field.sex.value: "М"}
    assert parser._get_prod_sex(p) == Sex.male.name

    p ={Field.sex.value: "Ж"}
    assert parser._get_prod_sex(p) == Sex.female.name

    p = {Field.sex.value: "qwerty"}
    assert parser._get_prod_sex(p) is None


def test_color_n_color_code_definition() -> None:
    parser = JsonParser(..., ...)

    for category in NON_COLORED_CATEGORIES:
        p = {
            Field.root_category.value: category,
            Field.color.value: "731/желтый",
        }
        color, color_code = parser._get_prod_color_and_color_code(p)
        assert color == "" and color_code == ""

    p = {
        Field.root_category.value: "any_colored_category",
        Field.color.value: "731/желтый",
    }
    color, color_code = parser._get_prod_color_and_color_code(p)
    assert color == "желтый" and color_code == "731"

    # Неизвестный разделитель между кодом и цветом
    p = {
        Field.root_category.value: "any_colored_category",
        Field.color.value: "731.желтый",
    }
    splitted = parser._get_prod_color_and_color_code(p)
    assert splitted is None


def test_get_category_object() -> None:
    parser = JsonParser(..., ...)

    p = {Field.root_category.value: "Category"}
    cat = parser._get_category_object(p)
    assert cat["name"] == "Category" and cat["slug"] == slugify("Category")


def test_get_brand_object() -> None:
    parser = JsonParser(..., ...)

    p = {Field.brand.value: "Brand"}
    color = "желтый"
    color_code = "731"
    sku = "qwerty"
    br = parser._get_brand_obj(p, color=color, color_code=color_code, sku=sku)
    assert br["name"] == "Brand"
    assert br["slug"] == slugify(f"{br['name']}+{color_code}+{color}+{sku}")


def test_unique_id() -> None:
    parser = JsonParser(..., ...)

    raw_id = "L012412-1"
    filtered_id = parser.filter_id(raw_id)
    raw_color = "BLACK/черный"

    assert parser._get_unique_id(filtered_id, raw_color) == filtered_id + raw_color


def test_find_duplicates() -> None:
    parser = JsonParser(..., ...)

    # Поиск последовательно идущих дубликатов с целевым id
    # Возвращаются только дубликаты, идущие непрерывно
    seq = [
        {
            Field.id.value: "ABC-R",
            Field.color.value: "",
        },
        {
            Field.id.value: "QWE", # <- должен вернуться
            Field.title.value: "duplicate_1",
            Field.color.value: "",
        },
        {
            Field.id.value: "QWE-2", # <- должен вернуться
            Field.title.value: "duplicate_2",
            Field.color.value: "",
        },
        {
            Field.id.value: "TYUI-OIITJ",
            Field.color.value: "",
        },
        {
            Field.id.value: "QWE-3", # <- не должен возвращаться, т.к. sequential=True
            Field.title.value: "duplicate_3",
            Field.color.value: "",
        }
    ]
    dups = parser.find_duplicates(filtered_id="QWE", products=seq, target_color="", sequential=True)
    assert seq[1] in dups
    assert seq[2] in dups

    # Товары с одинаковым id, идущие непрерывно, но у них разные цвета
    seq = [
        {
            Field.id.value: "ABC-R",
            Field.color.value: "",
        },
        {
            Field.id.value: "QWE", # <- Должен вернуться, т.к. совпадает целевой id и цвет
            Field.title.value: "duplicate_1",
            Field.color.value: "color_one",
        },
        {
            Field.id.value: "QWE-2", # <- Не должен возвращаться, т.к. совпадает целевой id, но цвет - нет
            Field.title.value: "",
            Field.color.value: "color_two",
        },
        {
            Field.id.value: "TYUI-OIITJ",
            Field.color.value: "",
        },
        {
            Field.id.value: "QWE-3", # <- Не должен возвращаться, т.к. sequential=True
            Field.title.value: "duplicate_3",
            Field.color.value: "color_one",
        }
    ]
    dups = parser.find_duplicates(filtered_id="QWE", products=seq, target_color="color_one", sequential=True)
    assert seq[1] in dups
    assert seq[2] not in dups
    assert seq[4] not in dups

    # Поиск всех дубликатов с целевым id
    # Возвращаются все дубликаты целевого id из массива
    seq = [
        {
            Field.id.value: "ABC-R",
            Field.color.value: "",
        },
        {
            Field.id.value: "QWE", # <- Должен вернуться
            Field.title.value: "duplicate_1",
            Field.color.value: "",
        },
        {
            Field.id.value: "QWE-R", # <- Должен вернуться
            Field.title.value: "duplicate_2",
            Field.color.value: "",
        },
        {
            Field.id.value: "TYUI-OIITJ",
            Field.color.value: "",
        },
        {
            Field.id.value: "QWE-3", # <- Должен вернуться, т.к. sequential=False
            Field.title.value: "duplicate_3",
            Field.color.value: "",
        }
    ]
    dups = parser.find_duplicates(filtered_id="QWE", products=seq, target_color="", sequential=False)
    assert seq[1] in dups
    assert seq[2] in dups
    assert seq[4] in dups

    # Товары с одинаковыми id и разными цветами не должны считаться дубликатами
    seq = [
        {
            Field.id.value: "ABC-R",
            Field.color.value: "",
        },
        {
            Field.id.value: "QWE", # <- Должен вернуться, т.к. id и цвет совпадает с целевым
            Field.title.value: "duplicate_1",
            Field.color.value: "unique",
        },
        {
            Field.id.value: "QWE-2", # <- Не должен возвращаться, т.к. id совпадает, но цвет не совпадает с целевым
            Field.title.value: "duplicate_2",
            Field.color.value: "",
        },
        {
            Field.id.value: "TYUI-OIITJ",
            Field.color.value: "",
        },
        {
            Field.id.value: "QWE-3", # <- Должен вернуться, т.к. sequential=True, id и цвет совпадает с целевым
            Field.title.value: "duplicate_3",
            Field.color.value: "unique",
        }
    ]
    dups = parser.find_duplicates(filtered_id="QWE", products=seq, target_color="unique", sequential=False)
    assert seq[1] in dups
    assert seq[4] in dups

    seq = [
        {
		"title": "сумка",
		"sku": "BB7337-AW576",
		"color": "80441/розовый",
		"brand": "Dolce&Gabbana",
		"sex": "Ж",
		"material": "100% кожа",
		"size_table_type": "Безразмерные",
		"root_category": "Сумки",
		"fashion_season": "2022-2",
		"fashion_collection": "Dolce&Gabbana Borse Donna FW 2022",
		"fashion_collection_inner": "Dolce&Gabbana Womens Handbags Fashion",
		"manufacture_country": "ИТАЛИЯ",
		"category": "сумка",
		"price": 67510,
		"discount_price": 67510,
		"in_the_sale": False,
		"leftovers": [
			{
				"size": "U",
				"count": 0,
				"price": 67510
			}
		]
	    },
	    {
	    	"title": "сумка",
	    	"sku": "BB7337-AW576",
	    	"color": "80999/черный",
	    	"brand": "Dolce&Gabbana",
	    	"sex": "Ж",
	    	"material": "100% кожа",
	    	"size_table_type": "Безразмерные",
	    	"root_category": "Сумки",
	    	"fashion_season": "2022-2",
	    	"fashion_collection": "Dolce&Gabbana Borse Donna FW 2022",
	    	"fashion_collection_inner": "Dolce&Gabbana Womens Handbags Fashion",
	    	"manufacture_country": "ИТАЛИЯ",
	    	"category": "сумка",
	    	"price": 67510,
	    	"discount_price": 67510,
	    	"in_the_sale": False,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 0,
	    			"price": 67510
	    		}
	    	]
	    },
	    {
	    	"title": "сумка",
	    	"sku": "BB7337-AW576-1",
	    	"color": "80002/белый",
	    	"brand": "Dolce&Gabbana",
	    	"sex": "Ж",
	    	"material": "100% кожа",
	    	"size_table_type": "Безразмерные",
	    	"root_category": "Сумки",
	    	"fashion_season": "2023-1",
	    	"fashion_collection": "Dolce&Gabbana Borse Donna SS 2023",
	    	"fashion_collection_inner": "Dolce&Gabbana Womens Handbags Precollection",
	    	"manufacture_country": "ИТАЛИЯ",
	    	"category": "сумка",
	    	"price": 73570,
	    	"discount_price": 73570,
	    	"in_the_sale": False,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 2,
	    			"price": 73570
	    		}
	    	]
	    },
	    {
	    	"title": "сумка",
	    	"sku": "BB7337-AW576-1",
	    	"color": "80441/циклин",
	    	"brand": "Dolce&Gabbana",
	    	"sex": "Ж",
	    	"material": "100% кожа",
	    	"size_table_type": "Безразмерные",
	    	"root_category": "Сумки",
	    	"fashion_season": "2023-1",
	    	"fashion_collection": "Dolce&Gabbana Borse Donna SS 2023",
	    	"fashion_collection_inner": "Dolce&Gabbana Womens Handbags Precollection",
	    	"manufacture_country": "ИТАЛИЯ",
	    	"category": "сумка",
	    	"price": 73570,
	    	"discount_price": 73570,
	    	"in_the_sale": False,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 1,
	    			"price": 73570
	    		}
	    	]
	    },
	    {
	    	"title": "сумка",
	    	"sku": "BB7337-AW576-1",
	    	"color": "80999/черный",
	    	"brand": "Dolce&Gabbana",
	    	"sex": "Ж",
	    	"material": "100% кожа",
	    	"size_table_type": "Безразмерные",
	    	"root_category": "Сумки",
	    	"fashion_season": "2023-1",
	    	"fashion_collection": "Dolce&Gabbana Borse Donna SS 2023",
	    	"fashion_collection_inner": "Dolce&Gabbana Womens Handbags Precollection",
	    	"manufacture_country": "ИТАЛИЯ",
	    	"category": "сумка",
	    	"price": 73570,
	    	"discount_price": 73570,
	    	"in_the_sale": False,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 1,
	    			"price": 73570
	    		}
	    	]
	    },
	    {
	    	"title": "сумка",
	    	"sku": "BB7337-AW576-1",
	    	"color": "8X052/красный",
	    	"brand": "Dolce&Gabbana",
	    	"sex": "Ж",
	    	"material": "100% кожа",
	    	"size_table_type": "Безразмерные",
	    	"root_category": "Сумки",
	    	"fashion_season": "2023-1",
	    	"fashion_collection": "Dolce&Gabbana Borse Donna SS 2023",
	    	"fashion_collection_inner": "Dolce&Gabbana Womens Handbags Precollection",
	    	"manufacture_country": "ИТАЛИЯ",
	    	"category": "сумка",
	    	"price": 73570,
	    	"discount_price": 73570,
	    	"in_the_sale": False,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 3,
	    			"price": 73570
	    		}
	    	]
	    },
    ]
    dups = parser.find_duplicates(filtered_id="BB7337-AW576", products=seq, target_color="80999/черный", sequential=True)
    assert len(dups) == 2
    dups = parser.find_duplicates(filtered_id="BB7337-AW576", products=seq, target_color="80999/черный", sequential=False)
    assert len(dups) == 2

    seq = [
        {
		"title": "сумка",
		"sku": "BB7337-AW576",
		"color": "80441/розовый",
		"brand": "Dolce&Gabbana",
		"sex": "Ж",
		"material": "100% кожа",
		"size_table_type": "Безразмерные",
		"root_category": "Сумки",
		"fashion_season": "2022-2",
		"fashion_collection": "Dolce&Gabbana Borse Donna FW 2022",
		"fashion_collection_inner": "Dolce&Gabbana Womens Handbags Fashion",
		"manufacture_country": "ИТАЛИЯ",
		"category": "сумка",
		"price": 67510,
		"discount_price": 67510,
		"in_the_sale": False,
		"leftovers": [
			{
				"size": "U",
				"count": 0,
				"price": 67510
			}
		]
	    },
	    {
	    	"title": "сумка",
	    	"sku": "BB7337-AW576",
	    	"color": "80999/черный",
	    	"brand": "Dolce&Gabbana",
	    	"sex": "Ж",
	    	"material": "100% кожа",
	    	"size_table_type": "Безразмерные",
	    	"root_category": "Сумки",
	    	"fashion_season": "2022-2",
	    	"fashion_collection": "Dolce&Gabbana Borse Donna FW 2022",
	    	"fashion_collection_inner": "Dolce&Gabbana Womens Handbags Fashion",
	    	"manufacture_country": "ИТАЛИЯ",
	    	"category": "сумка",
	    	"price": 67510,
	    	"discount_price": 67510,
	    	"in_the_sale": False,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 0,
	    			"price": 67510
	    		}
	    	]
	    },
	    {
	    	"title": "сумка",
	    	"sku": "BB7337-AW576-1",
	    	"color": "80002/белый",
	    	"brand": "Dolce&Gabbana",
	    	"sex": "Ж",
	    	"material": "100% кожа",
	    	"size_table_type": "Безразмерные",
	    	"root_category": "Сумки",
	    	"fashion_season": "2023-1",
	    	"fashion_collection": "Dolce&Gabbana Borse Donna SS 2023",
	    	"fashion_collection_inner": "Dolce&Gabbana Womens Handbags Precollection",
	    	"manufacture_country": "ИТАЛИЯ",
	    	"category": "сумка",
	    	"price": 73570,
	    	"discount_price": 73570,
	    	"in_the_sale": False,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 2,
	    			"price": 73570
	    		}
	    	]
	    },
	    {
	    	"title": "сумка",
	    	"sku": "BB7337-AW576-1",
	    	"color": "80441/циклин",
	    	"brand": "Dolce&Gabbana",
	    	"sex": "Ж",
	    	"material": "100% кожа",
	    	"size_table_type": "Безразмерные",
	    	"root_category": "Сумки",
	    	"fashion_season": "2023-1",
	    	"fashion_collection": "Dolce&Gabbana Borse Donna SS 2023",
	    	"fashion_collection_inner": "Dolce&Gabbana Womens Handbags Precollection",
	    	"manufacture_country": "ИТАЛИЯ",
	    	"category": "сумка",
	    	"price": 73570,
	    	"discount_price": 73570,
	    	"in_the_sale": False,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 1,
	    			"price": 73570
	    		}
	    	]
	    },
        {
            "sku": "non-common",
            "color": "80441/циклин",
        },
	    {
	    	"title": "сумка",
	    	"sku": "BB7337-AW576-1",
	    	"color": "80999/черный",
	    	"brand": "Dolce&Gabbana",
	    	"sex": "Ж",
	    	"material": "100% кожа",
	    	"size_table_type": "Безразмерные",
	    	"root_category": "Сумки",
	    	"fashion_season": "2023-1",
	    	"fashion_collection": "Dolce&Gabbana Borse Donna SS 2023",
	    	"fashion_collection_inner": "Dolce&Gabbana Womens Handbags Precollection",
	    	"manufacture_country": "ИТАЛИЯ",
	    	"category": "сумка",
	    	"price": 73570,
	    	"discount_price": 73570,
	    	"in_the_sale": False,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 1,
	    			"price": 73570
	    		}
	    	]
	    },
	    {
	    	"title": "сумка",
	    	"sku": "BB7337-AW576-1",
	    	"color": "8X052/красный",
	    	"brand": "Dolce&Gabbana",
	    	"sex": "Ж",
	    	"material": "100% кожа",
	    	"size_table_type": "Безразмерные",
	    	"root_category": "Сумки",
	    	"fashion_season": "2023-1",
	    	"fashion_collection": "Dolce&Gabbana Borse Donna SS 2023",
	    	"fashion_collection_inner": "Dolce&Gabbana Womens Handbags Precollection",
	    	"manufacture_country": "ИТАЛИЯ",
	    	"category": "сумка",
	    	"price": 73570,
	    	"discount_price": 73570,
	    	"in_the_sale": False,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 3,
	    			"price": 73570
	    		}
	    	]
	    },
    ]
    dups = parser.find_duplicates(filtered_id="BB7337-AW576", products=seq, target_color="80999/черный", sequential=True)
    assert len(dups) == 1


def test_merge_leftovers() -> None:
    parser = JsonParser(..., ...)

    l_1 = [
        {
			"size": "L",
			"count": 1,
			"price": 8650
		},
		{
			"size": "M",
			"count": 0,
			"price": 8650
		},
		{
			"size": "S",
			"count": 1,
			"price": 8650
		}
    ]
    l_2 = [
        {
            "size": "M",
            "count": 5,
            "price": 8650,
        },
        {
            "size": "XL",
            "count": 1,
            "price": 8650,
        },
    ]
    l_3 = [
        {
            "size": "S",
            "count": 2,
            "price": 8650,
        }
    ]
    
    for l_over in parser._merge_leftovers(leftovers_lists=[l_1, l_2, l_3], price=8650):
        quantity = l_over[Field.quantity.value]
        match l_over[Field.size.value]:
            case "S":
                assert quantity == 3
            case "M":
                assert quantity == 5
            case "L":
                assert quantity == 1
            case "XL":
                assert quantity == 1

    l_1 = []
    l_2 = [
        {
            "size": "S",
            "count": 1,
            "price": 8650,
        }
    ]

    for l_over in parser._merge_leftovers(leftovers_lists=[l_1, l_2], price=8650):
        quantity = l_over[Field.quantity.value]
        match l_over[Field.size.value]:
            case "S":
                assert quantity == 1


def test_product_consolidation() -> None:
    """Тест слияния дубликатов и их остатков в один объект"""
    parser = JsonParser(..., ...)
    
    p = [
        {
	    	"title": "Ёлочная игрушка",
	    	"sku": "L24337-1",
            "color": "",
            "color_code": "",
	    	"price": 3840,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 1,
	    			"price": 3840
	    		}
	    	]
	    },
	    {
	    	"title": "Ёлочная игрушка",
	    	"sku": "L24337-2",
            "color": "",
            "color_code": "",
	    	"price": 3840,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 1,
	    			"price": 3840
	    		}
	    	]
	    },
        {
	    	"title": "ремень",
	    	"sku": "E3-N68-11-25-01",
            "color": "",
            "color_code": "",
	    	"leftovers": [
	    		{
	    			"size": "L",
	    			"count": 1,
	    			"price": 8650
	    		},
	    		{
	    			"size": "M",
	    			"count": 0,
	    			"price": 8650
	    		},
	    		{
	    			"size": "S",
	    			"count": 1,
	    			"price": 8650
	    		}
	    	]
	    },
        {
	    	"title": "Ёлочная игрушка ",
	    	"sku": "03449",
            "color": "",
            "color_code": "",
	    	"price": 550,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 0,
	    			"price": 550
	    		}
	    	]
	    },
	    {
	    	"title": "Ёлочная игрушка",
	    	"sku": "L24337-3",
            "color": "",
            "color_code": "",
	    	"price": 3840,
	    	"leftovers": [
	    		{
	    			"size": "U",
	    			"count": 0,
	    			"price": 3840
	    		}
	    	]
	    },
	    {
	    	"title": "джинсы",
	    	"sku": "LDM550005",
            "color": "",
            "color_code": "",
	    	"price": 17840,
	    	"leftovers": [
	    		{
	    			"size": "33",
	    			"count": 0,
	    			"price": 7440
	    		},
	    		{
	    			"size": "34",
	    			"count": 0,
	    			"price": 7440
	    		},
	    		{
	    			"size": "36",
	    			"count": 1,
	    			"price": 7440
	    		}
	    	]
	    },
	    {
	    	"title": "джинсы",
	    	"sku": "LDM550005-1",
            "color": "",
            "color_code": "",
	    	"price": 19980,
	    	"leftovers": [
	    		{
	    			"size": "32",
	    			"count": 0,
	    			"price": 10410
	    		},
	    		{
	    			"size": "33",
	    			"count": 0,
	    			"price": 10410
	    		},
	    		{
	    			"size": "34",
	    			"count": 1,
	    			"price": 10410
	    		},
	    		{
	    			"size": "36",
	    			"count": 0,
	    			"price": 10410
	    		}
	    	]
	    },
	    {
	    	"title": "джинсы",
	    	"sku": "FAF8892",
            "color": "",
            "color_code": "",
	    	"price": 59260,
	    	"leftovers": [
	    		{
	    			"size": "36",
	    			"count": 0,
	    			"price": 34570
	    		},
                {
                    "size": "37",
                    "count": 0,
                    "price": 34570,
                },
                {
                    "size": "39",
                    "count": 2,
                    "price": 34570,
                },
	    	]
	    },
	    {
	    	"title": "джинсы",
	    	"sku": "FAF8892-2",
            "color": "",
            "color_code": "",
	    	"price": 49380,
	    	"leftovers": [
	    		{
	    			"size": "33",
	    			"count": 1,
	    			"price": 49380
	    		},
	    		{
	    			"size": "34",
	    			"count": 0,
	    			"price": 49380
	    		},
	    		{
	    			"size": "38",
	    			"count": 1,
	    			"price": 49380
	    		}
	    	]
	    }
    ]
    parser.loaded_prods = p

    # Ёлочная игрушка L24337
    target = p[0]
    prod = parser.consolidate_product(product=target, raw_color="", start_idx=0)
    prod_leftovers = prod[Field.leftovers.value]
    assert prod_leftovers[0][Field.quantity.value] == 2

    # Джинсы FAF8892
    target = p[-2]
    prod = parser.consolidate_product(product=target, raw_color="", start_idx=-2)
    prod_leftovers = prod[Field.leftovers.value]
    for leftover in prod_leftovers:
        quantity = leftover[Field.quantity.value]
        match leftover[Field.size.value]:
            case "33":
                assert quantity == 1
            case "34":
                assert quantity == 0
            case "36":
                assert quantity == 0
            case "37":
                assert quantity == 0
            case "38":
                assert quantity == 1
            case "39":
                assert quantity == 2
