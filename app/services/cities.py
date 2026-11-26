"""Exact city lookup in the bundled GeoNames cities15000 gazetteer."""
import csv
import gzip
import unicodedata
from functools import lru_cache
from pathlib import Path


def normalize(value: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(ch)).strip()


@lru_cache(maxsize=512)
def lookup_city(query: str) -> dict | None:
    name, *regions = [normalize(part) for part in query.split(",")]
    if not name:
        return None
    alias_match = None
    with gzip.open(Path(__file__).with_name("cities.csv.gz"), "rt", encoding="utf8", newline="") as source:
        for city, code, country, state_code, state, lat, lon, aliases in csv.reader(source):
            canonical = normalize(city) == name
            if not canonical and (alias_match or name not in aliases.casefold().split("|")):
                continue
            qualifiers = {normalize(part) for part in (code, country, state_code, state) if part}
            if code == "US":
                qualifiers.add("usa")
            if not all(region in qualifiers for region in regions if region):
                continue
            place = {"lat": float(lat), "lon": float(lon),
                     "display_name": ", ".join(filter(None, [city, state, country]))}
            if canonical:
                return place
            alias_match = place
    return alias_match
