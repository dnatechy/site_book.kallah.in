"""JSON-only discovery endpoints for future Flutter client."""
from flask import Blueprint, abort, jsonify, request
from ..content import (
    filter_businesses, get_business, get_businesses, get_categories,
    get_category, get_city, get_locations, get_professionals, get_quick_links, get_theme, demo_enabled, get_booking_config,
)
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "kallah-book", "version": "v1"})


@api_bp.get("/config/theme")
def theme():
    return jsonify({"theme": get_theme()})


@api_bp.get("/config/booking")
def booking_config():
    return jsonify({"booking": get_booking_config(), "demo_mode": demo_enabled()})


@api_bp.get("/locations")
def locations():
    return jsonify({"locations": get_locations(), "demo_mode": demo_enabled()})


@api_bp.get("/locations/<city_slug>/categories")
def categories(city_slug):
    if not get_city(city_slug):
        abort(404)
    return jsonify({"categories": get_categories(city_slug),
                    "quick_links": get_quick_links(city_slug)})


@api_bp.get("/locations/<city_slug>/<category_slug>/businesses")
def businesses(city_slug, category_slug):
    category = get_category(city_slug, category_slug)
    if not category:
        abort(404)
    all_businesses = get_businesses(city_slug, category_slug)
    return jsonify({"businesses": filter_businesses(all_businesses, category.get("filters", []),
                                                    request.args.to_dict(flat=True)),
                    "filters": category.get("filters", []), "total": len(all_businesses),
                    "demo_mode": demo_enabled()})


@api_bp.get("/locations/<city_slug>/<category_slug>/businesses/<business_slug>")
def business_detail(city_slug, category_slug, business_slug):
    business = get_business(city_slug, category_slug, business_slug)
    if not business:
        abort(404)
    return jsonify({"business": business, "theme": get_theme(city_slug, category_slug, business),
                    "demo_mode": demo_enabled()})


@api_bp.get("/locations/<city_slug>/<category_slug>/businesses/<business_slug>/professionals")
def professionals(city_slug, category_slug, business_slug):
    business = get_business(city_slug, category_slug, business_slug)
    if not business:
        abort(404)
    return jsonify({"professionals": get_professionals(business)})
