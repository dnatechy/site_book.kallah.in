"""Person albums: local folders, HTTPS images, and official Instagram embeds.

Only metadata is read. Remote media is never fetched or copied by the server.
"""
import json
import re
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / 'app/static/images/galleries'
SLUG = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
POST = re.compile(r'^/(p|reel)/([A-Za-z0-9_-]+)/?$')
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.avif', '.gif'}


def read_json(path):
    if not path.is_file():
        return {}
    with path.open(encoding='utf-8') as stream:
        return json.load(stream)


def safe_media_url(value):
    if not isinstance(value, str) or any(c.isspace() for c in value):
        return None
    if value.startswith('/static/images/') and '..' not in value and '\\' not in value and '..' not in unquote(value) and '\\' not in unquote(value):
        return value
    url = urlsplit(value)
    return value if url.scheme == 'https' and url.hostname and not url.username and not url.password else None


def instagram_url(value):
    if not isinstance(value, str):
        return None
    url = urlsplit(value)
    match = POST.fullmatch(url.path)
    if (url.scheme != 'https' or url.hostname not in ('instagram.com', 'www.instagram.com')
            or url.username or url.password or url.port not in (None, 443) or not match):
        return None
    return f'https://www.instagram.com/{match[1]}/{match[2]}/'


def load_gallery(city_path, person, business, category_slug, demo=False):
    pid = person.get('id', '')
    if not SLUG.fullmatch(pid):
        return {'albums': [], 'total': 0}
    raw = read_json(city_path / 'people' / pid / 'gallery.json')
    if not raw and demo:
        raw = read_json(ROOT / 'content/global/gallery.json').get('demo_categories', {}).get(category_slug, {})
    return resolve_gallery(raw, person, business)


def resolve_gallery(raw, person, business):
    albums = []
    seen = set()
    replacements = {'person_photo': person.get('photo_url'), 'business_photo': business.get('photo_url')}
    for album in raw.get('albums', [])[:12]:
        if not isinstance(album, dict):
            continue
        aid = album.get('id', '')
        if not SLUG.fullmatch(aid) or aid in seen or album.get('enabled') is False:
            continue
        seen.add(aid)
        items = []
        if album.get('source') == 'folder':
            folder = album.get('folder', '')
            segments = folder.split('/') if isinstance(folder, str) else []
            if segments and all(SLUG.fullmatch(part) for part in segments):
                directory = IMAGES.joinpath(*segments).resolve()
                if directory.is_relative_to(IMAGES.resolve()) and directory.is_dir():
                    for path in sorted(directory.iterdir()):
                        if (path.is_file() and path.suffix.lower() in EXTENSIONS
                                and path.resolve().is_relative_to(directory)):
                            items.append({'type': 'image', 'url': '/static/images/galleries/' + folder + '/' + quote(path.name),
                                          'caption': path.stem.replace('-', ' ').replace('_', ' ').lstrip('0123456789 ').strip().title()})
        else:
            for item in album.get('items', [])[:80]:
                if not isinstance(item, dict):
                    continue
                kind = item.get('type', 'image')
                value = replacements.get(item.get('ref')) if item.get('ref') else item.get('url')
                try:
                    url = instagram_url(value) if kind == 'instagram' else safe_media_url(value)
                except ValueError:
                    url = None
                if kind not in ('image', 'instagram') or not url:
                    continue
                items.append({'type': kind, 'url': url, 'caption': str(item.get('caption', ''))[:300],
                              'layout': item.get('layout') if item.get('layout') in ('portrait', 'landscape', 'square') else 'natural'})
        albums.append({'id': aid, 'title': str(album.get('title', aid))[:80],
                       'description': str(album.get('description', ''))[:400], 'items': items[:80]})
    return {'albums': albums, 'total': sum(len(album['items']) for album in albums)}
