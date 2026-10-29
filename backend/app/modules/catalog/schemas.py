from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.config import get_settings


class ProductSort(StrEnum):
    DEFAULT = "default"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    RATING_ASC = "rating_asc"
    RATING_DESC = "rating_desc"


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    map_url: str


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str
    price: Decimal
    average_rating: Decimal | None
    category: CategoryOut | None
    locations: list[LocationOut]
    image_path: str = Field(validation_alias="image_url", exclude=True)

    @computed_field
    @property
    def image_url(self) -> str:
        return f"{get_settings().media_url}/products/{self.image_path}"


class ProductPage(BaseModel):
    items: list[ProductOut]
    page: int
    page_size: int
    total: int
    total_pages: int
