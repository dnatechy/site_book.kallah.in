"use strict";
(() => {
  const data = document.getElementById('person-gallery-data');
  const dialog = document.getElementById('person-gallery');
  const viewer = document.getElementById('gallery-viewer');
  if (!data || !dialog || !viewer) return;
  let config;
  try { config = JSON.parse(data.textContent); } catch { return; }
  const albums = config.gallery?.albums || [];
  const tabs = dialog.querySelector('.gallery-album-tabs');
  const panel = document.getElementById('gallery-album-panel');
  const grid = document.getElementById('gallery-masonry');
  const stage = document.getElementById('gallery-viewer-stage');
  const previous = document.getElementById('gallery-previous');
  const next = document.getElementById('gallery-next');
  const zoom = document.getElementById('gallery-zoom');
  let albumIndex = 0, photoIndex = 0, embedScript;
  const element = (tag, cls, text) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text) node.textContent = text;
    return node;
  };
  const instagram = url => {
    try {
      const parsed = new URL(url);
      return parsed.protocol === 'https:' && ['instagram.com', 'www.instagram.com'].includes(parsed.hostname)
        && /^\/(p|reel)\/[A-Za-z0-9_-]+\/$/.test(parsed.pathname) && !parsed.username && !parsed.password;
    } catch { return false; }
  };
  const imageURL = url => {
    if (typeof url !== 'string') return false;
    if (url.startsWith('/static/images/')) {
      try { return !/[\\\s]/.test(url) && !decodeURIComponent(url).includes('..') && !decodeURIComponent(url).includes('\\'); }
      catch { return false; }
    }
    try { const parsed = new URL(url); return parsed.protocol === 'https:' && !parsed.username && !parsed.password; }
    catch { return false; }
  };
  function processEmbeds() {
    if (window.instgrm?.Embeds) { window.instgrm.Embeds.process(); return; }
    if (embedScript) return;
    embedScript = document.createElement('script');
    embedScript.src = 'https://www.instagram.com/embed.js';
    embedScript.async = true;
    embedScript.addEventListener('load', () => window.instgrm?.Embeds?.process());
    embedScript.addEventListener('error', () => { embedScript.remove(); embedScript = null; });
    document.head.append(embedScript);
  }
  function embedPost(item) {
    const wrap = element('div', 'gallery-instagram');
    if (!instagram(item.url)) return wrap;
    const block = element('blockquote', 'instagram-media');
    block.dataset.instgrmPermalink = item.url;
    block.dataset.instgrmVersion = '14';
    const link = element('a', '', 'View post on Instagram ↗');
    link.href = item.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
    block.append(link);
    wrap.append(block, element('p', 'gallery-embed-note', 'Public Instagram post · if unavailable here, open the original.'));
    return wrap;
  }
  function photo(item, large = false) {
    const img = document.createElement('img');
    img.alt = item.caption || `${config.name} · ${albums[albumIndex].title}`;
    img.loading = large ? 'eager' : 'lazy'; img.decoding = 'async';
    img.referrerPolicy = 'no-referrer';
    img.src = imageURL(item.url) ? item.url : '';
    img.addEventListener('error', () => {
      img.hidden = true;
      img.parentNode?.append(element('span', 'gallery-image-error', 'Image unavailable'));
    }, { once: true });
    return img;
  }
  function resetZoom() {
    stage.classList.remove('is-zoomed');
    zoom.textContent = 'Zoom +'; zoom.setAttribute('aria-pressed', 'false');
    stage.scrollTop = 0; stage.scrollLeft = 0;
  }
  function toggleZoom() {
    const image = stage.querySelector('img');
    if (!image || image.hidden) return;
    const active = !stage.classList.contains('is-zoomed');
    stage.style.setProperty('--zoom-width', `${Math.max(image.naturalWidth, image.clientWidth * 2)}px`);
    stage.classList.toggle('is-zoomed', active);
    zoom.textContent = active ? 'Zoom −' : 'Zoom +';
    zoom.setAttribute('aria-pressed', String(active));
  }
  function showPhoto(index) {
    const album = albums[albumIndex], item = album.items[index];
    if (!item) return;
    photoIndex = index; resetZoom(); stage.replaceChildren();
    document.getElementById('gallery-viewer-title').textContent = album.title;
    document.getElementById('gallery-viewer-count').textContent = `${index + 1} / ${album.items.length}`;
    document.getElementById('gallery-viewer-caption').textContent = item.caption || '';
    const original = document.getElementById('gallery-original-link');
    original.href = item.url;
    original.textContent = item.type === 'instagram' ? 'View on Instagram ↗' : 'Open original ↗';
    previous.disabled = index === 0; next.disabled = index === album.items.length - 1;
    zoom.hidden = item.type === 'instagram';
    if (item.type === 'instagram') stage.append(embedPost(item));
    else {
      const surface = element('button', 'gallery-zoom-surface');
      surface.type = 'button'; surface.setAttribute('aria-label', 'Toggle photo zoom');
      surface.append(photo(item, true)); surface.addEventListener('click', toggleZoom); stage.append(surface);
    }
    if (!viewer.open) viewer.showModal();
    if (item.type === 'instagram') processEmbeds();
  }
  function selectAlbum(index, focus = false) {
    if (!albums[index]) return;
    albumIndex = index;
    const album = albums[index];
    [...tabs.children].forEach((tab, i) => {
      tab.setAttribute('aria-selected', String(i === index)); tab.tabIndex = i === index ? 0 : -1;
    });
    if (focus) tabs.children[index].focus();
    panel.setAttribute('aria-labelledby', `gallery-tab-${index}`);
    document.getElementById('gallery-album-title').textContent = album.title;
    document.getElementById('gallery-album-count').textContent = `${album.items.length} moments`;
    document.getElementById('gallery-album-description').textContent = album.description || '';
    grid.replaceChildren();
    album.items.forEach((item, i) => {
      if (item.type === 'instagram') {
        const tile = element('article', 'gallery-social-tile'); tile.append(embedPost(item));
        const expand = element('button', 'gallery-expand-post', 'Expand post ↗');
        expand.type = 'button'; expand.addEventListener('click', () => showPhoto(i)); tile.append(expand); grid.append(tile);
      } else {
        const tile = element('button', `gallery-tile gallery-tile--${item.layout || 'natural'}`);
        tile.type = 'button'; tile.setAttribute('aria-label', `Open photo ${i + 1}: ${item.caption || album.title}`);
        tile.append(photo(item), element('span', 'gallery-tile-overlay', item.caption || 'Take a closer look ↗'));
        tile.addEventListener('click', () => showPhoto(i)); grid.append(tile);
      }
    });
    if (!album.items.length) grid.append(element('p', 'gallery-empty', 'New moments coming soon.'));
    if (album.items.some(item => item.type === 'instagram')) processEmbeds();
  }
  albums.forEach((album, index) => {
    const tab = element('button', 'gallery-album-tab'); tab.type = 'button'; tab.id = `gallery-tab-${index}`;
    tab.setAttribute('role', 'tab'); tab.setAttribute('aria-controls', panel.id);
    tab.append(element('span', '', album.title), element('span', 'gallery-tab-count', String(album.items.length)));
    tab.addEventListener('click', () => selectAlbum(index));
    tab.addEventListener('keydown', event => {
      let target;
      if (event.key === 'ArrowRight') target = (index + 1) % albums.length;
      if (event.key === 'ArrowLeft') target = (index + albums.length - 1) % albums.length;
      if (event.key === 'Home') target = 0;
      if (event.key === 'End') target = albums.length - 1;
      if (target !== undefined) { event.preventDefault(); selectAlbum(target, true); }
    });
    tabs.append(tab);
  });
  document.querySelector('[data-open-gallery]')?.addEventListener('click', () => {
    selectAlbum(albumIndex); dialog.showModal(); document.body.classList.add('gallery-is-open');
  });
  dialog.querySelector('[data-close-gallery]').addEventListener('click', () => dialog.close());
  viewer.querySelector('[data-close-viewer]').addEventListener('click', () => viewer.close());
  dialog.addEventListener('close', () => { document.body.classList.remove('gallery-is-open'); if (viewer.open) viewer.close(); });
  for (const modal of [dialog, viewer]) modal.addEventListener('click', event => {
    if (event.target !== modal) return;
    const box = modal.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) modal.close();
  });
  previous.addEventListener('click', () => showPhoto(photoIndex - 1));
  next.addEventListener('click', () => showPhoto(photoIndex + 1));
  zoom.addEventListener('click', toggleZoom);
  viewer.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft') { event.preventDefault(); showPhoto(photoIndex - 1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); showPhoto(photoIndex + 1); }
  });
})();
