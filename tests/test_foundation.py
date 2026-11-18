import json
import shutil
from pathlib import Path

from app import content


def test_home_health_and_theme(client):
    assert client.get("/").status_code == 200
    assert b"KALLAH Book" in client.get("/").data
    assert client.get("/api/v1/health").json["status"] == "ok"
    assert client.get("/api/v1/config/theme").json["theme"]["colors"]["primary"] == "#E53935"


def test_location_category_and_empty_sitemap(client):
    assert client.get("/trichy").status_code == 200
    response = client.get("/trichy/clinics")
    assert response.status_code == 200
    assert b"noindex,follow" in response.data
    assert client.get("/api/v1/locations/trichy/categories").json["categories"]
    assert b"https://book.kallah.in/trichy/clinics" not in client.get("/sitemap.xml").data
    assert client.get("/trichy/clinics/unknown").status_code == 404
    assert client.get("/api/v1/locations/invalid/categories").status_code == 404


def test_published_business_isolated_content(client, tmp_path, monkeypatch):
    shutil.copytree(content.CONTENT_ROOT, tmp_path, dirs_exist_ok=True)
    monkeypatch.setattr(content, "CONTENT_ROOT", tmp_path)
    demo_config = tmp_path / "global/demo.json"
    demo_config.write_text('{"enabled": false}', encoding="utf-8")
    directory = tmp_path / "locations/india/tamil-nadu/trichy/clinics/clinic-2001"
    directory.mkdir()
    data = {
        "id": 2001, "slug": "example-clinic", "name": "Example Clinic",
        "published": False, "content": {"heading": "Example Clinic", "summary": "Demo record"},
        "seo": {"title": "Example Clinic in {city} | {site}"},
        "theme": {"colors": {"primary": "#123456"}}
    }
    (directory / "data.json").write_text(json.dumps(data), encoding="utf-8")
    assert client.get("/trichy/clinics/example-clinic").status_code == 404
    data["published"] = True
    (directory / "data.json").write_text(json.dumps(data), encoding="utf-8")
    response = client.get("/trichy/clinics/example-clinic")
    assert response.status_code == 200
    assert b"Example Clinic in Trichy" in response.data
    # Default: the site palette cannot be silently overridden by a business.
    assert b"#123456" not in response.data
    assert b"#E53935" in response.data
    url = "/api/v1/locations/trichy/clinics/businesses/example-clinic"
    assert client.get(url).json["theme"]["colors"]["primary"] == "#E53935"
    # Only centrally configured category accent overrides are allowed.
    theme_file = tmp_path / "global/theme.json"
    theme = json.loads(theme_file.read_text(encoding="utf-8"))
    theme["mode"] = "category"
    theme["category_colors"] = {"clinics": {"primary": "#123456", "brand_accent": "#000000"}}
    theme_file.write_text(json.dumps(theme), encoding="utf-8")
    assert b"#123456" in client.get("/trichy/clinics/example-clinic").data
    palette = client.get(url).json["theme"]["colors"]
    assert palette["primary"] == "#123456"
    assert palette["brand_accent"] == "#E53935"
    assert b"example-clinic" in client.get("/sitemap.xml").data
    assert b"noindex,follow" not in client.get("/trichy/clinics").data
    assert client.get("/trichy/salons/example-clinic").status_code == 404
