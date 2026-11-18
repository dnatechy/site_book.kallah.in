"""Hotel room inventory and stay quotes, independent of people/appointment slots."""
import json
import re
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from .gallery import resolve_gallery, safe_media_url

SLUG = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


def load_rooms(directory, business):
    rooms = []
    if not directory.is_dir():
        return rooms
    for path in sorted(directory.glob('*.json')):
        with path.open(encoding='utf-8') as stream:
            room = json.load(stream)
        if not isinstance(room, dict) or room.get('enabled', True) is False or not SLUG.fullmatch(str(room.get('id', ''))):
            continue
        room['reviews'] = [review for review in room.get('reviews', []) if isinstance(review, dict) and isinstance(review.get('rating'), (int, float)) and not isinstance(review['rating'], bool) and 1 <= review['rating'] <= 5]
        room['review_count'] = len(room['reviews'])
        room['rating'] = round(sum(review['rating'] for review in room['reviews']) / room['review_count'], 1) if room['review_count'] else None
        room['photo_url'] = safe_media_url(room.get('photo_url'))
        room['gallery'] = resolve_gallery(room.get('gallery', {}), room, business)
        room['booking_modes'] = [mode for mode in room.get('booking_modes', ['night']) if mode in ('night', 'hour')]
        if room['booking_modes'] and room.get('inventory', 0) > 0:
            rooms.append(room)
    return rooms


def quote_room(room, values, today=None):
    """Times in this JSON contract are local wall-clock times in Asia/Kolkata."""
    today = today or datetime.now(ZoneInfo(room.get('time_zone', 'Asia/Kolkata'))).date()
    mode = values.get('mode', 'night')
    if mode not in room.get('booking_modes', []):
        raise ValueError('This room does not offer that booking mode.')
    try:
        arrival = date.fromisoformat(values.get('check_in', ''))
        guests = int(values.get('guests', 1))
    except (ValueError, TypeError):
        raise ValueError('Choose a valid check-in date and guest count.')
    if arrival < today:
        raise ValueError('Check-in cannot be in the past.')
    if not 1 <= guests <= room.get('max_guests', 2):
        raise ValueError('Guest count exceeds this room’s capacity.')
    if mode == 'night':
        try:
            departure = date.fromisoformat(values.get('check_out', ''))
        except (ValueError, TypeError):
            raise ValueError('Choose a valid check-out date.')
        units = (departure - arrival).days
        if not 1 <= units <= room.get('max_nights', 30):
            raise ValueError('Check-out must be after check-in, within the maximum stay.')
        start = datetime.combine(arrival, time.fromisoformat(room.get('check_in_time', '14:00')))
        end = datetime.combine(departure, time.fromisoformat(room.get('check_out_time', '11:00')))
        rate = int(room['nightly_rate_inr'])
    else:
        policy = room.get('hourly', {})
        try:
            units = int(values.get('hours', policy.get('min_hours', 2)))
            start = datetime.combine(arrival, time.fromisoformat(values.get('start_time', '')))
        except (ValueError, TypeError):
            raise ValueError('Choose a valid arrival time and number of hours.')
        if not policy.get('min_hours', 2) <= units <= policy.get('max_hours', 12):
            raise ValueError('Choose an allowed hourly duration.')
        end = start + timedelta(hours=units)
        opening = datetime.combine(arrival, time.fromisoformat(policy.get('opens', '06:00')))
        closing = datetime.combine(arrival, time.fromisoformat(policy.get('closes', '22:00')))
        if start < opening or end > closing:
            raise ValueError('The hourly stay must fit inside the room’s day-use hours.')
        rate = int(policy['rate_inr'])
    blocks = room.get('blocked_stays', [])
    overlaps = [block for block in blocks if start < datetime.fromisoformat(block['check_out']) and datetime.fromisoformat(block['check_in']) < end]
    events = []
    for block in overlaps:
        events.extend([(max(start, datetime.fromisoformat(block['check_in'])), 1),
                       (min(end, datetime.fromisoformat(block['check_out'])), -1)])
    active = peak = 0
    for _, delta in sorted(events):
        active += delta
        peak = max(peak, active)
    available = peak < int(room.get('inventory', 1))
    return {'available': available, 'room_id': room['id'], 'mode': mode,
            'check_in': start.isoformat(timespec='minutes'), 'check_out': end.isoformat(timespec='minutes'),
            'units': units, 'rate_inr': rate, 'total_inr': units * rate,
            'guests': guests, 'currency': 'INR', 'time_zone': room.get('time_zone', 'Asia/Kolkata')}
