from unittest.mock import patch

from app.routers.osm import search_city


def test_common_cities_work_without_network():
    with patch("app.routers.osm.requests.get", side_effect=AssertionError("unexpected network request")):
        assert search_city("Orlando")["display_name"] == "Orlando, Florida, United States"
        assert search_city("Gainesville, FL")["display_name"] == "Gainesville, Florida, United States"
        assert search_city("Gainesville, Georgia")["display_name"] == "Gainesville, Georgia, United States"


def test_unknown_city_uses_geocoder():
    with patch("app.routers.osm.requests.get") as request:
        request.return_value.json.return_value = []
        assert search_city("Unlisted locality example") is None
        request.assert_called_once()
