"""Shared schedule-to-slot projection for Web and Flutter API clients.

This is a read-only schedule preview. It does not reserve capacity or persist bookings.
The live implementation will replace the JSON schedule source with a transactional
MariaDB availability repository while keeping the API response contract stable.
"""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _timezone(config):
    try:
        return ZoneInfo(config.get("timezone", "Asia/Kolkata"))
    except (TypeError, ValueError):
        return ZoneInfo("Asia/Kolkata")


def _parse_time(value):
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        return None
    try:
        hour, minute = int(value[:2]), int(value[3:])
    except ValueError:
        return None
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        return None
    return hour * 60 + minute


def _format_time(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _normalise_windows(raw_windows):
    windows = []
    if not isinstance(raw_windows, list):
        return windows
    for raw in raw_windows:
        if not isinstance(raw, dict):
            continue
        start, end = _parse_time(raw.get("start")), _parse_time(raw.get("end"))
        if start is None or end is None or end <= start:
            continue
        windows.append({"start": _format_time(start), "end": _format_time(end)})
    return sorted(windows, key=lambda item: item["start"])


def _service_menu(person, booking_config):
    defaults = booking_config.get("services_menu_defaults", {})
    menu = person.get("services_menu") or defaults.get(person.get("category"), [])
    return [item for item in menu if isinstance(item, dict) and item.get("id")]


def _demo_booked_spans(config, context, venue, iso_date, windows):
    """Deterministic illustrative reservations, never live capacity."""
    rules = config.get("demo_booked_slots", {})
    if not isinstance(rules, dict) or rules.get("enabled") is not True:
        return []
    offsets = rules.get("offsets_min") or [30, 60, 90]
    if not isinstance(offsets, list):
        return []
    offsets = [value for value in offsets if isinstance(value, int) and 0 <= value <= 480]
    if not offsets:
        return []
    duration = rules.get("duration_min", 15)
    extra_duration = rules.get("extra_duration_min", 30)
    if not isinstance(duration, int) or not 5 <= duration <= 120:
        return []
    if not isinstance(extra_duration, int) or not 5 <= extra_duration <= 120:
        return []
    key = ":".join((context.get("city_slug", ""), context.get("person_id", ""),
                    venue.get("business_slug", ""), iso_date))
    seed = 0
    for char in key:
        seed = (seed * 31 + ord(char)) & 0xFFFFFFFF
    anchor = _parse_time(rules.get("anchor_time", "10:00"))
    spans = []
    for index, window in enumerate(windows):
        start, end = _parse_time(window["start"]), _parse_time(window["end"])
        if end - start < duration * 2:
            continue
        offset = offsets[(seed + index) % len(offsets)]
        first = (anchor if anchor is not None and start <= anchor
                 and anchor + duration <= end else min(start + offset, end - duration))
        candidates = [(first, duration)]
        extra_start = start + offsets[(seed + index + 1) % len(offsets)] + 90
        if (extra_start + extra_duration <= end and
                not (extra_start < first + duration and first < extra_start + extra_duration)):
            candidates.append((extra_start, extra_duration))
        for begins, length in candidates:
            spans.append({"start": _format_time(begins), "end": _format_time(begins + length),
                          "duration_min": length, "label": "Booked (demo)"})
    return spans


def build_availability(person, venue, booking_config, start_date=None, days=7, service_id=None,
                       demo_context=None):
    """Return date windows and valid start times for the selected service."""
    if not isinstance(days, int) or not 1 <= days <= 14:
        raise ValueError("days must be between 1 and 14.")
    timezone = _timezone(booking_config)
    today = datetime.now(timezone).date()
    if start_date:
        try:
            first_day = date.fromisoformat(start_date)
        except (TypeError, ValueError):
            raise ValueError("date/from must use YYYY-MM-DD format.")
    else:
        first_day = today
    if first_day < today:
        raise ValueError("Past dates cannot be requested.")

    services = _service_menu(person, booking_config)
    selected_service = None
    if service_id:
        selected_service = next((item for item in services if item.get("id") == service_id), None)
        if selected_service is None:
            raise ValueError("The requested service_id is not available for this professional.")
    elif services:
        selected_service = services[0]

    try:
        duration = int((selected_service or {}).get(
            "duration_min", booking_config.get("default_service_duration_min", 15)))
    except (TypeError, ValueError):
        duration = int(booking_config.get("default_service_duration_min", 15))
    if not 5 <= duration <= 480:
        raise ValueError("The selected service duration is invalid.")

    try:
        step = int(booking_config.get("slot_step_minutes", 15))
    except (TypeError, ValueError):
        step = 15
    if not 5 <= step <= 60:
        step = 15

    weekly = venue.get("weekly") if isinstance(venue.get("weekly"), dict) else {}
    enabled_dates = venue.get("enabled_dates")
    if not isinstance(enabled_dates, list):
        enabled_dates = ["today", "tomorrow"]
    fallback = booking_config.get("default_windows", [{"start": "10:00", "end": "14:00"}])

    day_results = []
    for offset in range(days):
        current = first_day + timedelta(days=offset)
        iso_date = current.isoformat()
        day_key = WEEKDAYS[current.weekday()]
        tag = "today" if current == today else "tomorrow" if current == today + timedelta(days=1) else "future"
        date_allowed = tag in enabled_dates or iso_date in enabled_dates
        raw_windows = weekly.get(day_key, []) if weekly else fallback
        windows = _normalise_windows(raw_windows)
        is_open = date_allowed and bool(windows)
        booked_spans = (_demo_booked_spans(booking_config, demo_context, venue, iso_date, windows)
                        if is_open and demo_context else [])
        slots = []
        if is_open:
            for window in windows:
                start, end = _parse_time(window["start"]), _parse_time(window["end"])
                cursor = start
                while cursor + duration <= end:
                    blocked = any(
                        cursor < _parse_time(b["end"]) and
                        _parse_time(b["start"]) < cursor + duration
                        for b in booked_spans
                    )
                    slots.append({
                        "start": _format_time(cursor),
                        "end": _format_time(cursor + duration),
                        "duration_min": duration,
                        "available": not blocked,
                        "source": "demo_booked" if blocked else "json_schedule",
                    })
                    cursor += step
        day_results.append({
            "date": iso_date,
            "weekday": day_key,
            "day_offset": (current - today).days,
            "enabled": is_open,
            "windows": windows if date_allowed else [],
            "booked_spans": booked_spans,
            "slots": slots,
        })

    return {
        "timezone": booking_config.get("timezone", "Asia/Kolkata"),
        "date_from": first_day.isoformat(),
        "days": day_results,
        "service": selected_service,
        "services": services,
        "slot_step_minutes": step,
        "slot_minutes": venue.get("slot_minutes", step),
        "venue": {
            "business_slug": venue.get("business_slug"),
            "business_name": venue.get("business_name"),
            "category_slug": venue.get("category_slug"),
            "area": venue.get("area"),
            "address": venue.get("address"),
            "phone": venue.get("phone"),
            "email": venue.get("email"),
            "weekly": weekly,
            "enabled_dates": enabled_dates,
        },
        "capacity_is_live": False,
        "booking_is_persistent": False,
        "demo_booked_spans_are_sample": bool(demo_context),
    }
