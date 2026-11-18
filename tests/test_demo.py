"""Public demo fixture contracts: 40 records, 40 professionals, filters, SEO, gating."""
import json
import shutil

from app import content


CATEGORIES = ("clinics", "salons", "hotels", "restaurants")


def test_each_category_has_ten_demo_businesses_and_people(client):
    for category in CATEGORIES:
        rows = content.get_businesses("trichy", category)
        assert len(rows) == 10, (category, len(rows))
        assert all(record["is_demo"] is True for record in rows)
        assert len({record["slug"] for record in rows}) == 10
        assert sum(len(record["professionals"]) for record in rows) == 10
        for record in rows:
            assert record["demo_rating"] >= 3.5
            assert record["rating_label"] == "Demo score"
            assert record["professionals"][0]["demo_slots"]
            slug = record["slug"]
            response = client.get(f"/trichy/{category}/{slug}")
            assert response.status_code == 200
            assert b"Try sample slots" in response.data
            assert b"Confirm demo booking" in response.data
            assert b'noindex,follow' in response.data
            assert b"not a real" in response.data.lower()
            detail = client.get(f"/api/v1/locations/trichy/{category}/businesses/{slug}")
            assert detail.status_code == 200
            assert detail.json["demo_mode"] is True
            people = client.get(f"/api/v1/locations/trichy/{category}/businesses/{slug}/professionals")
            assert len(people.json["professionals"]) == 1


def test_fee_is_only_a_json_driven_display(client):
    response = client.get("/api/v1/config/booking")
    assert response.status_code == 200
    settings = response.json["booking"]
    assert settings["convenience_fee_inr"] == 12
    assert settings["demo_payable_inr"] == 0
    assert settings["payments_enabled"] is False
    page = client.get("/trichy/clinics/demo-clinic-01")
    assert "₹12".encode("utf-8") in page.data
    assert b"Confirm demo booking" in page.data


def test_demo_pages_not_submitted_to_google(client):
    assert b"noindex,follow" in client.get("/").data
    assert b"noindex,follow" in client.get("/trichy").data
    assert b"noindex,follow" in client.get("/trichy/clinics").data
    assert b"demo-clinic-01" not in client.get("/sitemap.xml").data
    assert client.get("/demo-bookings").status_code == 200
    assert b"My demo bookings" in client.get("/demo-bookings").data
    assert b"Demo listings" not in client.get("/sitemap.xml").data


def test_demo_filter_variety(client):
    clinic = client.get("/trichy/clinics?specialty=dermatology")
    salon = client.get("/trichy/salons?service=haircut")
    hotels = client.get("/trichy/hotels?type=hotel")
    restaurants = client.get("/trichy/restaurants?cuisine=chinese")
    for response in (clinic, salon, hotels, restaurants):
        assert response.status_code == 200
        assert b"places found" in response.data
        assert b"Demo listing" in response.data
    api = client.get("/api/v1/locations/trichy/clinics/businesses?rating=4.5&parking=1")
    assert api.status_code == 200
    assert 0 < len(api.json["businesses"]) < 10


def test_demo_can_be_removed_with_one_json_flag(client, tmp_path, monkeypatch):
    shutil.copytree(content.CONTENT_ROOT, tmp_path, dirs_exist_ok=True)
    monkeypatch.setattr(content, "CONTENT_ROOT", tmp_path)
    demo = tmp_path / "global/demo.json"
    payload = json.loads(demo.read_text(encoding="utf-8"))
    payload["enabled"] = False
    demo.write_text(json.dumps(payload), encoding="utf-8")
    assert content.get_businesses("trichy", "clinics") == []
    assert client.get("/trichy/clinics/demo-clinic-01").status_code == 404
    assert client.get("/demo-bookings").status_code == 404
    assert b"DEMO MODE" not in client.get("/").data
    assert b"noindex,follow" in client.get("/trichy/clinics").data
    assert b"https://book.kallah.in/" in client.get("/sitemap.xml").data


def test_disable_category_hides_demo_businesses(client, tmp_path, monkeypatch):
    shutil.copytree(content.CONTENT_ROOT, tmp_path, dirs_exist_ok=True)
    monkeypatch.setattr(content, "CONTENT_ROOT", tmp_path)
    path = tmp_path / "locations/india/tamil-nadu/trichy/salons/category.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["enabled"] = False
    path.write_text(json.dumps(data), encoding="utf-8")
    assert client.get("/trichy/salons").status_code == 404
    assert client.get("/trichy/salons/demo-salon-01").status_code == 404
    assert all(row["slug"] != "salons" for row in
               client.get("/api/v1/locations/trichy/categories").json["categories"])
