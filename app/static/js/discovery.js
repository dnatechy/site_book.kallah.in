"use strict";
(() => {
  const config = document.getElementById("location-data");
  if (!config) return;
  let districts = [];
  try { districts = JSON.parse(config.textContent || "[]"); } catch { return; }
  const dialog = document.getElementById("location-modal");
  const status = document.getElementById("location-status");
  const select = document.getElementById("district-select");
  const current = document.body.dataset.currentCity || "";
  const entry = document.body.dataset.entryPage === "yes";
  const storeKey = "kallah-book:district";
  const valid = slug => districts.some(item => item.slug === slug);
  const stored = () => { try { return localStorage.getItem(storeKey); } catch { return null; } };
  const save = slug => { try { localStorage.setItem(storeKey, slug); } catch { /* private browser */ } };
  const pick = slug => {
    if (!valid(slug)) return;
    save(slug);
    window.location.assign("/" + encodeURIComponent(slug));
  };
  const show = () => {
    if (dialog && typeof dialog.showModal === "function") {
      if (!dialog.open) dialog.showModal();
    } else { dialog?.setAttribute("open", ""); }
  };
  const close = () => {
    if (dialog && typeof dialog.close === "function") {
      if (dialog.open) dialog.close();
    } else { dialog?.removeAttribute("open"); }
  };
  document.querySelectorAll("[data-open-location]").forEach(button =>
    button.addEventListener("click", show));
  document.getElementById("close-location")?.addEventListener("click", close);
  dialog?.addEventListener("click", event => {
    if (event.target === dialog) close();
  });
  document.getElementById("confirm-district")?.addEventListener("click", () => pick(select.value));
  if (current && valid(current)) save(current);
  else if (entry) {
    const last = stored();
    if (last && valid(last)) window.location.replace("/" + encodeURIComponent(last));
  }
  function distanceKm(lat1, lon1, lat2, lon2) {
    if (![lat1, lon1, lat2, lon2].every(Number.isFinite)) return Infinity;
    const r = Math.PI / 180;
    const a = Math.sin((lat2 - lat1) * r / 2) ** 2 +
      Math.cos(lat1 * r) * Math.cos(lat2 * r) * Math.sin((lon2 - lon1) * r / 2) ** 2;
    return 12742 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }
  const requestLocation = (ok, error) => {
    if (!navigator.geolocation) return error();
    navigator.geolocation.getCurrentPosition(pos => ok(pos.coords.latitude, pos.coords.longitude),
      error, { enableHighAccuracy: false, timeout: 10000, maximumAge: 180000 });
  };
  document.getElementById("use-my-location")?.addEventListener("click", () => {
    status.textContent = "Finding your district...";
    requestLocation((lat, lng) => {
      const nearest = districts.map(city => ({
        city, km: distanceKm(lat, lng, city.geo?.lat, city.geo?.lng)
      })).sort((a, b) => a.km - b.km)[0];
      if (nearest && nearest.km <= (nearest.city.geo?.match_radius_km || 35)) {
        pick(nearest.city.slug);
      } else { status.textContent = "Please select a district manually."; }
    }, () => { status.textContent = "Location unavailable. Please choose a district."; });
  });

  const near = document.querySelector("[data-near-me]");
  if (!near) return;
  const cards = [...document.querySelectorAll(".business-card")];
  const notice = document.getElementById("near-me-status");
  const count = document.getElementById("result-count");
  const rangeKm = 10;
  const update = () => {
    if (!near.checked) {
      cards.forEach(card => card.hidden = false);
      count.textContent = cards.length + " places found";
      notice.textContent = "";
      return;
    }
    notice.textContent = "Checking nearby places...";
    requestLocation((lat, lng) => {
      let shown = 0;
      for (const card of cards) {
        const match = card.hasAttribute("data-lat") && card.hasAttribute("data-lng") &&
          distanceKm(lat, lng, Number(card.dataset.lat), Number(card.dataset.lng)) <= rangeKm;
        card.hidden = !match;
        if (match) shown++;
      }
      count.textContent = shown + " places within " + rangeKm + " km";
      notice.textContent = shown ? "" : "No places with location coordinates found nearby.";
    }, () => {
      near.checked = false;
      notice.textContent = "Allow location access to use Near me.";
    });
  };
  near.addEventListener("change", update);
  if (near.checked) update();
})();
