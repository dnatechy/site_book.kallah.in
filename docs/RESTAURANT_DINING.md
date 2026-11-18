# Group dining and advance food orders

Restaurants use `booking_type: "dining"`. They open directly into party size, date/time, connected seating availability, dish quantities and an upfront food checkout. The former host profiles have been removed. Clinics and salons keep person appointments; hotels keep room reservations.

## Content per restaurant

| Path inside `restaurants/business-01/` | Purpose |
| --- | --- |
| `data.json` | Restaurant identity, contact details and category metadata |
| `seating.json` | Physical tables, allowed connected groups, dining sessions, duration and payment policy |
| `menu/<dish-id>.json` | Dish description, diet, portions, price in integer paise, availability, stock and reviews |
| `reviews.json` | Reviews of the restaurant, separate from dish reviews |
| `gallery.json` | Restaurant and food albums using the existing gallery contract |

The ten demo restaurants have vegetarian menus or mixed menus to match their kitchen preference. Illustrations and sample reviews are explicitly labelled. A sold-out dessert demonstrates unavailable dishes. Average ratings and counts come from each entity's reviews.

`tables` are physical inventory. `seating_options` are approved arrangements of those table IDs. The availability check finds the smallest free arrangement that seats the entire group. Free seats scattered across unrelated tables never count as a connected group. Options share physical IDs, so booking individual tables also blocks any joined arrangement using them. Only the restaurant should configure which tables can be joined.

All times are local Asia/Kolkata. The current policy allows 1–20 guests, 90-minute visits, half-hour arrivals, 30 days ahead and a 60-minute lead time. A visit must fit within a lunch/dinner session. Intervals are half-open: a reservation ending at 14:00 releases its tables for a 14:00 arrival. `blocked_reservations` applies to explicit dates; `demo_daily_reservations` is applied only for demo businesses.

## Python API

`GET /api/v1/locations/trichy/restaurants/businesses/demo-restaurant-01/dining` returns seating rules, menu, dish reviews, restaurant reviews, ratings and albums.

`POST .../dining/quote` accepts JSON:

```json
{"guests":20,"date":"2026-11-19","time":"14:00","items":[{"dish_id":"south-indian-thali","quantity":20},{"dish_id":"fresh-lime-soda","quantity":20}]}
```

It returns the assigned seating option/table IDs, start/end, priced lines, food total and payable-now amount in integer paise. Empty `items` reserves seats without a food preorder in the demo UI. The quote reprices menu IDs from content, aggregates duplicate dish lines and rejects unknown dishes, sold-out items, excessive/fractional/negative quantities and exhausted dish stock for the arrival slot. Prices include tax in this demo; seat reservation fee is zero. The full food amount is due at booking. `quote_dining(..., reservations=...)` accepts committed reservations for server-side availability checks. Quote endpoints are read-only and do not reserve inventory or collect payment.

The browser and compatibility Node renderer use `app/static/js/dining_quote.js`. Python `app/dining.py` remains the backend implementation. The static Sites deployment exports discovery snapshots and runs interactive quotes locally; a Python/Node server provides the POST endpoint.

## Demo checkout

Review party details, table group, food quantities and the full payable amount, then explicitly simulate payment/confirmation. Sign-in drafts preserve the entire dining plan. Saved records use `kind: "dining"`, exact table IDs, priced dish lines and `payment_status: "demo_paid"` (or `no_payment_required` for seats only). History lists food and seating and cancellation releases their local inventory. Reloading and another browser tab use saved demo reservations when checking availability. Storage is browser-local; it is not shared inventory. No real payment, restaurant notification, kitchen ticket or refund occurs.

## Connecting real payment and kitchen operations

The production write flow should atomically hold the selected tables and dish stock with a short expiry, snapshot the authoritative price, then create one gateway order for the full food amount. Use an idempotency key for retries. Confirm the reservation/order and release a scheduled kitchen ticket only after a verified gateway webhook confirms the exact amount/currency and order ID. A browser success callback cannot mark an order paid. Expire or cancel unpaid holds; release capacity on failure. Prevent late/double webhooks from confirming expired holds. A failed payment must never leave confirmed seats or duplicate food orders.

Keep separate records for `dining_reservations`, `reservation_tables`, `preorders`, `preorder_lines`, `payment_attempts` and `refunds`. Link guest submissions to completed visits and separate `restaurant_reviews` from `dish_reviews`. Restaurant acknowledgement, preparation lead time, dietary notes and the cancellation/refund policy must be configured before taking live payments. The current repository deliberately contains no gateway keys and no live money collection.
