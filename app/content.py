"""Static JSON discovery, category gates, reusable filters and theme resolution."""
import json
import math
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = ROOT / "content"
SHARED_ROOT = ROOT / "shared"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FIELD_RE = re.compile(r"^[a-z][a-z0-9_.]*$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _json(path):
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def global_config(name):
    return _json(CONTENT_ROOT / "global" / (name + ".json"))


def get_site():
    return global_config("site")


def get_pages():
    return global_config("pages")


def get_booking_config():
    return global_config("booking")


def demo_enabled():
    """Turn all demonstration records on/off using one JSON flag."""
    return global_config("demo").get("enabled") is True


def demo_config():
    return global_config("demo")


def _city_path(slug):
    if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
        return None
    relative = global_config("locations").get(slug)
    if not isinstance(relative, str):
        return None
    segments = relative.split("/")
    if not segments or any(not SLUG_RE.fullmatch(part) for part in segments):
        return None
    root = (CONTENT_ROOT / "locations").resolve()
    path = root.joinpath(*segments).resolve()
    return path if path.is_relative_to(root) else None


def get_city(slug):
    path = _city_path(slug)
    if path is None:
        return None
    city = _json(path / "city.json")
    if city.get("slug") != slug or city.get("enabled", True) is False:
        return None
    return city


def get_locations():
    # Public location selection must not reveal disabled category metadata.
    keys = ("slug", "name", "state", "country", "geo")
    return [{key: city[key] for key in keys if key in city}
            for slug in global_config("locations") if (city := get_city(slug))]


def get_category(city_slug, category_slug):
    if not isinstance(category_slug, str) or not SLUG_RE.fullmatch(category_slug):
        return None
    city = get_city(city_slug)
    if not city or category_slug not in city.get("categories", []):
        return None
    category = _json(_city_path(city_slug) / category_slug / "category.json")
    if category.get("slug") != category_slug or category.get("enabled", True) is False:
        return None
    return category


def get_categories(city_slug):
    city = get_city(city_slug)
    if not city:
        return []
    return [category for slug in city.get("categories", [])
            if (category := get_category(city_slug, slug))]


def get_quick_links(city_slug):
    city = get_city(city_slug)
    if not city:
        return []
    links = []
    for item in city.get("quick_links", []):
        if not isinstance(item, dict):
            continue
        category = get_category(city_slug, item.get("category"))
        if category:
            links.append({"label": item.get("label") or category["name"],
                          "category": category["slug"]})
    return links


def safe_photo_url(value):
    if not isinstance(value, str):
        return None
    if (value.startswith("/static/images/") and ".." not in value
            and "\\" not in value and not any(c.isspace() for c in value)):
        return value
    parsed = urlsplit(value)
    if parsed.scheme == "https" and parsed.netloc and not parsed.username and not parsed.password:
        return value
    return None


def safe_social_links(raw):
    if not isinstance(raw, dict):
        return {}
    clean = {}
    for key in ("whatsapp", "instagram", "linkedin", "facebook"):
        val = raw.get(key)
        if not isinstance(val, str):
            continue
        parsed = urlsplit(val.strip())
        if parsed.scheme == "https" and parsed.netloc and not parsed.username and not parsed.password:
            clean[key] = val.strip()
    return clean


def _people_map(city_slug):
    cpath = _city_path(city_slug)
    if not cpath:
        return {}
    pdir = cpath / "people"
    if not pdir.is_dir():
        return {}
    mapping = {}
    for entry in pdir.iterdir():
        if not entry.is_dir() or not SLUG_RE.fullmatch(entry.name):
            continue
        record = _json(entry / "data.json")
        pid = record.get("id") or entry.name
        if record.get("enabled", True) is False or not record.get("name"):
            continue
        person = dict(record)
        person["id"] = pid
        person["photo_url"] = safe_photo_url(person.get("photo_url"))
        person["social_links"] = safe_social_links(person.get("social_links"))
        mapping[pid] = person
    return mapping


def get_professionals(business, city_slug=None):
    if business.get('booking_type') in ('rooms', 'dining'):
        return []
    people = []
    seen = set()
    pmap = _people_map(city_slug) if city_slug else {}
    bslug = business.get("slug")

    for pid in business.get("people_ids", []):
        person = pmap.get(pid)
        if person and pid not in seen:
            seen.add(pid)
            people.append(dict(person))

    if bslug and pmap:
        for pid in sorted(pmap):
            if pid in seen:
                continue
            person = pmap[pid]
            if any(isinstance(s, dict) and s.get("business_slug") == bslug
                   for s in person.get("schedules", [])):
                seen.add(pid)
                people.append(dict(person))

    for record in business.get("professionals", []):
        if not isinstance(record, dict) or record.get("enabled", True) is False:
            continue
        if not record.get("name"):
            continue
        pid = record.get("id")
        if pid and pid in seen:
            continue
        if pid:
            seen.add(pid)
        person = dict(record)
        person["photo_url"] = safe_photo_url(person.get("photo_url"))
        person["social_links"] = safe_social_links(person.get("social_links"))
        people.append(person)
    return people


def get_businesses(city_slug, category_slug):
    if not get_category(city_slug, category_slug):
        return []
    directory = _city_path(city_slug) / category_slug
    found = []
    for path in directory.iterdir():
        if not path.is_dir() or not SLUG_RE.fullmatch(path.name):
            continue
        business = _json(path / "data.json")
        slug = business.get("slug")
        if (business.get("published") is True and business.get("enabled", True) is not False
                and isinstance(slug, str) and SLUG_RE.fullmatch(slug)
                and (not business.get("is_demo") or demo_enabled())):
            business["photo_url"] = safe_photo_url(business.get("photo_url"))
            business["social_links"] = safe_social_links(business.get("social_links"))
            if category_slug == 'hotels':
                from .rooms import load_rooms
                business['booking_type'] = 'rooms'
                business['professionals'] = []
                business['rooms'] = load_rooms(path / 'rooms', business)
            elif category_slug == 'restaurants':
                from .dining import load_dining
                business['booking_type'] = 'dining'
                business['professionals'] = []
                business['dining'] = load_dining(path, business)
            else:
                business["professionals"] = get_professionals(business, city_slug=city_slug)
            if business.get("is_demo"):
                business["rating_value"] = business.get("demo_rating")
                business["rating_label"] = "Demo score"
            elif business.get("rating_source") == "google":
                business["rating_value"] = business.get("google_rating")
                business["rating_label"] = "Google rating"
            if category_slug == 'restaurants':
                business['rating_value'] = business['dining']['restaurant_reviews']['rating']
                business['rating_label'] = 'Guest rating'
            found.append(business)
    return sorted(found, key=lambda record: (record.get("name") or "").casefold())


def get_business(city_slug, category_slug, business_slug):
    if not isinstance(business_slug, str) or not SLUG_RE.fullmatch(business_slug):
        return None
    return next((record for record in get_businesses(city_slug, category_slug)
                 if record["slug"] == business_slug), None)


def get_professional(city_slug, category_slug, business_slug, person_id):
    if not isinstance(person_id, str) or not SLUG_RE.fullmatch(person_id):
        return None, None
    business = get_business(city_slug, category_slug, business_slug)
    if not business:
        return None, None
    person = next((p for p in business.get("professionals", []) if p.get("id") == person_id), None)
    if not person:
        return None, None
    person = dict(person)
    venues = []
    seen_slugs = set()
    category_cache = {}
    for sched in person.get("schedules", []):
        if not isinstance(sched, dict):
            continue
        v_slug = sched.get("business_slug")
        v_cat = sched.get("category_slug") or category_slug
        if not v_slug or v_slug in seen_slugs:
            continue
        if v_cat not in category_cache:
            category_cache[v_cat] = {b["slug"]: b for b in get_businesses(city_slug, v_cat)}
        v_biz = category_cache[v_cat].get(v_slug)
        if not v_biz:
            continue
        seen_slugs.add(v_slug)
        venues.append({
            "business_slug": v_biz["slug"],
            "business_name": v_biz["name"],
            "category_slug": v_cat,
            "area": v_biz.get("area"),
            "address": v_biz.get("address"),
            "phone": v_biz.get("phone"),
            "email": v_biz.get("email"),
            "social_links": v_biz.get("social_links", {}),
            "weekly": sched.get("weekly", {}),
            "enabled_dates": sched.get("enabled_dates", ["today", "tomorrow"]),
            "slot_minutes": sched.get("slot_minutes", 15),
            "url": f"/{city_slug}/{v_cat}/{v_biz['slug']}/{person_id}",
        })
    if not venues:
        venues.append({
            "business_slug": business["slug"],
            "business_name": business["name"],
            "category_slug": category_slug,
            "area": business.get("area"),
            "address": business.get("address"),
            "phone": business.get("phone"),
            "email": business.get("email"),
            "social_links": business.get("social_links", {}),
            "weekly": {},
            "enabled_dates": ["today", "tomorrow"],
            "slot_minutes": 15,
            "url": f"/{city_slug}/{category_slug}/{business['slug']}/{person_id}",
        })
    person["venues"] = venues
    if not person.get("social_links") and business.get("social_links"):
        person["social_links"] = dict(business["social_links"])
    from .gallery import load_gallery
    person["gallery"] = load_gallery(_city_path(city_slug), person, business, category_slug, demo_enabled())
    return business, person


def _values(record, field):
    if not isinstance(field, str) or not FIELD_RE.fullmatch(field):
        return []
    value = record
    for part in field.split("."):
        if not isinstance(value, dict):
            return []
        value = value.get(part)
    result = list(value) if isinstance(value, list) else [value]
    if field in ("specialties", "services"):
        for person in record.get("professionals", []):
            value = person.get(field, [])
            result.extend(value if isinstance(value, list) else [value])
    return [value for value in result if value is not None]


def filter_businesses(businesses, filters, selected):
    """Field-based JSON filters: select / min_number / toggle; proximity is client-only."""
    result = list(businesses)
    for definition in filters:
        if not isinstance(definition, dict):
            continue
        key, kind, field = (definition.get(k) for k in ("key", "type", "field"))
        if not isinstance(key, str) or not SLUG_RE.fullmatch(key) or kind == "proximity":
            continue
        raw = selected.get(key)
        if not raw:
            continue
        if kind == "select":
            allowed = {str(opt.get("value", "")).casefold()
                       for opt in definition.get("options", []) if isinstance(opt, dict)}
            if str(raw).casefold() not in allowed:
                continue
            result = [b for b in result if any(str(v).casefold() == str(raw).casefold()
                      for v in _values(b, field))]
        elif kind == "min_number":
            try:
                threshold = float(raw)
            except (ValueError, TypeError):
                continue
            if not math.isfinite(threshold) or not 0 <= threshold <= 5:
                continue
            def meets_rating(b):
                for v in _values(b, field):
                    try:
                        n = float(v)
                        if math.isfinite(n) and threshold <= n <= 5:
                            return True
                    except (TypeError, ValueError):
                        continue
                return False
            result = [b for b in result if meets_rating(b)]
        elif kind == "toggle" and str(raw).lower() in ("1", "true", "yes", "on"):
            result = [b for b in result if any(v is True for v in _values(b, field))]
    return result


def _merge(base, changes):
    merged = dict(base)
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def get_theme(city_slug=None, category_slug=None, business=None):
    """Single site-wide palette. Explicit opt-in permits a scoped override."""
    theme = _merge(_json(SHARED_ROOT / "design_tokens.json"), global_config("theme"))
    if theme.get("allow_scoped_overrides") is True:
        if city_slug and category_slug:
            category = get_category(city_slug, category_slug)
            if category:
                theme = _merge(theme, category.get("theme", {}))
        if business:
            theme = _merge(theme, business.get("theme", {}))
    return theme


def theme_css(theme):
    variables = []
    for name in ("primary", "secondary", "background", "surface", "ink", "text", "muted"):
        value = theme.get("colors", {}).get(name)
        if isinstance(value, str) and HEX_RE.fullmatch(value):
            variables.append("--color-" + name + ": " + value)
    return "; ".join(variables)


def page_meta(kind, city=None, category=None, business=None):
    defaults = global_config("seo").get(kind, {})
    meta = _merge(defaults, (city or {}).get("seo", {}))
    meta = _merge(meta, (category or {}).get("seo", {}))
    meta = _merge(meta, (business or {}).get("seo", {}))
    values = {"site": get_site().get("name", "KALLAH Book"),
              "city": (city or {}).get("name", ""),
              "category": (category or {}).get("name", ""),
              "name": (business or {}).get("name", "")}
    return {key: str(meta.get(key, "")).format(**values) for key in ("title", "description")}
