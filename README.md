# KALLAH Book

Python Flask + Jinja2 booking/discovery foundation for https://book.kallah.in.
Branch policy: **Dev_v01** for development; **Publish** only for approved hosting files.

## Local development

Python 3.10+:

    python -m venv .venv
    python -m pip install -r requirements-dev.txt
    python -m flask --app "app:create_app" run --debug
    python -m pytest -q

Windows helper: scripts/windows/run_dev.ps1.

## Available public routes

- / — landing page
- /trichy — city categories
- /trichy/clinics — category page (noindex until real businesses are published)
- /trichy/clinics/{business-slug} — business page from published data.json
- /api/v1/health
- /api/v1/config/theme
- /api/v1/locations
- /api/v1/locations/trichy/categories
- /api/v1/locations/trichy/clinics/businesses
- /api/v1/locations/trichy/clinics/businesses/{business-slug}
- /robots.txt and /sitemap.xml

SEO, themes, layouts and content are sourced from shared JSON and location JSON;
business-specific content/SEO/theme live together in each business data.json.
Booking, payment, live queue and POS integration are not yet implemented.

## GitHub SSH / MilesWeb

Use the existing shared SSH identity on MilesWeb; **do not create a new key**.
Alias github-milesweb is configured in ~/.ssh/config for github.com and uses
~/.ssh/id_ed25519_github_common. Test:

    ssh -T git@github-milesweb

Repository remote:

    git@github-milesweb:dnatechy/site_book.kallah.in.git

Hosting checkout is /home/dnatechy/book.kallah.in and tracks Publish only:

    cd /home/dnatechy/book.kallah.in
    git switch Publish
    git pull --ff-only origin Publish

Do not push development directly to Publish. No runtime secrets, logs or user data in Git.
See docs/ARCHITECTURE.md and scripts/hosting/README.md.

## Static dummy marketplace preview

- Demo flag: content/global/demo.json, enabled=true. Disable it to hide all demo businesses.
- Trichy includes 10 fictional businesses per category and multiple fictional professionals:
  40 sample businesses and 100 sample professional profiles (3 per clinic/salon, 2 per hotel/restaurant).
- All sample businesses show an obvious DEMO label, use simulated rating scores,
  and are excluded from indexing/sitemap while demo mode is active.
- Flow: home -> select district -> category -> visual filters -> business profile ->
  professional profile -> venue/date/service/time selection -> local demo preview -> My bookings.
- Demo bookings are stored only in that browser's localStorage. There is no server booking,
  capacity reservation, payment, message or notification. No personal data is requested.
- Business and professional photos use the same JSON media fields; HTTPS URLs and approved static assets are supported.

## Reference UI migration and Flutter API parity

- UI/navigation/assets are migrated from mani-baskar/kallah-book-with-AI-Studio; its Node/AI Studio runtime is excluded.
- Flask/Jinja2 renders the public pages. JavaScript is limited to browser interactions.
- Web and future Flutter clients share the same Python content/services and JSON source of truth.
- API base: https://book.kallah.in/api/v1. Start with GET /bootstrap?city=trichy.
- Business lists support JSON-defined filters, search, sorting, pagination and near-me coordinates.
- Professional availability returns date windows and service-duration-aware sample start times.
- Full API request/response contract: docs/API_CONTRACT.md. Architecture: docs/ARCHITECTURE.md.
- Current availability is a read-only JSON preview; no server-side reservation, slot locking or payment is implemented.

To remove all dummy data from public display before launch:
edit content/global/demo.json and set enabled:false; the JSON fixtures can
remain in Git for QA without being displayed or indexed.
