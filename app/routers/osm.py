import logging
from typing import Any

import requests
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()
log = logging.getLogger("osm_proxy")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_ENDPOINTS = (
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)
REQUEST_HEADERS = {
    "User-Agent": "GeoInsightDashboard/1.0 (+https://thegeodashboard.vercel.app)",
    "Accept": "application/json",
}
ALLOWED_AMENITIES = {
    "restaurant", "cafe", "bar", "fast_food", "pub", "cinema", "hospital",
    "clinic", "pharmacy", "dentist", "school", "university", "library", "bank",
    "atm", "shop", "mall", "supermarket", "gym", "parking", "fuel", "police",
    "fire_station", "hotel", "post_office", "bus_station",
}


class PolygonPoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class AmenitiesRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    amenities: list[str] = Field(min_length=1, max_length=len(ALLOWED_AMENITIES))
    radius: int = Field(ge=100, le=20_000)
    polygon: list[PolygonPoint] | None = Field(default=None, max_length=100)


@router.get("/cities")
def search_city(query: str = Query(min_length=2, max_length=200)) -> dict[str, Any] | None:
    """Resolve one city through Nominatim without browser CORS restrictions."""
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "jsonv2", "limit": 1},
            headers=REQUEST_HEADERS,
            timeout=12,
        )
        response.raise_for_status()
        results = response.json()
    except requests.RequestException as exc:
        log.warning("Nominatim request failed: %s", exc)
        raise HTTPException(status_code=502, detail="City search service is temporarily unavailable") from exc

    if not results:
        return None

    place = results[0]
    return {
        "lat": float(place["lat"]),
        "lon": float(place["lon"]),
        "display_name": place["display_name"],
    }


@router.post("/amenities")
def fetch_amenities(payload: AmenitiesRequest) -> dict[str, Any]:
    """Fetch a small, validated set of OSM amenities with a failover endpoint."""
    invalid_amenities = set(payload.amenities) - ALLOWED_AMENITIES
    if invalid_amenities:
        raise HTTPException(status_code=400, detail="Unsupported amenity category")

    special = {
        "shop": '["shop"]', "mall": '["shop"="mall"]', "supermarket": '["shop"="supermarket"]',
        "hotel": '["tourism"="hotel"]', "gym": '["leisure"="fitness_centre"]',
    }
    filters = [special[name] for name in payload.amenities if name in special]
    standard = sorted(set(payload.amenities) - special.keys())
    if len(standard) == 1:
        filters.append(f'["amenity"="{standard[0]}"]')
    elif standard:
        filters.append(f'["amenity"~"^({"|".join(standard)})$"]')
    if payload.polygon:
        if len(payload.polygon) < 3:
            raise HTTPException(status_code=400, detail="A search polygon needs at least three points")
        area = f'(poly:"{" ".join(f"{point.lat} {point.lng}" for point in payload.polygon)}")'
    else:
        area = f"(around:{payload.radius},{payload.lat},{payload.lon})"

    clauses = "".join(f"nwr{tag_filter}{area};" for tag_filter in filters)
    selection = clauses if len(filters) == 1 else f"({clauses});"
    overpass_query = f"[out:json][timeout:12];{selection}out center;"

    failures = []
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            payload_data = {"data": overpass_query}
            if len(overpass_query) > 1500:
                response = requests.post(endpoint, data=payload_data, headers=REQUEST_HEADERS, timeout=15)
            else:
                response = requests.get(endpoint, params=payload_data, headers=REQUEST_HEADERS, timeout=15)
            response.raise_for_status()
            result = response.json()
            if "remark" in result or not isinstance(result.get("elements"), list):
                raise ValueError("Incomplete Overpass response")
            return {"elements": result["elements"]}
        except (requests.RequestException, ValueError) as exc:
            failures.append(f"{endpoint}: {exc}")

    log.warning("All Overpass endpoints failed: %s", "; ".join(failures))
    raise HTTPException(status_code=502, detail="Map data service is temporarily unavailable")
