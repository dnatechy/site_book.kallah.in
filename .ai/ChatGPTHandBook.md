# KALLAH Book Development Handbook

Repository: dnatechy/site_book.kallah.in
Development branch: Dev_v01 (always implement here first).
Production branch: Publish (manual, selective promotion only).
Hosting: /home/dnatechy/book.kallah.in; Passenger WSGI application.

Architecture V3: app (web/api/services/models/templates/static), content
(global and location/category/business JSON), shared design tokens,
database migrations, tests, scripts, docs.

Rules:
1. Keep the public website Python Flask + Jinja2 SSR for SEO.
2. Use a single read layer for HTML and Flutter API content.
3. Business pages use stable IDs and business-specific content/seo/theme in one JSON file.
4. Share theme design tokens with Flutter. Never duplicate booking logic in routes.
5. Store booking, payment, queue and personal data in secure MariaDB, NOT Git JSON.
6. Never publish fictitious businesses or expose private patient data.
7. Add tests and deployment notes for every meaningful change.
8. Never merge or push to Publish without explicit user instruction.

Current task: V3 foundation scaffold on Dev_v01 only. No booking or payment flows yet.
