# KALLAH Book Development Handbook

Repository: dnatechy/site_book.kallah.in
Reference UI/content source: mani-baskar/kallah-book-with-AI-Studio (main)
Development branch: Dev_v01
Hosting branch: Publish — only reviewed, selected files are copied here.
Hosting: /home/dnatechy/book.kallah.in, Python Passenger 3.10 WSGI.

## Non-negotiable architecture

- Python + Flask is the only backend/application runtime.
- Jinja2 server-renders public website pages for SEO.
- HTML/CSS implement the reference UI; JavaScript is only for browser interactions.
- Do not add Node.js, Express, EJS, Bun, React, AI Studio runtime or another backend.
- Web and future Flutter app use the same Python content/services and /api/v1 contract.
- JSON is the single source for site, location, category, filter, business, professional, SEO, theme and schedule data.
- Flutter must not read Git files or keep a second copy of filters/business rules. It consumes the API.

## Reference migration

Use the reference repository's page layouts, UI components, CSS, static images, icons and navigation flow. Re-implement/render them through this Flask application. The reference's Node/AI Studio runtime is not part of KALLAH Book.

## Navigation and features

District picker -> district -> category -> visual filter wizard -> filtered business list -> business profile -> professional profile -> venue/date/service/time selection -> demo preview. Category enable/disable and publication gates apply consistently to HTML, API and sitemap.

The API contract is in docs/API_CONTRACT.md. Keep API v1 additive; use v2 for breaking changes. Update API tests whenever a page capability or shared JSON model changes.

## Booking truth

Current slots are read-only JSON schedule previews. Demo selections are local-only, not real appointments, not capacity reservations and not payments. Live booking must be server-authoritative and MariaDB-backed with authentication, idempotency and atomic slot locking.

## Development and release

- Develop only on Dev_v01.
- Do not push to Publish without the user's approval.
- Do not deploy directly from the reference repository.
- Keep secrets, .env, logs, virtual environments and user data out of Git.
- Update README, architecture/API docs, tests and this handbook with each significant change.


## 2026-11-18 / AI Studio preview migration
- Source: `mani-baskar/kallah-book-with-AI-Studio` branch `sites-preview-2026-11-18`; target: `dnatechy/site_book.kallah.in` Dev_v01 -> Publish.
- Keep Flask SSR and `/api/v1` as the sole shared backend, including future Flutter clients. Never introduce EJS/Node to hosting.
- `app/templates/base.html` owns the shared navigation/header/footer and SEO metadata. Do not fork common headers for restaurants.
- Global theme: `content/global/theme.json`, `allow_scoped_overrides=false` by default; theme is not independently set in category pages.
- Do not regress existing bootstrap/search/pagination/professional availability APIs. Rooms and dining have distinct quote endpoints and JSON content directories.
- Quotes are not reservations. No real OTP/payment/booking persistence until explicit transactional backend work.
- Full maps, contracts, hosting command: `docs/AI_STUDIO_FLASK_MIGRATION.md`.

## 2026-11-18 / professional page parity and regression
- Canonical URLs omit trailing slash; preview links ending in slash get a 308 redirect (and retain query strings).
- Shared header is configured with content/global/pages.json and middle navigation is hidden by default.
- Professional grids use direct children in order: profile, booking, reviews, including on phones.
- +91 mobile input has 5–5 live formatting. This demo login does NOT send a real OTP or message.
- Same-person demo bookings in two venues cannot overlap locally; static illustrative booked ranges are shaded/disabled and returned via the Flask /api/v1 availability response for Flutter.
- Shared reviews are rendered with app/templates/components/review_cards.html.
- Restaurant and hotel bookings are represented in demo-bookings history alongside professional appointments.
- Demo slot/quote APIs are not live capacity reservations and do not persist bookings. Production needs database, authentication, payments and atomic slot locking.
