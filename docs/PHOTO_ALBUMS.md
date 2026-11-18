# Person photo albums

The person detail API returns `professional.gallery`; hotel room detail returns `room.gallery`. The web page and a future Flutter client can consume the same albums and media URLs. The static Sites preview includes the same metadata at build time.

## Where to maintain albums

Create `content/locations/india/tamil-nadu/<city>/people/<person-id>/gallery.json`.
Use that person's existing directory, independently of the clinic/salon they visit.
An album manifest is optional. Demo profiles fall back to `content/global/gallery.json`; this fallback is disabled when demo mode is off.

```json
{
  "version": 1,
  "albums": [
    {
      "id": "studio",
      "title": "The studio",
      "source": "folder",
      "folder": "my-person/studio"
    },
    {
      "id": "portfolio",
      "title": "My work",
      "source": "items",
      "items": [
        {
          "type": "image",
          "url": "/static/images/galleries/my-person/work/photo-01.jpg",
          "caption": "A recent look",
          "layout": "portrait"
        },
        {
          "type": "image",
          "url": "https://your-image-host.example/photos/look-02.jpg",
          "caption": "Hosted on my own website",
          "layout": "landscape"
        }
      ]
    },
    {
      "id": "instagram",
      "title": "Instagram",
      "source": "items",
      "items": [
        {
          "type": "instagram",
          "url": "https://www.instagram.com/p/REPLACE_WITH_REAL_POST_CODE/",
          "caption": "My public Instagram post"
        }
      ]
    }
  ]
}
```

The URLs above are placeholders for your own real content. The example is documentation, not live gallery data.

## Folder mode

For `folder: "my-person/studio"`, put the actual pictures in:

`app/static/images/galleries/my-person/studio/`

Files are sorted by name; use `01-entrance.jpg`, `02-styling.jpg`, and so on to control order. JPG, JPEG, PNG, WebP, AVIF and GIF are supported. Each album is limited to 80 items and each person to 12 albums. Nested folder components must be lowercase slugs. Directory traversal and files escaping the gallery directory are rejected.

The included `salons-person-03-3/gallery.json` demonstrates a real folder album using existing demo photos. Its Inspiration album demonstrates direct external image links and labels those photographs as external references, not the stylist's work.

## Direct image mode

Provide the actual HTTPS image URL, not an ordinary webpage URL. The browser loads that URL directly in an image element; the application never fetches, downloads, rehosts or proxies the remote image. The owner of the source website must permit embedding; deleted URLs and hotlink restrictions show an unavailable-image state. Local static image URLs are also accepted. Optional layouts are `natural` (default, preserving the source proportions), `portrait`, `landscape` and `square`.

## Instagram mode

Use an actual public `/p/<code>/` or `/reel/<code>/` permalink. Tracking parameters are removed. The page builds Instagram's standard blockquote placeholder and loads `https://www.instagram.com/embed.js` only when an album containing Instagram posts is opened. It does not scrape post HTML, extract image CDN URLs, store Instagram media, or strip Instagram attribution. No Meta credentials are needed for this browser embed integration.

An Instagram carousel remains a native Instagram post with its own controls. Our lightbox's previous/next controls navigate between album items (images or posts); it cannot individually extract/zoom photos inside an Instagram carousel. If Instagram blocks embedding or the post is private/deleted/embeds-disabled, the original post link remains available. No real person-specific Instagram post was supplied, so the sample Instagram albums are intentionally empty until real permalinks are added.

## Implementation

- Python resolver: `app/gallery.py`; attached in `app/content.py:get_professional`.
- Retained JavaScript renderer compatibility: `src/gallery.js`.
- Accessible dialogs, keyboard album tabs, next/previous, zoom/pan, Escape and focus restoration: `app/static/js/gallery.js`.
- Mixed portrait/landscape masonry: `app/static/css/gallery.css`.
- Source data stays JSON; images stay in the static folder or at their original external URL.

Python hosting reads updated JSON/files on subsequent page requests. For this static Sites preview, rebuild and publish after editing content.
