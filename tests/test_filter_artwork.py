"""Web/Flutter filter artwork uses the same resolved category metadata."""
import pytest


@pytest.mark.parametrize("category", ["clinics", "salons", "hotels", "restaurants"])
def test_filter_artwork_is_shared_and_assets_are_served(client, category):
    payload = client.get(f"/api/v1/locations/trichy/{category}").json
    page = client.get(f"/trichy/{category}")
    assert page.status_code == 200
    assert payload["api_version"] == "v1"
    assert b"filter-option-artwork" in page.data
    assert payload["filters"] == payload["category"]["filters"]
    urls = set()
    for field in payload["filters"]:
        items = [field["all_artwork"], field["artwork"]]
        items.extend(option["artwork"] for option in field.get("options", []))
        for art in items:
            assert art["url"].startswith("/static/images/filter-artwork/")
            assert 0 <= art["column"] < art["columns"]
            assert 0 <= art["row"] < art["rows"]
            urls.add(art["url"])
    for url in urls:
        asset = client.get(url)
        assert asset.status_code == 200
        assert asset.mimetype == "image/webp"
        assert asset.data[:4] == b"RIFF"


def test_anatomical_choices_and_existing_filter_values_are_consistent(client):
    payload = client.get("/api/v1/locations/trichy/clinics").json
    specialty = next(f for f in payload["filters"] if f["key"] == "specialty")
    options = {o["value"]: o for o in specialty["options"]}
    assert options["cardiology"]["artwork"] == {
        "url": "/static/images/filter-artwork/cardiology.webp",
        "columns": 1, "rows": 1, "column": 0, "row": 0,
    }
    assert options["gastro"]["artwork"]["column"] == 2
    assert options["gastro"]["artwork"]["row"] == 0
    assert options["nephrology"]["artwork"]["column"] == 2
    assert options["nephrology"]["artwork"]["row"] == 1
    assert options["gastro"]["image"] == "/static/images/filters/gastro.svg"
    bootstrap = client.get("/api/v1/bootstrap?city=trichy").json
    clinic = next(c for c in bootstrap["selected_location"]["categories"] if c["slug"] == "clinics")
    assert clinic["filters"] == payload["filters"]
    result = client.get("/api/v1/locations/trichy/clinics/businesses?specialty=cardiology").json
    assert result["applied_filters"]["specialty"] == "cardiology"
    assert result["total"] == 0  # No invented cardiology businesses in demo fixtures.
