# Hotels book rooms, not people

Hotel business JSON uses `booking_type: "rooms"` and has no people IDs. The former hotel host records have been removed. Clinics, salons and restaurants keep their existing professional booking flow.

Each hotel owns a `rooms/` directory next to its `data.json`:

```text
content/locations/india/tamil-nadu/trichy/hotels/business-01/rooms/standard-ac.json
content/locations/india/tamil-nadu/trichy/hotels/business-01/rooms/deluxe-room.json
```

Each room JSON holds its own ID, name, description, photo URL, album configuration, bed, size, guest capacity, amenities, inventory, nightly rate, check-in/out times, and allowed booking modes. Demo room pictures are illustrative external references; replace them with the actual property's room photographs.

`booking_modes: ["night"]` offers date-based overnight stays. Add `"hour"` only for rooms that permit hourly/day-use rentals and configure:

```json
{
  "booking_modes": ["night", "hour"],
  "nightly_rate_inr": 1900,
  "check_in_time": "14:00",
  "check_out_time": "11:00",
  "max_nights": 30,
  "time_zone": "Asia/Kolkata",
  "hourly": {
    "rate_inr": 320,
    "min_hours": 2,
    "max_hours": 8,
    "opens": "06:00",
    "closes": "22:00"
  },
  "inventory": 1,
  "blocked_stays": [
    {"check_in": "2026-11-20T14:00", "check_out": "2026-11-22T11:00"}
  ]
}
```

All timestamps represent local wall-clock times in the configured time zone. Availability uses half-open intervals: a stay ending exactly when another begins does not overlap. Nightly and hourly stays consume the same room inventory. Invalid/past dates, invalid guest counts, hourly stays outside the permitted hours, unsupported modes and overlapping full inventory are rejected. For multiple units, simultaneous occupancy is counted rather than counting all reservations in a date range.

## Python routes and API

- Page: `/<city>/hotels/<hotel>/rooms/<room-id>`.
- Room list: `GET /api/v1/locations/<city>/hotels/businesses/<hotel>/rooms`.
- Room detail and gallery: `GET /api/v1/locations/<city>/hotels/businesses/<hotel>/rooms/<room-id>`.
- Validated quote: `GET .../rooms/<room-id>/quote?mode=night&check_in=2026-11-23&check_out=2026-11-25&guests=2`.
- Hourly quote: `GET .../rooms/<room-id>/quote?mode=hour&check_in=2026-11-23&start_time=10:00&hours=3&guests=1`.

`app/rooms.py` is the Python source of truth for room loading and quotes. The retained Node preview renders the same room JSON; the validated quote endpoint is provided by Flask. Future app clients should use the Python APIs.

The Sites copy is a static demo: it exports room list/detail snapshots and computes displayed demo quotes in the browser. Reservations remain in browser storage, share the existing My bookings/cancellation flow, and preserve selected stay details across the mobile sign-in page. They are not shared between visitors/devices. Production booking requires authenticated API writes and an atomic inventory check in the database; none of the demo flow charges money or sends messages.

## Room reviews

Each room JSON owns a `reviews` array of `{ "author": "Guest name", "rating": 5, "comment": "Room feedback", "date": "2026-11-12" }`. Keep reviews scoped to the room, not a hotel host. Python and the compatibility renderer derive `rating` and `review_count` from valid ratings (1–5); those fields also appear in room list/detail APIs. Cards and room pages display the summary. An empty array shows “No reviews for this room yet.”

The seeded hotels contain explicitly labelled sample guest reviews. Room pages place reviews beneath the room overview on desktop and after the booking card on mobile. This is content-driven display; collecting authenticated, stay-linked guest submissions will require a backend write endpoint.
