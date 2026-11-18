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


def build_availability(person, venue, booking_config, start_date=None, days=7, service_id=None):
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
        slots = []
        if is_open:
            for window in windows:
                start, end = _parse_time(window["start"]), _parse_time(window["end"])
                cursor = start
                while cursor + duration <= end:
                    slots.append({
                        "start": _format_time(cursor),
                        "end": _format_time(cursor + duration),
                        "duration_min": duration,
                        "available": True,
                        "source": "json_schedule",
                    })
                    cursor += step
        day_results.append({
            "date": iso_date,
            "weekday": day_key,
            "day_offset": (current - today).days,
            "enabled": is_open,
            "windows": windows if date_allowed else [],
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
    }
