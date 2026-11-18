"""Group seating and dish preorders. Quotes are read-only; no payment is collected."""
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from .gallery import resolve_gallery, safe_media_url


def review_summary(reviews):
    reviews = [r for r in reviews if isinstance(r, dict) and type(r.get('rating')) in (int, float) and 1 <= r['rating'] <= 5]
    return {'reviews': reviews, 'review_count': len(reviews),
            'rating': round(sum(r['rating'] for r in reviews) / len(reviews), 1) if reviews else None}


def load_dining(directory, business):
    def read(path, default):
        return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default
    config = read(directory / 'seating.json', {})
    menu = []
    for path in sorted((directory / 'menu').glob('*.json')):
        dish = read(path, {})
        if dish.get('enabled', True) is False:
            continue
        dish.update(review_summary(dish.get('reviews', [])))
        dish['photo_url'] = safe_media_url(dish.get('photo_url'))
        menu.append(dish)
    config['menu'] = sorted(menu, key=lambda d: (d.get('sort_order', 100), d.get('name', '')))
    config['restaurant_reviews'] = review_summary(read(directory / 'reviews.json', []))
    config['gallery'] = resolve_gallery(read(directory / 'gallery.json', {}), business, business)
    config['demo_daily_reservations'] = config.get('demo_daily_reservations', []) if business.get('is_demo') else []
    return config


def _integer(value, label):
    if isinstance(value, bool) or str(value).strip() != str(int(str(value))):
        raise ValueError(f'{label} must be a whole number.')
    return int(value)


def quote_dining(config, values, reservations=(), now=None):
    """Select an intact table group and price menu IDs using authoritative prices.

    Production callers must supply committed reservations and perform the same
    check under a transaction before holding tables/food or creating a payment.
    """
    zone = ZoneInfo(config.get('time_zone', 'Asia/Kolkata'))
    now = now or datetime.now(zone)
    try:
        guests = _integer(values.get('guests', ''), 'Guest count')
        start = datetime.strptime(values.get('date', '') + 'T' + values.get('time', ''), '%Y-%m-%dT%H:%M').replace(tzinfo=zone)
    except (ValueError, TypeError):
        raise ValueError('Choose a valid date, arrival time and whole guest count.')
    if not config or not 1 <= guests <= config.get('max_party_size', 20):
        raise ValueError(f"Choose 1–{config.get('max_party_size', 20)} guests.")
    if start.date() > (now + timedelta(days=config.get('advance_days', 30))).date():
        raise ValueError('The selected date is outside the advance booking window.')
    if start < now + timedelta(minutes=config.get('lead_minutes', 60)):
        raise ValueError(f"Reserve at least {config.get('lead_minutes', 60)} minutes before arrival.")
    duration = config.get('duration_minutes', 90)
    end = start + timedelta(minutes=duration)
    clock = lambda text: datetime.strptime(values['date'] + 'T' + text, '%Y-%m-%dT%H:%M').replace(tzinfo=zone)
    if not any(clock(session['opens']) <= start and end <= clock(session['closes'])
               and int((start-clock(session['opens'])).total_seconds() // 60) % config.get('slot_minutes', 30) == 0
               for session in config.get('sessions', [])):
        raise ValueError('Choose an arrival slot within the dining hours.')
    relevant = [r for r in reservations if r.get('date') == values['date']]
    relevant += [{**r, 'date': values['date']} for r in config.get('demo_daily_reservations', [])]
    relevant += [r for r in config.get('blocked_reservations', []) if r.get('date') == values['date']]
    busy = set()
    for reservation in relevant:
        begins = clock(reservation['time'])
        finishes = begins + timedelta(minutes=reservation.get('duration_minutes', duration))
        if start < finishes and begins < end:
            busy.update(reservation.get('table_ids', []))
    tables = {table['id']: table['seats'] for table in config.get('tables', [])}
    options = []
    for option in config.get('seating_options', []):
        ids = option.get('table_ids', [])
        if ids and len(ids) == len(set(ids)) and all(t in tables for t in ids) and not busy.intersection(ids):
            options.append({**option, 'capacity': sum(tables[t] for t in ids)})
    options.sort(key=lambda o: (o['capacity'], len(o['table_ids']), o['id']))
    selected = next((option for option in options if option['capacity'] >= guests), None)
    items = values.get('items', [])
    if not isinstance(items, list) or len(items) > 100:
        raise ValueError('Choose dishes from the menu.')
    dishes = {dish['id']: dish for dish in config.get('menu', [])}
    quantities = {}
    for item in items:
        if not isinstance(item, dict) or item.get('dish_id') not in dishes:
            raise ValueError('A selected dish is no longer on the menu.')
        try:
            quantity = _integer(item.get('quantity', ''), 'Dish quantity')
        except (ValueError, TypeError):
            raise ValueError('Dish quantities must be whole numbers.')
        if quantity < 0:
            raise ValueError('Dish quantities cannot be negative.')
        quantities[item['dish_id']] = quantities.get(item['dish_id'], 0) + quantity
    lines = []
    for dish_id, quantity in quantities.items():
        if quantity == 0:
            continue
        dish = dishes[dish_id]
        sold = sum(item.get('quantity', 0) for r in relevant if r['time'] == values['time'] for item in r.get('items', []) if item.get('dish_id') == dish_id)
        remaining = max(0, dish.get('stock_per_slot', 50) - sold)
        if not dish.get('available', True) or quantity > min(dish.get('max_per_order', 20), remaining):
            raise ValueError(f"{dish['name']} is unavailable in that quantity for this slot.")
        lines.append({'dish_id': dish_id, 'name': dish['name'], 'quantity': quantity,
                      'unit_price_paise': dish['price_paise'], 'total_paise': quantity * dish['price_paise']})
    total = sum(line['total_paise'] for line in lines)
    return {'available': selected is not None, 'guests': guests, 'date': values['date'], 'time': values['time'],
            'end_time': end.strftime('%H:%M'), 'duration_minutes': duration,
            'seating': selected, 'largest_available_group': max((o['capacity'] for o in options), default=0),
            'table_ids': selected['table_ids'] if selected else [], 'items': lines,
            'food_total_paise': total, 'pay_now_paise': total, 'currency': 'INR',
            'prices_include_tax': config.get('payment', {}).get('prices_include_tax', False),
            'payment_mode': 'demo', 'time_zone': config.get('time_zone', 'Asia/Kolkata')}
