"""Public HTML, robots and sitemap routes."""
from xml.etree import ElementTree as ET

from flask import Blueprint, Response, abort, current_app, render_template, request
from ..content import (
    get_business, get_businesses, get_categories, get_category,
    get_city, get_locations, get_theme, page_meta, theme_css,
)

web_bp = Blueprint("web", __name__)
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def _meta(kind, indexable, city=None, category=None, business=None):
    data = page_meta(kind, city, category, business)
    data["canonical"] = current_app.config["SITE_URL"] + request.path
    data["indexable"] = indexable
    return data


@web_bp.get("/")
def home():
    return render_template("pages/home.html", cities=get_locations(),
                           meta=_meta("home", True))


@web_bp.get("/<city_slug>")
def city_page(city_slug):
    city = get_city(city_slug)
    if not city:
        abort(404)
    categories = get_categories(city_slug)
    active = any(get_businesses(city_slug, item["slug"]) for item in categories)
    return render_template("pages/city.html", city=city, categories=categories,
                           meta=_meta("city", active, city=city))


@web_bp.get("/<city_slug>/<category_slug>")
def category_page(city_slug, category_slug):
    city = get_city(city_slug)
    category = get_category(city_slug, category_slug)
    if not city or not category:
        abort(404)
    businesses = get_businesses(city_slug, category_slug)
    return render_template(
        "pages/category.html", city=city, category=category, businesses=businesses,
        theme_css=theme_css(get_theme(city_slug, category_slug)),
        meta=_meta("category", bool(businesses), city=city, category=category),
    )


@web_bp.get("/<city_slug>/<category_slug>/<business_slug>")
def business_page(city_slug, category_slug, business_slug):
    city = get_city(city_slug)
    category = get_category(city_slug, category_slug)
    business = get_business(city_slug, category_slug, business_slug)
    if not city or not category or not business:
        abort(404)
    return render_template(
        "pages/business.html", city=city, category=category, business=business,
        theme_css=theme_css(get_theme(city_slug, category_slug, business)),
        meta=_meta("business", True, city=city, category=category, business=business),
    )


@web_bp.get("/robots.txt")
def robots():
    body = "User-agent: *\nAllow: /\nSitemap: " + current_app.config["SITE_URL"] + "/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@web_bp.get("/sitemap.xml")
def sitemap():
    urls = ["/"]
    for city in get_locations():
        city_slug = city["slug"]
        published_categories = []
        for category in get_categories(city_slug):
            category_slug = category["slug"]
            businesses = get_businesses(city_slug, category_slug)
            if businesses:
                published_categories.append(category_slug)
                urls.append("/" + city_slug + "/" + category_slug)
                for business in businesses:
                    urls.append("/" + city_slug + "/" + category_slug + "/" + business["slug"])
        if published_categories:
            urls.append("/" + city_slug)
    ET.register_namespace("", SITEMAP_NS)
    root = ET.Element("{" + SITEMAP_NS + "}urlset")
    for path in sorted(set(urls)):
        element = ET.SubElement(root, "{" + SITEMAP_NS + "}url")
        ET.SubElement(element, "{" + SITEMAP_NS + "}loc").text = current_app.config["SITE_URL"] + path
    return Response(ET.tostring(root, encoding="utf-8", xml_declaration=True),
                    mimetype="application/xml")


@web_bp.app_errorhandler(404)
def not_found(_error):
    return render_template("pages/404.html", meta=_meta("not_found", False)), 404
