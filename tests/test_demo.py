"""Demo fixture, professional visibility, and API parity contracts."""
import json
import shutil

from app import content


CATEGORIES = ("clinics", "salons", "hotels", "restaurants")
PROFESSIONALS_PER_BUSINESS = {
    "clinics": 3,
    "salons": 3,
    "hotels": 0,
    "restaurants": 0,
}


def test_each_category_has_ten_demo_businesses_and_json_professionals(client):
    for category in CATEGORIES:
        businesses = content.get_businesses("trichy", category)
        assert len(businesses) == 10, (category, len(businesses))
        assert all(row["is_demo"] is True for row in businesses)
        assert len({row["slug"] for row in businesses}) == 10
        expected = PROFESSIONALS_PER_BUSINESS[category]
        assert sum(len(row["professionals"]) for row in businesses) >= expected * 10
        for business in businesses:
            assert business["demo_rating"] >= 3.5
            if category == "restaurants":
                assert business["booking_type"] == "dining"
                assert business["rating_label"] == "Guest rating"
                assert business["dining"]["menu"]
                assert business["dining"]["seating_options"]
            else:
                assert business["rating_value"] == business["demo_rating"]
                assert business["rating_label"] == "Demo score"
            if category == "hotels":
                assert business["booking_type"] == "rooms"
                assert business["rooms"]
            assert business["photo_url"].startswith("/static/images/")
            assert len(business["professionals"]) >= expected
            assert all(person["photo_url"].startswith("/static/images/")
                       for person in business["professionals"])


def test_business_to_professional_to_schedule_api_flow(client):
    business_page = client.get("/trichy/clinics/demo-clinic-01")
    assert business_page.status_code == 200
    assert b"Choose your doctor" in business_page.data
    assert b"Open profile, reviews &amp; book" in business_page.data

    people = client.get(
        "/api/v1/locations/trichy/clinics/businesses/demo-clinic-01/professionals"
    )
    assert people.status_code == 200
    assert len(people.json["professionals"]) >= 3

    person_id = "demo-clinics-person-01"
    profile_path = f"/trichy/clinics/demo-clinic-01/{person_id}"
    profile = client.get(profile_path)
    assert profile.status_code == 200
    for marker in (
        b"Schedule &amp; availability",
        b"Weekly visiting hours",
        b"booking-date-strip",
        b"service-menu-list",
        b"session-bars-container",
        b"Book appointment",
        b"demo-booking-data",
    ):
        assert marker in profile.data

    api_path = (
        "/api/v1/locations/trichy/clinics/businesses/demo-clinic-01/"
        f"professionals/{person_id}"
    )
    detail = client.get(api_path)
    assert detail.status_code == 200
    assert detail.json["professional"]["name"] == "Dr. Kavitha Subramanian"
    assert detail.json["services"]
    availability = client.get(api_path + "/availability?venue=demo-clinic-01&days=7")
    assert availability.status_code == 200
    assert len(availability.json["availability"]["days"]) == 7
    assert availability.json["availability"]["capacity_is_live"] is False
    assert availability.json["availability"]["booking_is_persistent"] is False


def test_demo_bookings_history_page_is_visible(client):
    response = client.get("/demo-bookings")
    assert response.status_code == 200
    assert b"My bookings" in response.data
    assert b"demo-booking-list" in response.data
    assert b"noindex,follow" in response.data


def test_demo_category_filters_and_api(client):
    expected = (
        ("clinics", "specialty=dermatology"),
        ("salons", "service=hair-styling"),
        ("hotels", "type=guest-house"),
        ("restaurants", "cuisine=north-indian"),
    )
    for category, query in expected:
        response = client.get(f"/api/v1/locations/trichy/{category}/businesses?{query}")
        assert response.status_code == 200
        assert response.json["businesses"]
        assert response.json["demo_mode"] is True

    filtered = client.get("/trichy/clinics?specialty=dermatology&browse=1")
    assert filtered.status_code == 200
    assert b"places found" in filtered.data
    assert b"Demo Care Clinic" in filtered.data


def test_demo_booking_configuration_is_json_driven(client):
    response = client.get("/api/v1/config/booking")
    assert response.status_code == 200
    settings = response.json["booking"]
    assert settings["convenience_fee_inr"] == 12
    assert settings["demo_payable_inr"] == 0
    assert settings["payments_enabled"] is False
    assert settings["timezone"] == "Asia/Kolkata"
    assert settings["services_menu_defaults"]["clinics"]


def test_demo_pages_are_noindex_and_excluded_from_sitemap(client):
    assert b"noindex,follow" in client.get("/").data
    assert b"noindex,follow" in client.get("/trichy").data
    assert b"noindex,follow" in client.get("/trichy/clinics").data
    assert b"demo-clinic-01" not in client.get("/sitemap.xml").data


def test_demo_can_be_removed_with_one_json_flag_and_empty_pages_stay_noindex(client, tmp_path, monkeypatch):
    shutil.copytree(content.CONTENT_ROOT, tmp_path, dirs_exist_ok=True)
    monkeypatch.setattr(content, "CONTENT_ROOT", tmp_path)
    demo = tmp_path / "global/demo.json"
    payload = json.loads(demo.read_text(encoding="utf-8"))
    payload["enabled"] = False
    demo.write_text(json.dumps(payload), encoding="utf-8")
    assert content.get_businesses("trichy", "clinics") == []
    assert client.get("/trichy/clinics/demo-clinic-01").status_code == 404
    assert client.get("/demo-bookings").status_code == 404
    assert b"demo-clinic-01" not in client.get("/sitemap.xml").data
    assert b"noindex,follow" in client.get("/trichy/clinics").data


def test_disable_category_hides_demo_businesses(client, tmp_path, monkeypatch):
    shutil.copytree(content.CONTENT_ROOT, tmp_path, dirs_exist_ok=True)
    monkeypatch.setattr(content, "CONTENT_ROOT", tmp_path)
    path = tmp_path / "locations/india/tamil-nadu/trichy/salons/category.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["enabled"] = False
    path.write_text(json.dumps(data), encoding="utf-8")
    assert client.get("/trichy/salons").status_code == 404
    assert client.get("/trichy/salons/demo-salon-01").status_code == 404
    assert client.get("/api/v1/locations/trichy/salons").status_code == 404
    assert all(row["slug"] != "salons" for row in
               client.get("/api/v1/locations/trichy/categories").json["categories"])


def test_reference_static_ui_assets_are_served_by_flask(client):
    for path in (
        "/static/css/site.css",
        "/static/css/demo.css",
        "/static/js/discovery.js",
        "/static/js/demo_booking.js",
        "/static/images/clinic_place.jpg",
        "/static/images/doctor_portrait.jpg",
        "/static/images/filters/parking.svg",
    ):
        response = client.get(path)
        assert response.status_code == 200, path
