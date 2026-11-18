"""Public pages, category-specific filters, and SEO."""
from xml.etree import ElementTree as ET
from flask import Blueprint, Response, abort, current_app, render_template, request
from ..content import (
    filter_businesses, get_business, get_businesses, get_categories,
    get_category, get_city, get_locations, get_quick_links,
    get_theme, page_meta, theme_css,
)

web_bp = Blueprint("web", __name__)
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def _meta(kind, indexable, city=None, category=None, business=None):
    meta = page_meta(kind, city, category, business)
    meta["canonical"] = current_app.config["SITE_URL"] + request.path
    meta["indexable"] = indexable
    return meta


def _home(city, root):
    slug = city["slug"] if city else None
    categories = get_categories(slug) if slug else []
    featured = [
        {"business": business, "category": category}
        for category in categories for business in get_businesses(slug, category["slug"])
        if business.get("featured") is True
    ][:8]
    return {"city": city, "active_city": None if root else city,
            "is_root": root, "categories": categories,
            "quick_links": get_quick_links(slug) if slug else [], "featured": featured}


@web_bp.get("/")
def home():
    cities = get_locations()
    city = get_city("trichy") or (cities[0] if cities else None)
    return render_template("pages/home.html", meta=_meta("home", True), **_home(city, True))


@web_bp.get("/<city_slug>")
def city_page(city_slug):
    city = get_city(city_slug)
    if not city:
        abort(404)
    active = any(get_businesses(city_slug, c["slug"]) for c in get_categories(city_slug))
    return render_template("pages/city.html", meta=_meta("city", active, city=city),
                           **_home(city, False))


@web_bp.get("/<city_slug>/<category_slug>")
def category_page(city_slug, category_slug):
    city, category = get_city(city_slug), get_category(city_slug, category_slug)
    if not city or not category:
        abort(404)
    all_businesses = get_businesses(city_slug, category_slug)
    selected = request.args.to_dict(flat=True)
    matching = filter_businesses(all_businesses, category.get("filters", []), selected)
    return render_template(
        "pages/category.html", active_city=city, city=city, category=category,
        businesses=matching, selected=selected, total_businesses=len(all_businesses),
        theme_css=theme_css(get_theme(city_slug, category_slug)),
        meta=_meta("category", bool(all_businesses), city=city, category=category),
    )


@web_bp.get("/<city_slug>/<category_slug>/<business_slug>")
def business_page(city_slug, category_slug, business_slug):
    city, category = get_city(city_slug), get_category(city_slug, category_slug)
    business = get_business(city_slug, category_slug, business_slug)
    if not city or not category or not business:
        abort(404)
    return render_template(
        "pages/business.html", active_city=city, city=city, category=category,
        business=business, theme_css=theme_css(get_theme(city_slug, category_slug, business)),
        meta=_meta("business", True, city=city, category=category, business=business),
    )


@web_bp.get("/robots.txt")
def robots():
    return Response("User-agent: *\nAllow: /\nSitemap: " +
                    current_app.config["SITE_URL"] + "/sitemap.xml\n", mimetype="text/plain")


@web_bp.get("/sitemap.xml")
def sitemap():
    urls = ["/"]
    for city in get_locations():
        slug = city["slug"]
        with_businesses = []
        for category in get_categories(slug):
            category_slug = category["slug"]
            businesses = get_businesses(slug, category_slug)
            if businesses:
                with_businesses.append(category_slug)
                urls.append("/" + slug + "/" + category_slug)
                urls.extend("/" + slug + "/" + category_slug + "/" + b["slug"]
                            for b in businesses)
        if with_businesses:
            urls.append("/" + slug)
    ET.register_namespace("", SITEMAP_NS)
    root = ET.Element("{" + SITEMAP_NS + "}urlset")
    for path in sorted(set(urls)):
        node = ET.SubElement(root, "{" + SITEMAP_NS + "}url")
        ET.SubElement(node, "{" + SITEMAP_NS + "}loc").text = current_app.config["SITE_URL"] + path
    return Response(ET.tostring(root, encoding="utf-8", xml_declaration=True),
                    mimetype="application/xml")


@web_bp.app_errorhandler(404)
def not_found(_error):
    return render_template("pages/404.html", meta=_meta("not_found", False)), 404
