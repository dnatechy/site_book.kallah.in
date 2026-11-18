"use strict";
(() => {
  const storageKey = "kallah-book:demo-bookings:v1";
  const userKey = "kallah-book:user:v1";
  const pendingKey = "kallah-book:pending:v1";
  const phoneDigits = value => {
    const digits = String(value || '').replace(/\D/g, '');
    return digits.length === 12 && digits.startsWith('91') ? digits.slice(2) : digits;
  };
  const formatPhone = digits => digits.length > 5 ? `${digits.slice(0, 5)} - ${digits.slice(5)}` : digits;

  const read = () => {
    try {
      const data = JSON.parse(localStorage.getItem(storageKey) || "[]");
      return Array.isArray(data) ? data.filter(x => x && x.demo === true).slice(0, 50) : [];
    } catch { return []; }
  };
  const save = list => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(list.slice(0, 50)));
      return true;
    } catch { return false; }
  };

  const readUser = () => {
    try {
      const u = JSON.parse(localStorage.getItem(userKey) || "null");
      const digits = phoneDigits(u?.phone);
      return u && /^\d{10}$/.test(digits) ? { ...u, phone: '+91' + digits } : null;
    } catch { return null; }
  };
  const saveUser = u => {
    try {
      localStorage.setItem(userKey, JSON.stringify(u));
      return true;
    } catch { return false; }
  };

  const readPending = () => {
    try {
      return JSON.parse(sessionStorage.getItem(pendingKey) || "null");
    } catch { return null; }
  };
  const savePending = p => {
    try {
      if (p) sessionStorage.setItem(pendingKey, JSON.stringify(p));
      else sessionStorage.removeItem(pendingKey);
    } catch { /* ignore */ }
  };

  const textElement = (tag, value, className = "") => {
    const el = document.createElement(tag);
    el.textContent = String(value);
    if (className) el.className = className;
    return el;
  };

  const localDate = daysFromNow => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), now.getDate() + daysFromNow);
  };
  const isoOf = d => {
    const pad = x => String(x).padStart(2, "0");
    return [d.getFullYear(), pad(d.getMonth() + 1), pad(d.getDate())].join("-");
  };
  const dayKeyOf = d => ["sun", "mon", "tue", "wed", "thu", "fri", "sat"][d.getDay()];
  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const tableDayOrder = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
  const dayFullLabels = {
    sun: "Sun",
    mon: "Mon",
    tue: "Tue",
    wed: "Wed",
    thu: "Thu",
    fri: "Friday",
    sat: "Sat"
  };

  const toMinutes = hhmm => {
    const [h, m] = String(hhmm || "00:00").split(":").map(Number);
    return (Number.isFinite(h) ? h : 0) * 60 + (Number.isFinite(m) ? m : 0);
  };
  const formatTime12 = mins => {
    const h24 = Math.floor(mins / 60) % 24;
    const m = mins % 60;
    const ampm = h24 >= 12 ? "PM" : "AM";
    const h12 = h24 % 12 || 12;
    return `${h12}:${String(m).padStart(2, "0")} ${ampm}`;
  };
  const formatTimeShort = mins => {
    const h24 = Math.floor(mins / 60) % 24;
    const m = mins % 60;
    const ampm = h24 >= 12 ? "PM" : "AM";
    const h12 = h24 % 12 || 12;
    return m === 0 ? `${h12} ${ampm}` : `${h12}:${String(m).padStart(2, "0")}`;
  };
  const formatTime24 = mins => {
    const h = Math.floor(mins / 60) % 24;
    const m = mins % 60;
    return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
  };
  const rangesOverlap = (aStart, aDur, bStart, bDur) => aStart < bStart + bDur && bStart < aStart + aDur;

  /* 1. /login page controller */
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    const phoneInput = document.getElementById("login-phone");
    const statusEl = document.getElementById("login-status");
    const updatePhone = () => {
      const raw = phoneInput.value;
      const cursor = phoneInput.selectionStart;
      let before = raw.slice(0, cursor ?? raw.length).replace(/\D/g, '').length;
      const all = raw.replace(/\D/g, '');
      if (all.length === 12 && all.startsWith('91')) before = Math.max(0, before - 2);
      const digits = phoneDigits(raw).slice(0, 10);
      phoneInput.value = formatPhone(digits);
      const count = Math.min(before, digits.length);
      const caret = count + (count > 5 ? 3 : 0);
      phoneInput.setSelectionRange(caret, caret);
      phoneInput.setCustomValidity(digits.length && digits.length !== 10 ? 'Please enter exactly 10 digits.' : '');
      if (statusEl) statusEl.textContent = '';
    };
    phoneInput?.addEventListener('input', updatePhone);
    phoneInput?.addEventListener('paste', event => {
      event.preventDefault();
      const pasted = event.clipboardData?.getData('text') || '';
      const digits = phoneDigits(pasted);
      if (digits.length > 10) {
        if (statusEl) statusEl.textContent = 'Please paste a 10-digit mobile number, optionally with +91.';
        return;
      }
      // A complete number replaces the field; shorter pastes replace the selection.
      if (digits.length === 10) {
        phoneInput.value = digits;
        phoneInput.setSelectionRange(digits.length, digits.length);
      } else phoneInput.setRangeText(digits, phoneInput.selectionStart, phoneInput.selectionEnd, 'end');
      updatePhone();
    });
    phoneInput?.addEventListener('beforeinput', event => {
      const pos = phoneInput.selectionStart;
      if (pos !== phoneInput.selectionEnd) return;
      const backward = event.inputType === 'deleteContentBackward' && pos > 5 && pos <= 8;
      const forward = event.inputType === 'deleteContentForward' && pos >= 5 && pos < 8;
      if (!backward && !forward) return;
      event.preventDefault();
      const digits = phoneDigits(phoneInput.value);
      const index = backward ? 4 : 5;
      phoneInput.value = digits.slice(0, index) + digits.slice(index + 1);
      phoneInput.setSelectionRange(index, index);
      updatePhone();
    });
    const existing = readUser();
    if (existing && phoneInput) {
      phoneInput.value = formatPhone(phoneDigits(existing.phone));
      const radio = loginForm.querySelector(`input[name="channel"][value="${existing.channel}"]`);
      if (radio) radio.checked = true;
    }
    loginForm.addEventListener("submit", event => {
      event.preventDefault();
      const digits = phoneDigits(phoneInput?.value);
      if (!/^\d{10}$/.test(digits)) {
        if (statusEl) statusEl.textContent = "Please enter a valid 10-digit mobile number.";
        phoneInput?.focus();
        return;
      }
      const channel = loginForm.querySelector('input[name="channel"]:checked')?.value || "sms";
      saveUser({ phone: '+91' + digits, channel, verifiedAt: new Date().toISOString() });
      let nextUrl = loginForm.dataset.nextUrl || "/";
      if (!nextUrl.startsWith("/") || nextUrl.startsWith("//")) nextUrl = "/";
      window.location.assign(nextUrl);
    });
    return;
  }

  /* 2. /demo-bookings history page */
  const history = document.getElementById("demo-booking-list");
  if (history) {
    function renderHistory() {
      history.replaceChildren();
      const list = read();
      if (!list.length) {
        history.appendChild(textElement("p", "No bookings saved on this browser yet.", "notice"));
        return;
      }
      for (const booking of list) {
        const card = document.createElement("article");
        card.className = "demo-history-item";
        card.appendChild(textElement("strong", booking.business || "Local place"));
        if (booking.kind === 'room') {
          card.appendChild(textElement('p', `${booking.room_name} · ${(booking.check_in || '').replace('T', ' ')} → ${(booking.check_out || '').replace('T', ' ')} · ${booking.guests} guest(s) · ₹${booking.total_inr}`));
        } else if (booking.kind === 'dining') {
          card.appendChild(textElement('p', `${booking.guests} people · ${booking.date} · ${formatTime12(toMinutes(booking.time))}–${formatTime12(toMinutes(booking.end_time))} · ${booking.seating?.label || 'Group seating'}`));
          for (const item of booking.items || []) card.appendChild(textElement('p', `${item.quantity} × ${item.name} · ₹${(item.total_paise / 100).toFixed(2)}`));
          card.appendChild(textElement('p', booking.payment_status === 'demo_paid' ? `Demo payment ₹${(booking.pay_now_paise / 100).toFixed(2)} · no money charged` : 'Seats only · no payment required'));
        } else {
        const startText = booking.time ? formatTime12(toMinutes(booking.time)) : "";
        const endText = booking.end_time ? ` – ${formatTime12(toMinutes(booking.end_time))}` : "";
        const serviceText = booking.service_label ? ` · ${booking.service_label}` : "";
        card.appendChild(textElement("p", `${booking.professional || "Specialist"} · ${booking.date || ""} · ${startText}${endText}${serviceText}`));
        }
        if (booking.user_phone) {
          card.appendChild(textElement("p", "Mobile: " + booking.user_phone +
            (booking.channel ? " (" + booking.channel.toUpperCase() + ")" : "")));
        }
        card.appendChild(textElement("small", (booking.reference || "") + " · Saved on this device"));
        const cancel = textElement("button", "Cancel booking", "button button-secondary");
        cancel.type = "button";
        cancel.addEventListener("click", () => {
          save(read().filter(item => item.reference !== booking.reference));
          renderHistory();
        });
        card.appendChild(cancel);
        history.appendChild(card);
      }
    }
    renderHistory();
  }

  /* 3. Specialist direct booking page with Weekly Table + Service Duration + Horizontal Morning & Evening Bars */
  const config = document.getElementById("demo-booking-data");
  if (!config) return;
  let page;
  try { page = JSON.parse(config.textContent); } catch { return; }

  const people = (page.professionals || []).filter(p => p && p.id && p.name);
  const person = people.find(p => p.id === page.person_id) || people[0] || null;
  if (!person) return;

  const venues = Array.isArray(page.venues) && page.venues.length
    ? page.venues
    : [{ business_slug: page.slug, business_name: page.business, category_slug: page.category, weekly: {}, enabled_dates: ["today", "tomorrow"], slot_minutes: 15 }];

  const defaultServices = page.default_services || {};
  const servicesMenu = Array.isArray(person.services_menu) && person.services_menu.length
    ? person.services_menu
    : (Array.isArray(defaultServices[page.category]) ? defaultServices[page.category] : []);

  const venueSelect = document.getElementById("venue-select");
  const weeklyListEl = document.getElementById("weekly-schedule-list");
  const dateStripEl = document.getElementById("booking-date-strip");
  const serviceListEl = document.getElementById("service-menu-list");
  const serviceDurationNoteEl = document.getElementById("service-duration-note");
  const calWindowEl = document.getElementById("teams-cal-window");
  const sessionBarsEl = document.getElementById("session-bars-container");
  const slotSummaryEl = document.getElementById("slot-selection-summary");
  const zoomInBtn = document.getElementById("zoom-in");
  const zoomOutBtn = document.getElementById("zoom-out");
  const zoomLabelEl = document.getElementById("zoom-level-label");
  const form = document.getElementById("demo-booking-form");
  const messageEl = document.getElementById("demo-booking-message");
  const loginBar = document.getElementById("login-session-bar");
  const loginBarText = document.getElementById("login-session-text");

  const activeEyebrow = document.getElementById("active-venue-eyebrow");
  const activeAddress = document.getElementById("active-venue-address");
  const activePhone = document.getElementById("active-venue-phone");
  const activeEmail = document.getElementById("active-venue-email");

  if (!form || !dateStripEl || !sessionBarsEl) return;

  const zoomScales = [
    { pxPerMin: 2.0, label: "75%" },
    { pxPerMin: 2.8, label: "100%" },
    { pxPerMin: 3.8, label: "135%" },
    { pxPerMin: 5.0, label: "180%" }
  ];
  let zoomIndex = 1;
  let activeVenue = venues.find(v => v.business_slug === page.slug) || venues[0];
  let selectedDateISO = "";
  let selectedService = servicesMenu[0];
  let selectedTime = "";

  const currentUser = readUser();
  if (currentUser && loginBar && loginBarText) {
    loginBar.hidden = false;
    loginBarText.textContent = `Signed in: ${currentUser.phone} (${currentUser.channel === "whatsapp" ? "WhatsApp" : "SMS"})`;
  }

  function formatWeeklyTableRows(weekly) {
    const rows = [];
    for (const d of tableDayOrder) {
      const wins = weekly?.[d];
      if (!Array.isArray(wins) || !wins.length) continue;
      const morning = wins
        .filter(w => toMinutes(w.start) < 15 * 60)
        .map(w => `${formatTime12(toMinutes(w.start))} – ${formatTime12(toMinutes(w.end))}`)
        .join(", ");
      const evening = wins
        .filter(w => toMinutes(w.start) >= 15 * 60)
        .map(w => `${formatTime12(toMinutes(w.start))} – ${formatTime12(toMinutes(w.end))}`)
        .join(", ");
      rows.push({
        day: dayFullLabels[d] || dayLabelsFromKey(d),
        morning: morning || "—",
        evening: evening || "—"
      });
    }
    return rows;
  }

  function dayLabelsFromKey(k) {
    return k ? k.charAt(0).toUpperCase() + k.slice(1) : "";
  }

  function renderVenueHeader() {
    if (activeEyebrow) activeEyebrow.textContent = activeVenue.business_name;
    if (activeAddress) {
      activeAddress.textContent = activeVenue.area
        ? `${activeVenue.business_name} · ${activeVenue.area}`
        : activeVenue.business_name;
    }
    if (activePhone && activeVenue.phone) {
      activePhone.href = `tel:${String(activeVenue.phone).replace(/\s+/g, "")}`;
      activePhone.title = `Call ${activeVenue.phone}`;
      activePhone.setAttribute("aria-label", `Call ${activeVenue.phone}`);
    }
    if (activeEmail && activeVenue.email) {
      activeEmail.href = `mailto:${activeVenue.email}`;
      activeEmail.title = `Email ${activeVenue.email}`;
      activeEmail.setAttribute("aria-label", `Email ${activeVenue.email}`);
    }
    if (weeklyListEl) {
      weeklyListEl.replaceChildren();
      const rows = formatWeeklyTableRows(activeVenue.weekly);
      if (!rows.length) {
        const tr = document.createElement("tr");
        tr.appendChild(textElement("td", "Daily", "weekly-day-cell"));
        tr.appendChild(textElement("td", "10:00 AM – 2:00 PM", "tabular"));
        tr.appendChild(textElement("td", "—", "weekly-empty-cell"));
        weeklyListEl.appendChild(tr);
      } else {
        for (const r of rows) {
          const tr = document.createElement("tr");
          tr.appendChild(textElement("td", r.day, "weekly-day-cell"));
          tr.appendChild(textElement("td", r.morning, r.morning === "—" ? "weekly-empty-cell" : "tabular"));
          tr.appendChild(textElement("td", r.evening, r.evening === "—" ? "weekly-empty-cell" : "tabular"));
          weeklyListEl.appendChild(tr);
        }
      }
    }
  }

  function isDateEnabled(offset, d) {
    const enabledKeys = Array.isArray(activeVenue.enabled_dates)
      ? activeVenue.enabled_dates
      : ["today", "tomorrow"];
    const tag = offset === 0 ? "today" : offset === 1 ? "tomorrow" : "future";
    if (!enabledKeys.includes(tag)) return false;
    const weekly = activeVenue.weekly || {};
    if (Object.keys(weekly).length > 0) {
      const wins = weekly[dayKeyOf(d)];
      return Array.isArray(wins) && wins.length > 0;
    }
    return true;
  }

  function windowsForDate(d) {
    const weekly = activeVenue.weekly || {};
    const wins = weekly[dayKeyOf(d)];
    if (Array.isArray(wins) && wins.length) return wins;
    if (Object.keys(weekly).length === 0) return [{ start: "10:00", end: "14:00" }];
    return [];
  }

  function getSavedSpans() {
    return read()
      .filter(b =>
        b.city === page.city &&
        b.person_id === person.id &&
        b.date === selectedDateISO &&
        b.time
      )
      .map(b => ({
        start: toMinutes(b.time),
        duration: Number(b.duration_min) > 0 ? Number(b.duration_min) : 15,
        label: b.service_label || "Booked"
      }));
  }

  // Stable demo reservations per person, venue and day; never saved as user bookings.
  function getDemoSpans() {
    const rules = page.booking?.demo_booked_slots;
    if (!rules?.enabled || !selectedDateISO) return [];
    const [y, m, d] = selectedDateISO.split('-').map(Number);
    const wins = windowsForDate(new Date(y, m - 1, d));
    const key = `${page.city}:${person.id}:${activeVenue.business_slug}:${selectedDateISO}`;
    const seed = [...key].reduce((hash, char) => (hash * 31 + char.charCodeAt(0)) >>> 0, 0);
    const offsets = rules.offsets_min || [30, 60, 90];
    const spans = [];
    wins.forEach((win, index) => {
      const start = toMinutes(win.start);
      const end = toMinutes(win.end);
      const duration = Number(rules.duration_min) || 15;
      if (end - start < duration * 2) return;
      const anchor = toMinutes(rules.anchor_time || '10:00');
      const offset = offsets[(seed + index) % offsets.length];
      const first = start <= anchor && anchor + duration <= end
        ? anchor : Math.min(start + offset, end - duration);
      spans.push({ start: first, duration, label: 'Booked (demo)' });
      const extraDuration = Number(rules.extra_duration_min) || 30;
      const extraStart = start + offsets[(seed + index + 1) % offsets.length] + 90;
      if (extraStart + extraDuration <= end && !rangesOverlap(extraStart, extraDuration, first, duration)) {
        spans.push({ start: extraStart, duration: extraDuration, label: 'Booked (demo)' });
      }
    });
    return spans;
  }

  const getOccupiedSpans = () => [...getDemoSpans(), ...getSavedSpans()];

  function isStartValidForWindow(startM, duration, winEnd, savedSpans) {
    if (startM + duration > winEnd) return false;
    return !savedSpans.some(s => rangesOverlap(startM, duration, s.start, s.duration));
  }

  function updateSummary() {
    if (!slotSummaryEl) return;
    if (!selectedDateISO) {
      slotSummaryEl.textContent = "Switch location above to view an active day.";
      slotSummaryEl.classList.remove("is-active");
      return;
    }
    if (!selectedTime) {
      slotSummaryEl.textContent = `Tap any open time on Morning or Evening bar (${selectedService.label} · ${selectedService.duration_min} min).`;
      slotSummaryEl.classList.remove("is-active");
      return;
    }
    const startM = toMinutes(selectedTime);
    const endM = startM + selectedService.duration_min;
    slotSummaryEl.textContent = `Selected: ${formatTime12(startM)} – ${formatTime12(endM)} (${selectedService.label} · ${selectedService.duration_min} min)`;
    slotSummaryEl.classList.add("is-active");
  }

  function renderDateStrip(preferredISO = null) {
    dateStripEl.replaceChildren();
    let firstEnabledISO = "";
    const cells = [];

    for (let offset = 0; offset < Number(page.booking?.availability_window_days || 7); offset++) {
      const d = localDate(offset);
      const iso = isoOf(d);
      const enabled = isDateEnabled(offset, d);
      if (enabled && !firstEnabledISO) firstEnabledISO = iso;
      cells.push({ offset, d, iso, enabled });
    }

    if (preferredISO && cells.some(c => c.iso === preferredISO && c.enabled)) {
      selectedDateISO = preferredISO;
    } else if (!cells.some(c => c.iso === selectedDateISO && c.enabled)) {
      selectedDateISO = firstEnabledISO;
    }

    for (const c of cells) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "date-cell" + (c.enabled ? "" : " is-shaded") + (c.iso === selectedDateISO ? " is-selected" : "");
      btn.disabled = !c.enabled;
      btn.setAttribute("role", "radio");
      btn.setAttribute("aria-checked", c.iso === selectedDateISO ? "true" : "false");
      btn.setAttribute("title", c.enabled ? `Book on ${c.iso}` : "Booking not yet opened for this date");

      btn.appendChild(textElement("span", dayNames[c.d.getDay()], "date-cell-day"));
      btn.appendChild(textElement("strong", String(c.d.getDate()), "date-cell-num tabular"));
      const subLabel = c.offset === 0 ? "Today" : c.offset === 1 ? "Tomorrow" : monthNames[c.d.getMonth()];
      btn.appendChild(textElement("span", subLabel, "date-cell-tag"));

      if (c.enabled) {
        btn.addEventListener("click", () => {
          selectedDateISO = c.iso;
          selectedTime = "";
          if (messageEl) messageEl.textContent = "";
          renderDateStrip(selectedDateISO);
          renderSessionBars();
        });
      }
      dateStripEl.appendChild(btn);
    }
  }

  function renderServiceMenu() {
    if (!serviceListEl) return;
    serviceListEl.replaceChildren();
    if (serviceDurationNoteEl) {
      serviceDurationNoteEl.textContent = `Occupies ${selectedService.duration_min} min on bar`;
    }

    for (const svc of servicesMenu) {
      const btn = document.createElement("button");
      btn.type = "button";
      const isActive = svc.id === selectedService.id;
      btn.className = "service-option-btn" + (isActive ? " is-selected" : "");
      btn.setAttribute("role", "radio");
      btn.setAttribute("aria-checked", isActive ? "true" : "false");
      btn.appendChild(textElement("span", svc.label, "service-option-name"));
      btn.appendChild(textElement("span", `${svc.duration_min} min`, "service-option-dur tabular"));

      btn.addEventListener("click", () => {
        selectedService = svc;
        if (messageEl) messageEl.textContent = "";
        if (selectedDateISO && selectedTime) {
          const [y, m, dd] = selectedDateISO.split("-").map(Number);
          const wins = windowsForDate(new Date(y, m - 1, dd));
          const startM = toMinutes(selectedTime);
          const savedSpans = getOccupiedSpans();
          const matchingWin = wins.find(w => startM >= toMinutes(w.start) && startM < toMinutes(w.end));
          if (!matchingWin || !isStartValidForWindow(startM, svc.duration_min, toMinutes(matchingWin.end), savedSpans)) {
            selectedTime = "";
          }
        }
        renderServiceMenu();
        renderSessionBars();
      });
      serviceListEl.appendChild(btn);
    }
  }

  function buildSessionBar(title, wins, savedSpans, pxPerMin) {
    const card = document.createElement("div");
    card.className = "session-bar-card";

    const head = document.createElement("div");
    head.className = "session-bar-head";
    head.appendChild(textElement("strong", title, "session-bar-title"));

    if (!wins.length) {
      head.appendChild(textElement("span", "Not available", "session-bar-closed"));
      card.appendChild(head);
      card.appendChild(textElement("p", `No ${title.toLowerCase()} visiting hours on this day.`, "session-bar-empty"));
      return card;
    }

    const rangeSummary = wins
      .map(w => `${formatTime12(toMinutes(w.start))} – ${formatTime12(toMinutes(w.end))}`)
      .join(", ");
    head.appendChild(textElement("span", rangeSummary, "session-bar-range tabular"));
    card.appendChild(head);

    const scrollWrap = document.createElement("div");
    scrollWrap.className = "session-bar-scroll";

    const duration = selectedService.duration_min;
    const step = (duration % 15 !== 0 || zoomIndex === zoomScales.length - 1) ? 10 : 15;

    for (const w of wins) {
      const startM = toMinutes(w.start);
      const endM = toMinutes(w.end);
      const totalMins = Math.max(30, endM - startM);
      const trackWidth = Math.round(totalMins * pxPerMin);

      const track = document.createElement("div");
      track.className = "session-bar-track";
      track.style.width = `${trackWidth}px`;

      /* Ruler labels along top */
      const ruler = document.createElement("div");
      ruler.className = "session-ruler";
      for (let t = startM; t <= endM; t += 30) {
        if (t !== startM && t % 30 !== 0) continue;
        const leftPx = Math.round((t - startM) * pxPerMin);
        const tick = textElement("span", formatTimeShort(t), "session-ruler-tick tabular");
        tick.style.left = `${leftPx}px`;
        if (t === endM) tick.classList.add("is-end");
        ruler.appendChild(tick);
      }
      if ((endM - startM) % 30 !== 0) {
        const endTick = textElement("span", formatTimeShort(endM), "session-ruler-tick is-end tabular");
        endTick.style.left = `${trackWidth}px`;
        ruler.appendChild(endTick);
      }
      track.appendChild(ruler);

      /* Interactive horizontal lane */
      const lane = document.createElement("div");
      lane.className = "session-lane";

      for (let t = startM; t < endM; t += step) {
        const segWidthMins = Math.min(step, endM - t);
        const validStart = isStartValidForWindow(t, duration, endM, savedSpans);
        const t24 = formatTime24(t);

        const segBtn = document.createElement("button");
        segBtn.type = "button";
        segBtn.className = "session-tick-btn" + (validStart ? "" : " is-unavailable") + (selectedTime === t24 ? " is-start" : "");
        segBtn.style.left = `${(t - startM) * pxPerMin}px`;
        segBtn.style.width = `${segWidthMins * pxPerMin}px`;
        segBtn.disabled = !validStart;
        segBtn.setAttribute("aria-label", validStart
          ? `Start at ${formatTime12(t)} for ${duration} minutes`
          : `${formatTime12(t)} unavailable for ${duration} minutes`);
        segBtn.title = validStart
          ? `${formatTime12(t)} – ${formatTime12(t + duration)} (${duration} min)`
          : "Exceeds session end or overlaps a booked slot";

        if (t % 30 === 0 || (t === startM)) {
          segBtn.appendChild(textElement("span", formatTimeShort(t), "session-tick-label tabular"));
        }

        if (validStart) {
          segBtn.addEventListener("click", () => {
            selectedTime = t24;
            if (messageEl) messageEl.textContent = "";
            renderSessionBars();
          });
        }
        lane.appendChild(segBtn);
      }

      /* Render already-booked spans on this lane */
      for (const b of savedSpans) {
        if (b.start + b.duration <= startM || b.start >= endM) continue;
        const clampedStart = Math.max(startM, b.start);
        const clampedEnd = Math.min(endM, b.start + b.duration);
        const bookedEl = document.createElement("div");
        bookedEl.className = "session-booked-span";
        bookedEl.style.left = `${(clampedStart - startM) * pxPerMin}px`;
        bookedEl.style.width = `${Math.max(24, (clampedEnd - clampedStart) * pxPerMin)}px`;
        bookedEl.appendChild(textElement("span", "Booked", "session-span-text"));
        lane.appendChild(bookedEl);
      }

      /* Render active extended occupied span for user's clicked start time */
      if (selectedTime) {
        const selStart = toMinutes(selectedTime);
        if (selStart >= startM && selStart + duration <= endM) {
          const spanEl = document.createElement("div");
          spanEl.className = "session-selected-span";
          spanEl.style.left = `${(selStart - startM) * pxPerMin}px`;
          spanEl.style.width = `${Math.round(duration * pxPerMin)}px`;
          spanEl.appendChild(textElement(
            "span",
            `${formatTime12(selStart)} – ${formatTime12(selStart + duration)}`,
            "session-span-text tabular"
          ));
          lane.appendChild(spanEl);
        }
      }

      track.appendChild(lane);
      scrollWrap.appendChild(track);
    }

    card.appendChild(scrollWrap);
    return card;
  }

  function renderSessionBars() {
    sessionBarsEl.replaceChildren();
    const scale = zoomScales[zoomIndex];
    if (zoomLabelEl) zoomLabelEl.textContent = scale.label;
    if (zoomOutBtn) zoomOutBtn.disabled = zoomIndex === 0;
    if (zoomInBtn) zoomInBtn.disabled = zoomIndex === zoomScales.length - 1;

    if (!selectedDateISO) {
      if (calWindowEl) calWindowEl.textContent = "Not visiting on Today/Tomorrow — switch location above";
      sessionBarsEl.appendChild(textElement("p", "No open window at this location for today or tomorrow. Try selecting another hospital above.", "notice"));
      updateSummary();
      return;
    }

    const [y, m, dd] = selectedDateISO.split("-").map(Number);
    const chosenDate = new Date(y, m - 1, dd);
    const wins = windowsForDate(chosenDate);
    if (!wins.length) {
      if (calWindowEl) calWindowEl.textContent = "No slots on this date";
      sessionBarsEl.appendChild(textElement("p", "No visiting hours on this day.", "notice"));
      updateSummary();
      return;
    }

    if (calWindowEl) {
      calWindowEl.textContent = `${selectedService.label} (${selectedService.duration_min} min) — scroll bar & click start time`;
    }

    const savedSpans = getOccupiedSpans();
    if (selectedTime) {
      const start = toMinutes(selectedTime);
      if (!wins.some(w => start >= toMinutes(w.start) &&
        isStartValidForWindow(start, selectedService.duration_min, toMinutes(w.end), savedSpans))) {
        selectedTime = "";
      }
    }
    const morningWins = wins.filter(w => toMinutes(w.start) < 15 * 60);
    const eveningWins = wins.filter(w => toMinutes(w.start) >= 15 * 60);

    sessionBarsEl.appendChild(buildSessionBar("Morning", morningWins, savedSpans, scale.pxPerMin));
    sessionBarsEl.appendChild(buildSessionBar("Evening", eveningWins, savedSpans, scale.pxPerMin));
    updateSummary();
  }

  zoomOutBtn?.addEventListener("click", () => {
    if (zoomIndex > 0) {
      zoomIndex -= 1;
      renderSessionBars();
    }
  });
  zoomInBtn?.addEventListener("click", () => {
    if (zoomIndex < zoomScales.length - 1) {
      zoomIndex += 1;
      renderSessionBars();
    }
  });

  venueSelect?.addEventListener("change", () => {
    const nextVenue = venues.find(v => v.business_slug === venueSelect.value);
    if (!nextVenue) return;
    activeVenue = nextVenue;
    selectedTime = "";
    if (messageEl) messageEl.textContent = "";
    renderVenueHeader();
    renderDateStrip();
    renderServiceMenu();
    renderSessionBars();
  });

  /* Restore pending slot after returning from /login */
  const pending = readPending();
  let preferredISO = null;
  if (pending && pending.personId === person.id) {
    const matchedVenue = venues.find(v => v.business_slug === pending.venueSlug);
    if (matchedVenue) {
      activeVenue = matchedVenue;
      if (venueSelect) venueSelect.value = matchedVenue.business_slug;
    }
    if (pending.serviceId) {
      const matchedSvc = servicesMenu.find(s => s.id === pending.serviceId);
      if (matchedSvc) selectedService = matchedSvc;
    }
    preferredISO = pending.date || null;
    selectedTime = pending.time || "";
    savePending(null);
  }

  renderVenueHeader();
  renderDateStrip(preferredISO);
  renderServiceMenu();
  renderSessionBars();

  form.addEventListener("submit", event => {
    event.preventDefault();
    if (!selectedDateISO || !selectedTime) {
      if (messageEl) messageEl.textContent = "Please select a date, a service type, and click an open start time on the Morning or Evening bar.";
      return;
    }

    const user = readUser();
    if (!user) {
      savePending({
        venueSlug: activeVenue.business_slug,
        personId: person.id,
        date: selectedDateISO,
        serviceId: selectedService.id,
        time: selectedTime
      });
      const nextPath = window.location.pathname + window.location.search;
      window.location.assign("/login?next=" + encodeURIComponent(nextPath));
      return;
    }

    const startM = toMinutes(selectedTime);
    const duration = selectedService.duration_min;
    const savedSpans = getOccupiedSpans();
    const [y, m, dd] = selectedDateISO.split("-").map(Number);
    const wins = windowsForDate(new Date(y, m - 1, dd));
    if (!wins.some(w => startM >= toMinutes(w.start) &&
      isStartValidForWindow(startM, duration, toMinutes(w.end), savedSpans))) {
      if (messageEl) messageEl.textContent = "This time is unavailable or overlaps an existing booking. Please pick another start time.";
      selectedTime = "";
      renderSessionBars();
      return;
    }

    const endTime = formatTime24(startM + duration);
    const value = {
      demo: true,
      reference: "KB-" + Date.now().toString(36).toUpperCase() + "-" + Math.random().toString(36).slice(2, 6).toUpperCase(),
      city: page.city,
      category: activeVenue.category_slug || page.category,
      slug: activeVenue.business_slug,
      business: activeVenue.business_name,
      person_id: person.id,
      professional: person.name,
      date: selectedDateISO,
      time: selectedTime,
      end_time: endTime,
      duration_min: duration,
      service_id: selectedService.id,
      service_label: selectedService.label,
      user_phone: user.phone,
      channel: user.channel
    };

    if (!save([value, ...read()])) {
      if (messageEl) messageEl.textContent = "Browser storage is blocked. Booking could not be saved.";
      return;
    }

    if (messageEl) {
      messageEl.textContent = `Appointment booked (${value.reference}) · ${selectedService.label} (${formatTime12(startM)} – ${formatTime12(startM + duration)}) with ${person.name} at ${activeVenue.business_name} on ${value.date}.`;
    }
    selectedTime = "";
    renderSessionBars();
  });
})();
