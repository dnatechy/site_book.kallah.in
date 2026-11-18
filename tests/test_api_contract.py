def test_flutter_bootstrap_contains_shared_app_configuration(client):
    response = client.get("/api/v1/bootstrap?city=trichy")
    assert response.status_code == 200
    payload = response.json
    assert payload["api_version"] == "v1"
    assert payload["site"]["name"] == "KALLAH Book"
    assert payload["pages"]["home"]["hero"]["title"] == "Book ahead."
    assert payload["pages"]["navigation"][0]["label"] == "Services"
    assert payload["theme"]["colors"]["primary"] == "#E53935"
    assert payload["booking"]["timezone"] == "Asia/Kolkata"
    assert payload["locations"]
    assert payload["selected_location"]["city"]["slug"] == "trichy"
    assert {item["slug"] for item in payload["selected_location"]["categories"]} == {
        "clinics", "salons", "hotels", "restaurants"
    }


def test_json_page_content_endpoint(client):
    response = client.get("/api/v1/config/pages")
    assert response.status_code == 200
    assert response.json["pages"]["location_picker"]["title"] == "Choose your district"


def test_category_business_search_pagination_and_filters(client):
    category = client.get("/api/v1/locations/trichy/clinics")
    assert category.status_code == 200
    assert category.json["category"]["slug"] == "clinics"
    assert category.json["filters"]
    assert category.json["theme"]["colors"]["primary"]

    response = client.get(
        "/api/v1/locations/trichy/clinics/businesses"
        "?specialty=dermatology&page=1&per_page=5&sort=rating_desc"
    )
    assert response.status_code == 200
    assert len(response.json["businesses"]) <= 5
    assert response.json["pagination"]["page"] == 1
    assert response.json["pagination"]["per_page"] == 5
    assert response.json["total"] >= len(response.json["businesses"])
    assert response.json["applied_filters"]["specialty"] == "dermatology"


def test_near_me_requires_coordinates_and_returns_distance(client):
    missing = client.get("/api/v1/locations/trichy/clinics/businesses?near-me=1")
    assert missing.status_code == 400
    assert missing.is_json
    response = client.get(
        "/api/v1/locations/trichy/clinics/businesses"
        "?near-me=1&lat=10.7905&lng=78.7047&radius_km=20"
    )
    assert response.status_code == 200
    assert all(item["distance_km"] is not None for item in response.json["businesses"])


def test_professional_profile_and_availability_api(client):
    base = (
        "/api/v1/locations/trichy/clinics/businesses/demo-clinic-01/"
        "professionals/demo-clinics-person-01"
    )
    profile = client.get(base)
    assert profile.status_code == 200
    assert profile.json["professional"]["name"] == "Dr. Kavitha Subramanian"
    assert profile.json["services"]
    assert profile.json["availability_url"].endswith("/availability")

    availability = client.get(base + "/availability?venue=demo-clinic-01&days=7")
    assert availability.status_code == 200
    payload = availability.json["availability"]
    assert len(payload["days"]) == 7
    assert payload["timezone"] == "Asia/Kolkata"
    assert payload["service"]["id"] == "consultation"
    assert payload["capacity_is_live"] is False
    assert payload["booking_is_persistent"] is False
