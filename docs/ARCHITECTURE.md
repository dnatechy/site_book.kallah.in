# KALLAH Book — shared Web + Flutter architecture

## Runtime

- Python 3.10 + Flask is the only application backend/runtime.
- Jinja2 server-renders public HTML pages for crawlable SEO.
- HTML/CSS preserve the selected reference UI; JavaScript is limited to browser interactions.
- The same Python content/services layer feeds Jinja pages and versioned /api/v1 endpoints.
- Flutter uses the same API and JSON content contracts, rendering the same pages, navigation, filters, profiles and booking preview with native widgets.
- No Node.js, Express, EJS, Bun, React or AI Studio runtime is deployed.

## Single source of truth

- Global configuration and page copy: content/global/*.json, including content/global/pages.json.
- Location registry: content/global/locations.json.
- District records: content/locations/india/tamil-nadu/{city}/city.json.
- Category navigation, filter choices and page copy: {city}/{category}/category.json.
- Business profiles, content, SEO, themes, facilities and professional references: {city}/{category}/{business-id}/data.json.
- Professional profiles, reviews, service menus, venues and weekly schedules: {city}/people/{person-id}/data.json.
- Shared design tokens: shared/design_tokens.json.
- JSON is the content/default configuration source. Never maintain a separate Flutter-only copy of business rules, filters or navigation.

## Request flow

1. A web request reaches Flask; Python loads applicable JSON and server-renders Jinja HTML with SEO metadata.
2. A Flutter request reaches the same Flask content services through /api/v1.
3. Category filters, business visibility, professional schedules, theme and content are resolved in Python.
4. The two clients render the same resolved data using platform-native presentation.

## API contract

See API_CONTRACT.md. The mobile bootstrap endpoint returns site config, JSON-driven page copy/navigation, theme, booking config, locations and selected district navigation. Category endpoints return filter definitions and visual assets. Business/professional endpoints expose the same records shown on the website. Availability returns date windows and service-duration-aware sample start times.

## SEO

- Public web pages are server-rendered; title, description, canonical URL, robots and sitemap are resolved from JSON.
- Demo/sample pages remain noindex and excluded from sitemap.
- Flutter consumes the same content but does not replace server-rendered web SEO.
- Never make the public page depend on a client-only fetch for its primary content.

## Booking phases

- Current demo: JSON weekly schedules and sample availability only. Demo selections are browser-local and not real reservations.
- Live phase: MariaDB is the source of truth for capacity, availability, booking, cancellation and audit history. The API response shape remains stable; the data provider changes from JSON preview to transactional DB queries.
- Never claim a slot is reserved until the server commits it.

## Hosting and branches

- Develop and test on prePublish.
- Publish is the hosting branch; move only reviewed/approved files there.
- MilesWeb Passenger runs the Flask WSGI application.
- Keep secrets, logs, virtual environments and runtime data outside Git.

## Shared filter artwork

`get_category()` resolves `content/global/filter_artwork.json` once per category
load and adds the same atlas coordinates to website and API filter definitions.
`components/filter_choice.html` is reused for every business category. Shared
filter colors are design tokens. Images are optimized static WebP assets; no
image processing or external image service runs on hosting.
