# KALLAH Book Development Handbook

Repository: dnatechy/site_book.kallah.in
Reference UI/content source: mani-baskar/kallah-book-with-AI-Studio (main)
Development branch: prePublish
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

- Develop only on prePublish.
- Do not push to Publish without the user's approval.
- Do not deploy directly from the reference repository.
- Keep secrets, .env, logs, virtual environments and user data out of Git.
- Update README, architecture/API docs, tests and this handbook with each significant change.


## 2026-11-18 / AI Studio preview migration
- Source: `mani-baskar/kallah-book-with-AI-Studio` branch `sites-preview-2026-11-18`; target: `dnatechy/site_book.kallah.in` prePublish -> Publish.
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

## 2026-11-18 / source shared UI + theme migration
- Source repo `mani-baskar/kallah-book-with-AI-Studio` commit `bc829fdd` is the reference for the shared business header, contact actions, reviews and global theme tokens.
- `components/business_header.html` handles all four business types with JSON-driven cover, identity, highlights and contact information. Restaurant seating/menu/checkout remains below that common header.
- `components/contact_actions.html` macro is reused by businesses and professionals and preserves dynamic phone/email element IDs.
- `components/reviews.html` provides shared review section/cards across professionals, rooms, restaurants and dish feedback.
- `shared/design_tokens.json` defines global brand/status colors; `content/global/theme.json` chooses `global` or `category` mode. Only category primary/secondary may change. Business/category JSON no longer owns colors.
- Keep Flask SEO SSR and versioned `/api/v1` for Flutter; preserve existing Python booking availability and quote APIs. Do not introduce Node, EJS or another backend.

## 2026-11-19 / filter artwork and current release workflow
- User designated this repository as the source of truth for all future work.
- Develop on `prePublish`; retain `Dev_v01` as historical. Promote to `Publish`
  only after user approval. This filter artwork release was explicitly approved
  for direct publication. Hosting pull/restart is performed by the user.
- Detailed heart/stomach/kidney and other category illustrations live in optimized
  WebP atlases under `app/static/images/filter-artwork/`.
- Shared registry: `content/global/filter_artwork.json`. `get_category()` resolves
  it for both Jinja and API v1, preserving existing filters and API fields.
- Reuse `components/filter_choice.html` for every category. Keep brand/theme
  tokens centralized. Future Flutter clients consume API atlas coordinates.
- Preserve Flask API services, search/pagination/availability and booking truth;
  do not replace hosting application files with the preview runtime.
