"""Read versioned JSON defaults; later admin overrides can come from MariaDB."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = ROOT / "content"
SHARED_ROOT = ROOT / "shared"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _json(path, default=None):
    if not path.is_file():
        return {} if default is None else default
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def global_config(name):
    return _json(CONTENT_ROOT / "global" / (name + ".json"))


def get_site():
    return global_config("site")


def get_locations():
    result = []
    for slug in global_config("locations"):
        city = get_city(slug)
        if city:
            result.append(city)
    return result


def _city_path(slug):
    if not SLUG_RE.fullmatch(slug):
        return None
    relative = global_config("locations").get(slug)
    if not isinstance(relative, str):
        return None
    segments = relative.split("/")
    if not segments or any(not SLUG_RE.fullmatch(item) for item in segments):
        return None
    root = (CONTENT_ROOT / "locations").resolve()
    path = root.joinpath(*segments).resolve()
    return path if path.is_relative_to(root) else None


def get_city(slug):
    directory = _city_path(slug)
    if directory is None:
        return None
    data = _json(directory / "city.json")
    return data if data.get("slug") == slug else None


def get_category(city_slug, category_slug):
    if not SLUG_RE.fullmatch(category_slug):
        return None
    city = get_city(city_slug)
    if not city or category_slug not in city.get("categories", []):
        return None
    data = _json(_city_path(city_slug) / category_slug / "category.json")
    return data if data.get("slug") == category_slug else None


def get_categories(city_slug):
    city = get_city(city_slug)
    if not city:
        return []
    return [item for slug in city.get("categories", [])
            if (item := get_category(city_slug, slug))]


def get_businesses(city_slug, category_slug):
    if not get_category(city_slug, category_slug):
        return []
    directory = _city_path(city_slug) / category_slug
    businesses = []
    for item in directory.iterdir():
        if not item.is_dir() or not SLUG_RE.fullmatch(item.name):
            continue
        data = _json(item / "data.json")
        if data.get("published") is True and SLUG_RE.fullmatch(str(data.get("slug", ""))):
            businesses.append(data)
    return sorted(businesses, key=lambda item: (item.get("name") or "").casefold())


def get_business(city_slug, category_slug, business_slug):
    if not SLUG_RE.fullmatch(business_slug):
        return None
    return next((item for item in get_businesses(city_slug, category_slug)
                 if item["slug"] == business_slug), None)


def _merge(base, override):
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def get_theme(city_slug=None, category_slug=None, business=None):
    theme = _merge(_json(SHARED_ROOT / "design_tokens.json"), global_config("theme"))
    if city_slug and category_slug:
        category = get_category(city_slug, category_slug)
        if category:
            theme = _merge(theme, category.get("theme", {}))
    if business:
        theme = _merge(theme, business.get("theme", {}))
    return theme


def theme_css(theme):
    # Sanitize CSS variable values, even when overrides are introduced later.
    colors = theme.get("colors", {})
    variables = []
    for name in ("primary", "secondary", "background", "surface", "text", "muted"):
        value = colors.get(name)
        if isinstance(value, str) and HEX_RE.fullmatch(value):
            variables.append("--color-" + name + ": " + value)
    return "; ".join(variables)


def page_meta(kind, city=None, category=None, business=None):
    defaults = global_config("seo").get(kind, {})
    site = get_site()
    values = {
        "site": site.get("name", "KALLAH Book"),
        "city": (city or {}).get("name", ""),
        "category": (category or {}).get("name", ""),
        "name": (business or {}).get("name", ""),
    }
    override = (business or {}).get("seo", {})
    meta = _merge(defaults, override)
    return {key: str(meta.get(key, "")).format(**values)
            for key in ("title", "description")}
