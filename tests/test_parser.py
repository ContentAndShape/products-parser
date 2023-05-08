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
    assert price == 50 and disc_price == 50

    # Если disc_price > 0 и disc_price > price
    price, disc_price = parser._get_price_and_discount_price(price=50, discount_price=100)
    assert price == 100 and disc_price == 0

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


def test_find_duplicates() -> None:
    parser = JsonParser(..., ...)

    # Поиск последовательно идущих дубликатов с целевым id
    # Возвращаются только дубликаты, идущие непрерывно
    seq = [
        {
            Field.id.value: "ABC-R",
        },
        {
            Field.id.value: "QWE",
            Field.title.value: "duplicate_1",
        },
        {
            Field.id.value: "QWE-2",
            Field.title.value: "duplicate_2",
        },
        {
            Field.id.value: "TYUI-OIITJ",
        },
        {
            Field.id.value: "QWE-3",
            Field.title.value: "duplicate_3",
        }
    ]
    dups = parser.find_duplicates(target_id="QWE", products=seq, sequential=True)
    assert seq[1] in dups
    assert seq[2] in dups

    # Поиск всех дубликатов с целевым id
    # Возвращаются все дубликаты целевого id из массива
    seq = [
        {
            Field.id.value: "ABC-R",
        },
        {
            Field.id.value: "QWE",
            Field.title.value: "duplicate_1",
        },
        {
            Field.id.value: "QWE-R",
            Field.title.value: "duplicate_2",
        },
        {
            Field.id.value: "TYUI-OIITJ",
        },
        {
            Field.id.value: "QWE-3",
            Field.title.value: "duplicate_3",
        }
    ]
    dups = parser.find_duplicates(target_id="QWE", products=seq, sequential=False)
    assert seq[1] in dups
    assert seq[2] in dups
    assert seq[4] in dups


def test_merge_leftovers_into_product() -> None:
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
    prod = parser.consolidate_product(product=target, start_idx=0)
    prod_leftovers = prod[Field.leftovers.value]
    assert prod_leftovers[0][Field.quantity.value] == 2

    # Джинсы FAF8892
    target = p[-2]
    prod = parser.consolidate_product(product=target, start_idx=-2)
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
