from dataclasses import dataclass

from enums import Sex, Category, Country, BrandCode


@dataclass
class Brand:
    _code: BrandCode

    @property
    def name(self) -> str:
        return self._code.name
    
    @property
    def slug(self) -> str:
        return ...


@dataclass
class BaseProduct:
    """
    Базовый класс продукта. 
    Все продукты-наследники содержат его поля.
    """
    title: str
    category: Category
    vendor_code: str # Артикул
    brand: int
    sex: Sex
    fashion_season: str
    country: Country
    brand: Brand
    price: int
    discount_price: int
    in_the_sale: bool


@dataclass
class PerfumeProduct(BaseProduct):
    ...


@dataclass
class ClothingProduct(BaseProduct):
    material: str
    color: int
    color_code: str
