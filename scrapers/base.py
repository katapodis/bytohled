from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Listing:
    external_id: str
    source: str
    url: str
    title: str
    price: int | None
    price_type: Literal["sale", "rent"]
    disposition: str | None
    area_m2: int | None
    address: str | None
    description: str | None
    images: list[str] = field(default_factory=list)


class BaseScraper:
    def fetch_listings(self) -> list[Listing]:
        raise NotImplementedError
