# KALLAH Book — Python migration from AI Studio preview

Source: `mani-baskar/kallah-book-with-AI-Studio` / `sites-preview-2026-11-18`.
Target: `dnatechy/site_book.kallah.in`. Develop on `Dev_v01`; host from `Publish`.

## Directory map

```text
passenger_wsgi.py                  MilesWeb Passenger WSGI entry
app/
  __init__.py                      Flask factory and shared Jinja context
  content.py                       JSON loading, business mapping, SEO and theme
  web/routes.py                    HTML SSR routes and sitemap
  api/routes.py                    Versioned API for browser and Flutter
  services/availability.py         Clinic/salon schedule projection
  dining.py                        Restaurant connected-table and food quote
  rooms.py                         Hotel room rates and inventory quote
  gallery.py                       Shared photo/album loader
  templates/
    base.html                      SINGLE header, nav, footer and metadata
    components/                    Reusable gallery, discovery, hotel rooms
    pages/                         Home, category, business, professional,
                                   restaurant, room, login and demo history
  static/css/                      Shared styles + dining/gallery/room modules
  static/js/                       Presentation controls and demo checkout
  static/images/                   Existing reusable local media
content/
  global/
    theme.json                     ONE authoritative color configuration
    pages.json                     JSON copy for homepage/nav and SEO-visible text
    seo.json                       Search metadata defaults
    booking.json                   Existing booking/availability settings
  locations/india/tamil-nadu/trichy/
    clinics/                       Clinic records
    salons/                        Salon records, albums and professionals
    hotels/business-01/rooms/      Individual JSON room inventory and prices
    restaurants/business-01/
      seating.json                 Tables, connected groups, hours
      menu/*.json                  Item-by-item prices and reviews
      reviews.json                 Restaurant reviews
      gallery.json                 Restaurant albums
shared/design_tokens.json          Geometry/typography token defaults
tests/                              GitHub Actions Flask/API regression tests
```

## API (Flask is shared by web and any future Flutter app)

All paths below are prefixed by `https://book.kallah.in/api/v1`.

| Purpose | Endpoint |
| --- | --- |
| App initialization | `GET /bootstrap?city=trichy` |
| Site configuration | `GET /config/site`, `GET /config/pages`, `GET /config/theme` |
| Discovery | `GET /locations/{city}/{category}/businesses` |
| Individual business | `GET /locations/{city}/{category}/businesses/{slug}` |
| Professional slots | `GET /locations/{city}/{category}/businesses/{slug}/professionals/{id}/availability` |
| Restaurant seating/menu | `GET /locations/{city}/restaurants/businesses/{slug}/dining` |
| Restaurant food and table quote | `POST /locations/{city}/restaurants/businesses/{slug}/dining/quote` |
| Hotel room collection | `GET /locations/{city}/hotels/businesses/{slug}/rooms` |
| Hotel room detail | `GET /locations/{city}/hotels/businesses/{slug}/rooms/{id}` |
| Stay quote | `GET /locations/{city}/hotels/businesses/{slug}/rooms/{id}/quote` |

Python computes published rates, seating eligibility and gallery data. Jinja renders JSON data server-side so crawlers get HTML. Client JavaScript is retained only for UI interactions and demo checkout previews. The same JSON data is exposed to future Flutter apps via the APIs.

## Global theme

Edit `content/global/theme.json` to control `colors.primary`, `secondary`, `background`, `surface`, `ink`, `text`, and `muted`. These are injected as CSS variables on all pages. `allow_scoped_overrides` defaults to `false`; category and business JSON cannot arbitrarily change the brand palette. If an approved category-specific palette is required later, opt in explicitly.

## Deployment

Repository commits on `Publish` do not update MilesWeb automatically without a hosting-side Git pull/deploy hook. On the hosting SSH terminal with the already configured remote:

```bash
cd /home/dnatechy/book.kallah.in
git fetch origin
git checkout Publish
git pull --ff-only origin Publish
mkdir -p tmp
touch tmp/restart.txt
```

Sanity paths: `/api/v1/health`, `/api/v1/bootstrap?city=trichy`, `/trichy/restaurants/demo-restaurant-01`, `/trichy/hotels/demo-hotel-01`. Demo data and pages are intentionally `noindex`.

## Not yet production-bookable

**The quote APIs are read-only**. Demo confirmations remain browser-local: no OTP delivery, live venue availability, transactionally locked reservations, MariaDB writes, trusted payment webhook, or WhatsApp/SMS notifications. Any real booking workflow must introduce authentication, server-side reservation persistence/locking and payment settlement before enabling production charges. Do not call a quote a confirmed booking.
