"""Versioned JSON API shared by the web UI and future Flutter clients."""
from math import asin, ceil, cos, radians, sin, sqrt
from flask import Blueprint, abort, jsonify, request
from ..content import (
    demo_enabled, filter_businesses, get_booking_config, get_business,
    get_businesses, get_categories, get_category, get_city, get_locations,
    get_professional, get_professionals, get_quick_links, get_pages, get_site, get_theme,
)
from ..services.availability import build_availability

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


def _response(**payload):
    payload["api_version"] = "v1"
    return jsonify(payload)


def _truthy(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _number_arg(name, minimum, maximum):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        abort(400, description=f"'{name}' must be a number.")
    if not minimum <= value <= maximum:
        abort(400, description=f"'{name}' is outside the allowed range.")
    return value


def _integer_arg(name, default, minimum, maximum):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        abort(400, description=f"'{name}' must be an integer.")
    if not minimum <= value <= maximum:
        abort(400, description=f"'{name}' must be between {minimum} and {maximum}.")
    return value


def _distance_km(lat1, lng1, lat2, lng2):
    earth_radius_km = 6371.0088
    p1, p2 = radians(lat1), radians(lat2)
    dp, dl = radians(lat2 - lat1), radians(lng2 - lng1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(min(1.0, a)))


def _matches_search(record, query):
    if not query:
        return True
    content = record.get("content") if isinstance(record.get("content"), dict) else {}
    values = [record.get("name"), record.get("address"), record.get("area"),
              content.get("heading"), content.get("summary"), content.get("description")]
    for field in ("specialties", "services", "cuisines", "dishes"):
        value = record.get(field, [])
        values.extend(value if isinstance(value, list) else [value])
    for person in record.get("professionals", []):
        if isinstance(person, dict):
            values.extend((person.get("name"), person.get("role"), person.get("description")))
    return query.casefold() in " ".join(str(value) for value in values if value).casefold()


@api_bp.errorhandler(400)
def api_bad_request(error):
    return jsonify({"api_version": "v1", "error": {
        "code": "BAD_REQUEST",
        "message": getattr(error, "description", None) or "The request is invalid.",
    }}), 400


@api_bp.errorhandler(404)
def api_not_found(_error):
    return jsonify({"api_version": "v1", "error": {
        "code": "NOT_FOUND",
        "message": "The requested KALLAH Book resource was not found.",
    }}), 404


@api_bp.get("/health")
def health():
    return _response(status="ok", service="kallah-book")


@api_bp.get("/bootstrap")
def bootstrap():
    city_slug = request.args.get("city", "trichy")
    city = get_city(city_slug) if city_slug else None
    if city_slug and not city:
        abort(404)
    selected = None
    if city:
        selected = {"city": city, "categories": get_categories(city_slug),
                    "quick_links": get_quick_links(city_slug)}
    return _response(site=get_site(), pages=get_pages(), theme=get_theme(), booking=get_booking_config(),
                     demo_mode=demo_enabled(), locations=get_locations(), selected_location=selected)


@api_bp.get("/config/site")
def site_config():
    return _response(site=get_site())


@api_bp.get("/config/pages")
def pages_config():
    return _response(pages=get_pages())


@api_bp.get("/config/theme")
def theme():
    return _response(theme=get_theme())


@api_bp.get("/config/booking")
def booking_config():
    return _response(booking=get_booking_config(), demo_mode=demo_enabled())


@api_bp.get("/locations")
def locations():
    return _response(locations=get_locations(), demo_mode=demo_enabled())


@api_bp.get("/locations/<city_slug>")
def location_detail(city_slug):
    city = get_city(city_slug)
    if not city:
        abort(404)
    return _response(city=city, categories=get_categories(city_slug),
                     quick_links=get_quick_links(city_slug), theme=get_theme(),
                     demo_mode=demo_enabled())


@api_bp.get("/locations/<city_slug>/categories")
def categories(city_slug):
    if not get_city(city_slug):
        abort(404)
    return _response(categories=get_categories(city_slug),
                     quick_links=get_quick_links(city_slug), demo_mode=demo_enabled())


@api_bp.get("/locations/<city_slug>/<category_slug>")
def category_detail(city_slug, category_slug):
    category = get_category(city_slug, category_slug)
    if not category:
        abort(404)
    return _response(city=get_city(city_slug), category=category,
                     filters=category.get("filters", []),
                     theme=get_theme(city_slug, category_slug), demo_mode=demo_enabled())


@api_bp.get("/locations/<city_slug>/<category_slug>/businesses")
def businesses(city_slug, category_slug):
    category = get_category(city_slug, category_slug)
    if not category:
        abort(404)
    matching = filter_businesses(get_businesses(city_slug, category_slug),
                                 category.get("filters", []), request.args.to_dict(flat=True))
    query = (request.args.get("q") or "").strip()[:120]
    if query:
        matching = [item for item in matching if _matches_search(item, query)]
    lat, lng = _number_arg("lat", -90, 90), _number_arg("lng", -180, 180)
    if (lat is None) != (lng is None):
        abort(400, description="Both lat and lng are required together.")
    near = _truthy(request.args.get("near-me") or request.args.get("near"))
    radius_km = _number_arg("radius_km", 0.1, 200) or 10.0
    if near and lat is None:
        abort(400, description="Near-me filtering requires lat and lng.")
    if lat is not None:
        for item in matching:
            geo = item.get("geo") if isinstance(item.get("geo"), dict) else {}
            try:
                item["distance_km"] = round(_distance_km(
                    lat, lng, float(geo["lat"]), float(geo["lng"])
                ), 2)
            except (KeyError, TypeError, ValueError):
                item["distance_km"] = None
    if near:
        matching = [item for item in matching if item.get("distance_km") is not None
                    and item["distance_km"] <= radius_km]
    sort = request.args.get("sort", "name_asc")
    if sort == "name_asc":
        matching.sort(key=lambda item: (item.get("name") or "").casefold())
    elif sort == "name_desc":
        matching.sort(key=lambda item: (item.get("name") or "").casefold(), reverse=True)
    elif sort == "rating_desc":
        matching.sort(key=lambda item: float(item.get("rating_value") or 0), reverse=True)
    elif sort == "featured":
        matching.sort(key=lambda item: (item.get("featured") is not True,
                                        (item.get("name") or "").casefold()))
    elif sort == "distance_asc":
        if lat is None:
            abort(400, description="Sorting by distance requires lat and lng.")
        matching.sort(key=lambda item: item.get("distance_km")
                      if item.get("distance_km") is not None else float("inf"))
    else:
        abort(400, description="Unsupported sort value.")
    total = len(matching)
    page = _integer_arg("page", 1, 1, 1000000)
    per_page = _integer_arg("per_page", 20, 1, 100)
    start = (page - 1) * per_page
    total_pages = ceil(total / per_page) if total else 0
    return _response(
        businesses=matching[start:start + per_page],
        filters=category.get("filters", []), total=total,
        pagination={"page": page, "per_page": per_page, "total_pages": total_pages,
                    "has_previous": page > 1, "has_next": page < total_pages},
        applied_filters={definition["key"]: request.args.get(definition["key"])
                         for definition in category.get("filters", [])
                         if isinstance(definition, dict) and definition.get("key") in request.args},
        search=query, sort=sort, demo_mode=demo_enabled(),
    )


@api_bp.get("/locations/<city_slug>/<category_slug>/businesses/<business_slug>")
def business_detail(city_slug, category_slug, business_slug):
    business = get_business(city_slug, category_slug, business_slug)
    if not business:
        abort(404)
    return _response(business=business, professionals=business.get("professionals", []),
                     theme=get_theme(city_slug, category_slug, business), demo_mode=demo_enabled())


@api_bp.get("/locations/<city_slug>/<category_slug>/businesses/<business_slug>/professionals")
def professionals(city_slug, category_slug, business_slug):
    business = get_business(city_slug, category_slug, business_slug)
    if not business:
        abort(404)
    category = get_category(city_slug, category_slug) or {}
    return _response(professionals=get_professionals(business, city_slug=city_slug),
                     professional_label=category.get("professional_label"), demo_mode=demo_enabled())


@api_bp.get("/locations/<city_slug>/<category_slug>/businesses/<business_slug>/professionals/<person_id>")
def professional_detail(city_slug, category_slug, business_slug, person_id):
    business, person = get_professional(city_slug, category_slug, business_slug, person_id)
    if not business or not person:
        abort(404)
    booking = get_booking_config()
    services = person.get("services_menu") or booking.get("services_menu_defaults", {}).get(category_slug, [])
    return _response(
        professional=person, services=services,
        business={"name": business["name"], "slug": business["slug"],
                  "address": business.get("address"), "area": business.get("area"),
                  "phone": business.get("phone"), "email": business.get("email"),
                  "photo_url": business.get("photo_url")},
        booking=booking, availability_url=request.base_url + "/availability",
        demo_mode=demo_enabled(),
    )


@api_bp.get("/locations/<city_slug>/<category_slug>/businesses/<business_slug>/professionals/<person_id>/availability")
def professional_availability(city_slug, category_slug, business_slug, person_id):
    business, person = get_professional(city_slug, category_slug, business_slug, person_id)
    if not business or not person:
        abort(404)
    venues = person.get("venues", [])
    venue_slug = request.args.get("venue", business_slug)
    venue = next((item for item in venues if item.get("business_slug") == venue_slug), None)
    if not venue:
        abort(404)
    booking = get_booking_config()
    service_id = request.args.get("service_id")
    start_date = request.args.get("date") or request.args.get("from")
    days = 1 if request.args.get("date") else _integer_arg(
        "days", int(booking.get("availability_window_days", 7)), 1, 14
    )
    try:
        availability = build_availability(person, venue, booking, start_date, days, service_id)
    except ValueError as error:
        abort(400, description=str(error))
    return _response(
        availability=availability,
        business={"slug": business["slug"], "name": business["name"]},
        professional={"id": person.get("id"), "name": person.get("name")},
        demo_mode=demo_enabled(),
        availability_mode="demo_preview" if business.get("is_demo") else "published_schedule",
    )
