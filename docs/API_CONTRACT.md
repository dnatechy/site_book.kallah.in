# KALLAH Book API Contract — v1

The public website and future Flutter app share the same Flask content services and JSON records. The website renders HTML; Flutter renders native widgets. Neither client owns a separate content database or a second implementation of business rules.

Base URL: https://book.kallah.in/api/v1

Every successful response includes api_version: "v1". API errors return JSON with an error object and an HTTP status code. Asset paths beginning with /static/ are relative to the site origin supplied by site.url.

## App startup

GET /bootstrap?city=trichy

One-call startup payload:
- site: brand, canonical site URL and language
- pages: JSON-driven home-page copy, navigation labels and location-picker content
- theme: shared design tokens and global theme
- booking: timezone, slot interval, demo settings and service defaults
- locations: enabled districts
- selected_location: selected district, enabled categories and quick links
- demo_mode: whether sample fixtures are visible

The city query is optional and defaults to trichy.

Configuration endpoints:
- GET /config/site
- GET /config/pages
- GET /config/theme
- GET /config/booking
- GET /locations

## Discovery and navigation

- GET /locations/{city}: district landing data, categories and quick links
- GET /locations/{city}/categories: enabled categories for the district
- GET /locations/{city}/{category}: category page configuration, visual filter wizard and theme
- GET /locations/{city}/{category}/businesses: filtered, searchable and paginated business cards
- GET /locations/{city}/{category}/businesses/{business}: business profile and professionals
- GET /locations/{city}/{category}/businesses/{business}/professionals: professionals at the selected business
- GET /locations/{city}/{category}/businesses/{business}/professionals/{person}: professional profile, venues, reviews and service menu
- GET /locations/{city}/{category}/businesses/{business}/professionals/{person}/availability: date windows and sample start times

City and category slugs are the same slugs used in website URLs. A disabled city/category or unpublished business returns HTTP 404 in both Web and API.

## Business list query parameters

JSON-defined filters:
- Clinics: specialty, rating, parking, accessible
- Salons: service, rating, AC, parking
- Hotels: diet, type, cuisine, rating, Wi-Fi, parking
- Restaurants: diet, cuisine, dish, rating, AC, parking

The exact filter keys/options always come from the category JSON response. Flutter must render controls from that response, not hard-code a separate filter list.

Other parameters:
- q: text search across business name, area, address, description, services and professionals
- sort: name_asc (default), name_desc, rating_desc, featured or distance_asc
- page: 1-based page number (default 1)
- per_page: 1–100 (default 20)
- near-me=1&lat=10.79&lng=78.70&radius_km=10: distance filtering; both coordinates required; default radius is 10 km

The response includes businesses, filters, total, pagination, applied_filters, search, sort and demo_mode.

## Professional and availability

Example request:

    GET /locations/trichy/clinics/businesses/demo-clinic-01/professionals/demo-clinics-person-01/availability?venue=demo-clinic-01&days=7&service_id=consultation

Parameters:
- venue: selected practice/business location; defaults to the current page business
- date: return one date
- from plus days: return a date window (1–14 days; default 7)
- service_id: service whose duration determines valid start times

The response includes selected service, service menu, venue schedule, date windows, open/closed state and start/end times. Web and Flutter use this contract for the date strip, service selector, weekly table and time bars.

Current-phase limit:
- capacity_is_live is false
- booking_is_persistent is false
- schedules are read-only JSON previews
- website demo selections remain in browser localStorage
- no real appointment, reservation, cancellation, payment or message is created

Do not present a demo slot as reserved or confirmed.

## Future live booking contract

When authentication and MariaDB booking tables are implemented, keep the availability response shape and add authenticated endpoints:

- POST /auth/otp/request
- POST /auth/otp/verify
- POST /bookings (idempotency key; server rechecks capacity and atomically reserves)
- GET /bookings
- GET /bookings/{booking_id}
- POST /bookings/{booking_id}/cancel

These routes are planned, not implemented. Do not add a client-side fake success path. Live availability, slot locking, booking status, cancellation, payments and notifications must be server-authoritative.

## Compatibility rules

- Existing website routes and JSON content paths remain canonical.
- Additive response fields are allowed within v1; do not silently rename fields.
- Breaking response changes require /api/v2.
- Flutter must not read repository files directly; it consumes this API.
- No Node.js, Express, EJS, Bun, React or AI Studio runtime is part of this deployment.
