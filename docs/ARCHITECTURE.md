# KALLAH Book — V3 architecture

- Python 3.10 + Flask/Jinja2 for server-rendered public pages.
- The same content service feeds public pages and versioned /api/v1 read endpoints.
- JSON defaults live under content/global and content/locations.
- Location registry is content/global/locations.json; it maps a public slug to a directory.
- Each location holds category.json and optionally business-ID directories with a data.json.
- Each business data.json combines content, seo and theme overrides.
- Only published=true businesses appear in API, HTML and sitemap. Empty city/category pages are noindex.
- Theme resolution: shared/design_tokens.json → content/global/theme.json → category theme → business theme.
- Future Flutter clients consume /api/v1/config/theme and public business data; render their own native widgets.
- Live booking, payments, availability, notifications and queues belong in MariaDB-backed app/services, not editable JSON files.
- The hosting server must use Dev_v01 only for development; production pulls Publish after approval.
- App startup must remain import-safe: no scheduled jobs, migrations or network calls in create_app.

## Example business record (not production data)

File: content/locations/india/tamil-nadu/trichy/clinics/clinic-2001/data.json

{
  "id": 2001,
  "slug": "example-clinic",
  "name": "Example Clinic",
  "published": false,
  "content": {"heading": "Example Clinic", "summary": "Demonstration only."},
  "seo": {"title": "Example Clinic in {city} | {site}"},
  "theme": {"colors": {"primary": "#E53935"}}
}

Do not publish fictional businesses or doctor profiles. Later, approved admin edits
should reside in MariaDB with revision history; Git JSON supplies defaults and seeds.
