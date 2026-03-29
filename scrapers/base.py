from dataclasses import dataclass, field
from typing import Literal


KNOWN_CITIES = [
    "Ostrava",
    "Frýdek-Místek",
    "Čeladná",
    "Ostravice",
    "Frýdlant nad Ostravicí",
    "Pstruží",
    "Metylovice",
    "Kunčice pod Ondřejníkem",
    "Baška",
    "Staré Hamry",
]


def extract_city(address: str | None) -> str | None:
    if not address:
        return None
    address_lower = address.lower()
    for city in KNOWN_CITIES:
        if city.lower() in address_lower:
            return city
    return None


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
    city: str | None = None


class BaseScraper:
    def fetch_listings(self) -> list[Listing]:
        raise NotImplementedError
