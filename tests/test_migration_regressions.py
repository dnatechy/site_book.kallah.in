"""Regression coverage for the KALLAH Book AI Studio preview migration."""
from pathlib import Path

PROFILE = "/trichy/salons/demo-salon-02/demo-salons-person-01"


def test_salon_person_profile_and_trailing_slash(client):
    response = client.get(PROFILE)
    assert response.status_code == 200
    html = response.data
    assert b"Ananya Krishnan" in html
    assert b"Demo Style Salon 02" in html
    assert b"Available at 2 locations" in html
    assert b"booking-slot-legend" in html
    assert b"session-bars-container" in html
    assert b"header-links" not in html
    assert b"professional-profile-card" not in html
    assert b"reviews-section" in html
    assert b"person-reviews" in html
    assert b"contact-actions" in html
    assert html.index(b"professional-profile-top") < html.index(b"direct-booking-card")
    assert html.index(b"direct-booking-card") < html.index(b"professional-reviews-block")
    assert b"demo-salons-person-01/availability" in html

    redirected = client.get(PROFILE + "/?from=preview")
    assert redirected.status_code == 308
    assert redirected.headers["Location"].endswith(PROFILE + "?from=preview")
    assert client.get(PROFILE + "/", follow_redirects=True).status_code == 200


def test_phone_and_demo_history_from_reference(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"phone-country-code" in response.data
    assert b"+91" in response.data
    assert b"98765 - 43210" in response.data
    script = (Path(__file__).resolve().parents[1] / "app/static/js/demo_booking.js").read_text()
    assert "const formatPhone" in script
    assert "booking.kind === 'room'" in script
    assert "booking.kind === 'dining'" in script
    assert "getOccupiedSpans()" in script


def test_demo_blocked_spans_are_identical_to_flutter_slots(client):
    url = (
        "/api/v1/locations/trichy/salons/businesses/demo-salon-01/"
        "professionals/demo-salons-person-01/availability"
        "?venue=demo-salon-01&days=2&service_id=haircut"
    )
    response = client.get(url)
    assert response.status_code == 200
    availability = response.json["availability"]
    assert availability["capacity_is_live"] is False
    assert availability["booking_is_persistent"] is False
    assert availability["demo_booked_spans_are_sample"] is True
    days = [d for d in availability["days"] if d["enabled"]]
    assert days
    assert any(d["booked_spans"] for d in days)
    assert any(not s["available"] for d in days for s in d["slots"])

    def minutes(value):
        hours, minute = map(int, value.split(":"))
        return hours * 60 + minute

    for day in days:
        for slot in day["slots"]:
            overlapping = any(
                minutes(slot["start"]) < minutes(b["end"])
                and minutes(b["start"]) < minutes(slot["end"])
                for b in day["booked_spans"]
            )
            assert slot["available"] is not overlapping


def test_shared_review_cards_across_business_types(client):
    routes = (
        PROFILE,
        "/trichy/hotels/demo-hotel-01/rooms/deluxe-room",
        "/trichy/restaurants/demo-restaurant-01",
    )
    for route in routes:
        response = client.get(route)
        assert response.status_code == 200, route
        assert b"reviews-grid" in response.data
        assert b"review-card" in response.data
