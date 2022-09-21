from dataclasses import dataclass
from typing import Optional

from minigalaxy.galaxy.product import Product
from minigalaxy.galaxy.tag import Tag


@dataclass
class FilterProductsAppliedFilters:
    tags: Optional[list[any]]


@dataclass
class FilterProductsResponse:
    sortBy: any
    page: int
    totalProducts: int
    totalPages: int
    productsPerPage: int
    contentSystemCompatibility: any
    moviesCount: int
    tags: list[Tag]
    products: list[Product]
    updatedProductsCount: int
    hiddenUpdatedProductsCount: int
    appliedFilters: FilterProductsAppliedFilters
    hasHiddenProducts: bool
