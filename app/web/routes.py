"""Public pages, category-specific filters, and SEO."""
from xml.etree import ElementTree as ET
from flask import Blueprint, Response, abort, current_app, jsonify, render_template, request
from ..content import (
    filter_businesses, get_business, get_businesses, get_categories,
    get_category, get_city, get_locations, get_professional, get_quick_links,
    get_theme, page_meta, theme_css, demo_enabled,
)

web_bp = Blueprint("web", __name__)
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def _meta(kind, indexable, city=None, category=None, business=None):
    meta = page_meta(kind, city, category, business)
    meta["canonical"] = current_app.config["SITE_URL"] + request.path
    meta["indexable"] = indexable and not demo_enabled()
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


@web_bp.get("/demo-bookings")
def demo_bookings():
    if not demo_enabled():
        abort(404)
    return render_template("pages/demo_bookings.html", meta=_meta("home", False),
                           active_city=None)


@web_bp.get("/login")
def login_page():
    next_url = request.args.get("next", "/")
    if not isinstance(next_url, str) or not next_url.startswith("/") or next_url.startswith("//"):
        next_url = "/"
    meta = _meta("home", False)
    meta["title"] = "Sign in with mobile | KALLAH Book"
    meta["description"] = "Sign in with your mobile number to confirm your appointment slot."
    return render_template("pages/login.html", meta=meta, active_city=None, next_url=next_url)


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
    if not selected:
        toggles = [
            f for f in category.get("filters", [])
            if isinstance(f, dict) and f.get("type") in ("toggle", "proximity")
        ]
        return render_template(
            "pages/category_filter.html", active_city=city, city=city, category=category,
            toggles=toggles, total_businesses=len(all_businesses),
            theme_css=theme_css(get_theme(city_slug, category_slug)),
            meta=_meta("category", bool(all_businesses), city=city, category=category),
        )
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
        "pages/restaurant.html" if category_slug == "restaurants" else "pages/business.html", active_city=city, city=city, category=category,
        business=business, theme_css=theme_css(get_theme(city_slug, category_slug, business)),
        meta=_meta("business", True, city=city, category=category, business=business),
    )


@web_bp.get("/<city_slug>/<category_slug>/<business_slug>/<person_id>")
def professional_page(city_slug, category_slug, business_slug, person_id):
    city, category = get_city(city_slug), get_category(city_slug, category_slug)
    business, person = get_professional(city_slug, category_slug, business_slug, person_id)
    if not city or not category or not business or not person:
        abort(404)
    meta = _meta("business", True, city=city, category=category, business=business)
    meta["title"] = f"{person['name']} — {business['name']} | {city['name']} | KALLAH Book"
    meta["description"] = (
        f"Book a direct appointment slot with {person['name']} ({person.get('role', 'Specialist')}) "
        f"at {business['name']} in {city['name']}."
    )
    return render_template(
        "pages/professional.html", active_city=city, city=city, category=category,
        business=business, person=person,
        theme_css=theme_css(get_theme(city_slug, category_slug, business)),
        meta=meta,
    )


@web_bp.get('/<city_slug>/hotels/<business_slug>/rooms/<room_id>')
def room_page(city_slug, business_slug, room_id):
    city, category = get_city(city_slug), get_category(city_slug, 'hotels')
    business = get_business(city_slug, 'hotels', business_slug)
    room = next((r for r in (business or {}).get('rooms', []) if r['id'] == room_id), None)
    if not city or not category or not business or not room:
        abort(404)
    meta = _meta('business', True, city=city, category=category, business=business)
    meta['title'] = f"{room['name']} — {business['name']} | KALLAH Book"
    meta['description'] = room.get('description', '')
    return render_template('pages/room.html', city=city, active_city=city, category=category,
                           business=business, room=room, meta=meta,
                           theme_css=theme_css(get_theme(city_slug, 'hotels', business)))


@web_bp.get("/robots.txt")
def robots():
    return Response("User-agent: *\nAllow: /\nSitemap: " +
                    current_app.config["SITE_URL"] + "/sitemap.xml\n", mimetype="text/plain")


@web_bp.get("/sitemap.xml")
def sitemap():
    urls = [] if demo_enabled() else ["/"]
    for city in ([] if demo_enabled() else get_locations()):
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
                if category_slug == 'hotels':
                    urls.extend(f"/{slug}/hotels/{b['slug']}/rooms/{room['id']}"
                                for b in businesses for room in b.get('rooms', []))
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
    if request.path.startswith("/api/"):
        return jsonify({
            "api_version": "v1",
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested API endpoint was not found.",
            },
        }), 404
    return render_template("pages/404.html", meta=_meta("not_found", False)), 404
