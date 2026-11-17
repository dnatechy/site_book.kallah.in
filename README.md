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
