# Shared business UI and theme ownership

All business detail pages use `components/business_header.html`. The header owns the breadcrumb, cover, business identity, rating, contact controls and category highlights. Restaurant pages include that same header; their group seating/menu/checkout remain below it. The component reads content, not category-specific CSS or hardcoded cover URLs.

`components/contact_actions.html` contains the reusable phone, email and social controls. Professional pages use it too, preserving the dynamic venue phone/email IDs.

`components/reviews.html` exports `review_section` and `review_list`. Person, hotel room and restaurant reviews share the section/card markup, rating format, empty state, sample label and responsive CSS. Dish feedback reuses `review_list` inside its disclosure. Entity-specific JSON data stays separate. Layout classes select placement only; review appearance lives in `site.css`. Restaurant reviews are a sibling after the dining grid, keeping the sticky order card within its own section.

This migration retains **only Flask/Jinja** as the application renderer. The original EJS components are not deployed. The shared includes/macros are rendered server-side, without a browser framework or extra requests.

## Theme configuration

| File | Ownership |
| --- | --- |
| `shared/design_tokens.json` | Default site palette, permanent brand colors, semantic rating/status colors |
| `content/global/theme.json` | Global palette overrides and explicit `global` / `category` mode |

Current mode is `global`: the same red primary palette applies to discovery, business, person, room and restaurant pages. The KALLAH Book logo uses `brand_ink` / `brand_accent`, independent of the category accent.

To deliberately enable category colors, set `mode` to `category` and configure `category_colors` in the same global theme file:

```json
{"version":2,"mode":"category","colors":{},"category_colors":{"restaurants":{"primary":"#CF6631","secondary":"#FF7043"}}}
```

Only `primary` and `secondary` may vary by category. Brand/status colors stay global. Category and business JSON no longer carry theme overrides. Both Python `get_theme` and compatibility `getTheme` implement this policy, so business details cannot silently change the brand or differ from category discovery.

To change a color everywhere, edit its token/global override rather than adding page CSS literals. Social network icons retain their platform identity colors. The dark photo viewer and disabled/success/error states use distinct UI roles rather than category accents.
