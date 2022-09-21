from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProductAvailability:
    isAvailable: bool
    isAvailableInAccount: bool


@dataclass
class ProductWorksOn:
    Windows: bool
    Mac: bool
    Linux: bool


@dataclass
class ProductReleaseDate:
    date: datetime
    timezone_type: int
    timezone: str


@dataclass
class Product:
    isGalaxyCompatible: bool
    tags: list[any]
    id: int
    availability: ProductAvailability
    title: str
    image: str
    url: str
    worksOn: ProductWorksOn
    category: str
    rating: int
    isComingSoon: bool
    isMovie: bool
    isGame: bool
    slug: str
    updates: int
    isNew: bool
    dlcCount: int
    releaseDate: ProductReleaseDate
    isBaseProductMissing: bool
    isHidingDisabled: bool
    isInDevelopment: bool
    extraInfo: list[any]
    isHidden: bool
