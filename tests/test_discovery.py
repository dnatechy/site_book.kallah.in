"""Reference UI navigation, JSON category filters, and professional profiles."""
import json
import shutil

from app import content


def _sandbox(tmp_path, monkeypatch):
    shutil.copytree(content.CONTENT_ROOT, tmp_path, dirs_exist_ok=True)
    monkeypatch.setattr(content, "CONTENT_ROOT", tmp_path)
    (tmp_path / "global/demo.json").write_text('{"enabled": false}', encoding="utf-8")


def _business(root, category, slug, **changes):
    directory = root / "locations" / "india" / "tamil-nadu" / "trichy" / category / ("business-" + slug)
    directory.mkdir()
    record = {
        "id": 5001, "slug": slug, "name": slug.replace("-", " ").title(),
        "published": True, "featured": True,
        "services": ["haircut"], "specialties": ["dermatology"],
        "google_rating": 4.6, "rating_source": "google",
        "amenities": {"parking": True}, "geo": {"lat": 10.7905, "lng": 78.7047},
        "content": {"heading": "Sample Business", "summary": "Test record"},
        "professionals": [
            {"id": "test-person", "name": "Example Professional",
             "role": "Hair stylist", "services": ["haircut"],
             "photo_url": "javascript:alert(1)"},
            {"name": "Hidden Person", "enabled": False}
        ]
    }
    record.update(changes)
    (directory / "data.json").write_text(json.dumps(record), encoding="utf-8")
    return directory


def test_location_picker_home_and_extra_districts(client):
    root = client.get("/")
    assert root.status_code == 200
    assert b'id="location-modal"' in root.data
    assert b"Book ahead." in root.data
    assert b"Clinics" in root.data and b"Salons" in root.data
    assert b"Popular booking types" in root.data
    names = {city["slug"] for city in client.get("/api/v1/locations").json["locations"]}
    assert {"trichy", "madurai", "coimbatore", "chennai", "salem"} <= names
    assert client.get("/madurai").status_code == 200
    assert client.get("/madurai/clinics").status_code == 404


def test_category_specific_visual_filter_wizards(client):
    clinic = client.get("/trichy/clinics")
    salon = client.get("/trichy/salons")
    hotel = client.get("/trichy/hotels")
    restaurant = client.get("/trichy/restaurants")
    assert all(r.status_code == 200 for r in (clinic, salon, hotel, restaurant))
    assert b"Choose a specialty or browse clinics" in clinic.data
    assert b"Gastroenterology" in clinic.data
    assert b"Wheelchair access" in clinic.data
    assert b"Car parking" in clinic.data
    assert b"Choose your salon service" in salon.data
    assert b"Haircut" in salon.data and b"AC studio" in salon.data
    assert b"Specialty" not in salon.data
    assert b"Find the right hotel or stay" in hotel.data
    assert b"Guest House" in hotel.data and b"Free Wi-Fi" in hotel.data
    assert b"What would you like to eat?" in restaurant.data
    assert b"Biryani &amp; Grill" in restaurant.data
    assert b"/static/images/filters/" in clinic.data


def test_category_switch_hides_every_route(client, tmp_path, monkeypatch):
    _sandbox(tmp_path, monkeypatch)
    _business(tmp_path, "salons", "test-salon")
    assert client.get("/trichy/salons/test-salon").status_code == 200
    assert b"test-salon" in client.get("/sitemap.xml").data
    path = tmp_path / "locations/india/tamil-nadu/trichy/salons/category.json"
    category = json.loads(path.read_text(encoding="utf-8"))
    category["enabled"] = False
    path.write_text(json.dumps(category), encoding="utf-8")
    assert b"Salon appointments" not in client.get("/").data
    assert b"Salons" not in client.get("/trichy").data
    assert client.get("/trichy/salons").status_code == 404
    assert client.get("/trichy/salons/test-salon").status_code == 404
    assert client.get("/api/v1/locations/trichy/salons/businesses").status_code == 404
    assert client.get("/api/v1/locations/trichy/salons/businesses/test-salon").status_code == 404
    assert b"test-salon" not in client.get("/sitemap.xml").data
    assert all(c["slug"] != "salons" for c in
               client.get("/api/v1/locations/trichy/categories").json["categories"])


def test_filter_backend_and_professional_profile(client, tmp_path, monkeypatch):
    _sandbox(tmp_path, monkeypatch)
    _business(tmp_path, "salons", "test-salon")
    _business(tmp_path, "salons", "other-salon", services=["bridal"],
              google_rating=3.2, amenities={"parking": False}, professionals=[])
    page = client.get("/trichy/salons?service=haircut&rating=4.5&parking=1")
    assert page.status_code == 200
    assert b"Test Salon" in page.data
    assert b"Other Salon" not in page.data
    api = client.get("/api/v1/locations/trichy/salons/businesses?service=haircut&rating=4.5&parking=1")
    assert len(api.json["businesses"]) == 1
    detail = client.get("/trichy/salons/test-salon")
    assert b"Example Professional" in detail.data
    assert b"Open profile, reviews &amp; book" in detail.data
    assert b"javascript:alert" not in detail.data
    people = client.get("/api/v1/locations/trichy/salons/businesses/test-salon/professionals")
    assert people.status_code == 200
    assert len(people.json["professionals"]) == 1
    assert people.json["professionals"][0]["photo_url"] is None
    profile = client.get("/trichy/salons/test-salon/test-person")
    assert profile.status_code == 200
    assert b"Book with Example Professional" in profile.data
    assert b"booking-date-strip" in profile.data


def test_unpublished_business_and_professional_are_not_public(client, tmp_path, monkeypatch):
    _sandbox(tmp_path, monkeypatch)
    _business(tmp_path, "clinics", "test-clinic", published=False)
    assert client.get("/trichy/clinics/test-clinic").status_code == 404
    assert client.get("/madurai/clinics/test-clinic").status_code == 404
