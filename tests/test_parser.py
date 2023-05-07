import pytest

from src.json_parser import JsonParser


def test_filter_id() -> None:
    parser = JsonParser(..., ...)

    assert parser.filter_id("ABC-1") == "ABC"
    assert parser.filter_id("ABC-DEF-r") == "ABC-DEF"
    assert parser.filter_id("ab12cd-34ef56.gh-78-3") == "ab12cd-34ef56.gh-78"

    assert parser.filter_id("ABC") == "ABC"
    assert parser.filter_id("ABC-DEF") == "ABC-DEF"
    assert parser.filter_id("57135-20619-123") == "57135-20619-123"
    assert parser.filter_id("qwerty.qwerty-qwerty") == "qwerty.qwerty-qwerty"


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
    price, disc_price = parser._get_price_and_discount_price(price=0, discount_price=0)
    assert price == 0 and disc_price == 0
