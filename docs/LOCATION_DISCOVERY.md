# KALLAH Book — JSON-Only Location Discovery

## Website location flow

The root URL is SEO-rendered with Trichy as a default browseable city.
First visit opens the district picker; visitors may choose a district manually or
click "Use my current location" to prompt browser permission. No geolocation
coordinates are sent to the server. Only the chosen district slug is stored in
browser localStorage. Existing choice redirects / to /{district}.

Approximate city-center coordinates + match_radius_km in each city.json decide
whether a visitor is close to a configured service area. This is not a district
boundary detector. If uncertain, ask the visitor to select manually.

District options come from content/global/locations.json and
content/locations/india/tamil-nadu/{district}/city.json. Trichy currently has
4 service categories. Madurai, Coimbatore, Chennai and Salem are selectable
but intentionally show no businesses/categories yet.

## Category enable/disable control

Edit content/locations/india/tamil-nadu/trichy/salons/category.json:
    "enabled": false

With the switch disabled, category cards, quick links, category route,
business routes, API endpoints and sitemap URLs disappear/404, including any
nested professional profiles.

## Filter JSON — no code change for more filters

Example:
    {"key": "parking", "label": "Car parking",
     "type": "toggle", "field": "amenities.parking"}

Supported:
- select with options [{value,label}] and field such as specialties/services/cuisines
- min_number with field such as google_rating (rating range 0..5)
- toggle with Boolean field such as amenities.parking
- proximity for browser-only Near me (currently 10 km)

Filtering is applied by Python to locally published business JSON for both
website and /api/v1; proximity uses only browser geolocation and business.geo.

## Professional profiles beneath business information

Inside the business data.json (single file per business):
{
  "id": 2001,
  "slug": "sample-clinic",
  "name": "Sample Clinic",
  "published": false,
  "content": {"heading": "Sample Clinic", "summary": "Example only"},
  "seo": {"title": "{name} in {city} | {site}"},
  "theme": {"colors": {"primary": "#E53935"}},
  "specialties": ["dermatology"],
  "amenities": {"parking": true},
  "professionals": [{
    "id": "doctor-1",
    "name": "Example Doctor",
    "role": "Dermatologist",
    "specialties": ["dermatology"],
    "photo_url": null,
    "description": "Example only; do not publish fictitious profiles.",
    "enabled": true
  }]
}

The same schema serves salon hairdressers (services instead of specialties).
Professional photos allow HTTPS image URLs (future R2) or /static/images/ paths.
Do not publish fake doctors, ratings, or available booking slots. Booking
controls are disabled until payment, capacity and slot APIs are implemented.

## SEO and safety

- Disabled categories and unpublished businesses never appear in sitemap.
- City/category pages without any published businesses are noindex.
- The original static category/SEO JSON continues as the source of truth.
- Public APIs expose only published business/professional data.
- Any real patient details, bookings or payments must not go in Git JSON files.

## Demo fixtures (November 2026)

The JSON-only preview contains 40 fictional Trichy business entries (10 each clinic,
salon, hotel, restaurant) and 40 fictional professional profiles. Every entry has
is_demo:true and a fixed list of demo_slots on its professional. These are
fictional placeholders, not existing businesses, professionals, verified ratings
or actual appointment availability.

The browser flow demonstrates choosing a person, selecting a date within the
next 14 days and a sample time, storing a demo confirmation in localStorage,
viewing it under /demo-bookings and removing it. No backend writes, patient
information, gateway transactions or real queue operations exist.

content/global/demo.json is an independent master switch. enabled:false hides
all demo businesses everywhere, disables the demo history page and restores
the normal SEO behavior. While enabled, all HTML pages are noindex and the
sitemap does not expose fictional listings. When production business data is
ready, turn this flag off and verify the live sitemap before deployment.
