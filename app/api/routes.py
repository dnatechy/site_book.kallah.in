"""Read-only foundation endpoints; booking and payments are NOT implemented."""
from flask import Blueprint, abort, jsonify
from ..content import (
    get_business, get_businesses, get_categories, get_category, get_city,
    get_locations, get_theme,
)

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "kallah-book", "version": "v1"})


@api_bp.get("/config/theme")
def theme():
    return jsonify({"theme": get_theme()})


@api_bp.get("/locations")
def locations():
    return jsonify({"locations": get_locations()})


@api_bp.get("/locations/<city_slug>/categories")
def categories(city_slug):
    if not get_city(city_slug):
        abort(404)
    return jsonify({"categories": get_categories(city_slug)})


@api_bp.get("/locations/<city_slug>/<category_slug>/businesses")
def businesses(city_slug, category_slug):
    if not get_category(city_slug, category_slug):
        abort(404)
    return jsonify({"businesses": get_businesses(city_slug, category_slug)})


@api_bp.get("/locations/<city_slug>/<category_slug>/businesses/<business_slug>")
def business_detail(city_slug, category_slug, business_slug):
    business = get_business(city_slug, category_slug, business_slug)
    if not business:
        abort(404)
    return jsonify({"business": business,
                    "theme": get_theme(city_slug, category_slug, business)})
