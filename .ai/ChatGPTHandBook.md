# KALLAH Book Development Handbook

Repository: dnatechy/site_book.kallah.in
Development: Dev_v01
Production: Publish; only selective approved runtime files, never wholesale merge.
Hosting: /home/dnatechy/book.kallah.in, Python Passenger 3.10 WSGI.

Tech: Flask + Jinja2, static JSON content + SEO, shared design tokens for future Flutter.
Current implementation:
- District picker on first visit, manual district change, optional browser location.
- Trichy categories + curated quick booking links on the homepage.
- Four category-specific JSON filter sets with easy future additions.
- Category enabled:false blocks all nested HTML/API routes and sitemap entries.
- Professionals are nested beneath each published business in data.json.
- Professional photos accept HTTPS or static paths; booking slots are placeholders only.
- No database, live booking, payment or POS integration in this phase.

Source locations: content/locations/india/tamil-nadu/{city}/{category}/
Business record: {category}/{business-id}/data.json
API: /api/v1, same JSON sources for future Flutter.
Rules: don't fabricate businesses, ratings or slots; keep tests updated;
do not modify Publish without explicit user permission.

## Demo marketplace QA phase

Demo content is enabled in content/global/demo.json. Trichy receives 10 fictional
businesses per category, each with one fictional professional. They include
variable amenities, specialty/service, geo proximity, sample rating and sample
time-slot arrays. Demo website is globally noindex, sitemap has no fake URLs.
Browser-only demo booking flow uses localStorage; not a real reservation or payment.
Never link these sample entries to actual patients, doctors, clinics or businesses.
Production toggle enabled:false must hide every is_demo business.
