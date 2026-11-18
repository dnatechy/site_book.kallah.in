"use strict";
/* Browser-only demonstration. No server writes, payment, patient data or real capacity. */
(() => {
  const storageKey = "kallah-book:demo-bookings:v1";
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
  const textElement = (tag, value, className = "") => {
    const el = document.createElement(tag);
    el.textContent = String(value);
    if (className) el.className = className;
    return el;
  };
  const localISO = daysFromNow => {
    const now = new Date();
    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + daysFromNow);
    const pad = x => String(x).padStart(2, "0");
    return [d.getFullYear(), pad(d.getMonth() + 1), pad(d.getDate())].join("-");
  };
  const history = document.getElementById("demo-booking-list");
  if (history) {
    function renderHistory() {
      history.replaceChildren();
      const list = read();
      if (!list.length) {
        history.appendChild(textElement("p", "No demo bookings saved on this browser yet.", "notice"));
        return;
      }
      for (const booking of list) {
        const card = document.createElement("article");
        card.className = "demo-history-item";
        card.appendChild(textElement("strong", booking.business || "Demo business"));
        card.appendChild(textElement("p", (booking.professional || "Sample professional") +
          " · " + (booking.date || "") + " · " + (booking.time || "")));
        card.appendChild(textElement("small", (booking.reference || "") + " · DEMO ONLY — NOT CONFIRMED"));
        const cancel = textElement("button", "Remove demo booking", "button button-secondary");
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

  const config = document.getElementById("demo-booking-data");
  if (!config) return;
  let page;
  try { page = JSON.parse(config.textContent); } catch { return; }
  const people = (page.professionals || []).filter(p => p && p.id && p.name);
  const section = document.getElementById("demo-booking-panel");
  const form = document.getElementById("demo-booking-form");
  const personTitle = document.getElementById("demo-selected-person");
  const date = document.getElementById("demo-date");
  const slotList = document.getElementById("demo-slot-list");
  const message = document.getElementById("demo-booking-message");
  if (!section || !form || !date || !slotList) return;

  date.min = localISO(1);
  date.max = localISO(Number(page.days_ahead) > 0 ? Math.min(30, Number(page.days_ahead)) : 14);
  date.value = date.min;
  let person = null;
  let selectedTime = "";

  function renderSlots() {
    slotList.replaceChildren();
    selectedTime = "";
    if (!person) return;
    const saved = read();
    const slots = (person.demo_slots || []).filter(s => s && s.enabled && /^\d\d:\d\d$/.test(s.time));
    for (const slot of slots) {
      const occupiedInThisBrowser = saved.some(b => b.slug === page.slug &&
        b.person_id === person.id && b.date === date.value && b.time === slot.time);
      const button = textElement("button", slot.time + (occupiedInThisBrowser ? " · used" : ""), "demo-slot");
      button.type = "button";
      button.disabled = occupiedInThisBrowser;
      button.addEventListener("click", () => {
        selectedTime = slot.time;
        slotList.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", "false"));
        button.setAttribute("aria-pressed", "true");
        message.textContent = "";
      });
      button.setAttribute("aria-pressed", "false");
      slotList.appendChild(button);
    }
    if (!slotList.children.length) {
      slotList.appendChild(textElement("p", "No example slots configured for this person."));
    }
  }
  document.querySelectorAll("[data-demo-person]").forEach(button => {
    button.addEventListener("click", () => {
      person = people.find(p => p.id === button.dataset.demoPerson);
      if (!person) return;
      personTitle.textContent = "Selected: " + person.name;
      section.hidden = false;
      date.value = localISO(1);
      message.textContent = "";
      renderSlots();
      section.scrollIntoView({behavior: "smooth", block: "start"});
      date.focus({preventScroll: true});
    });
  });
  date.addEventListener("change", renderSlots);
  form.addEventListener("submit", event => {
    event.preventDefault();
    if (!person || !selectedTime || !date.value || date.value < date.min || date.value > date.max) {
      message.textContent = "Select a sample date and time first.";
      return;
    }
    const slots = person.demo_slots || [];
    if (!slots.some(s => s.time === selectedTime && s.enabled === true)) {
      message.textContent = "That sample slot is not selectable.";
      return;
    }
    if (read().some(b => b.slug === page.slug && b.person_id === person.id &&
      b.date === date.value && b.time === selectedTime)) {
      message.textContent = "This sample time was already used in this browser.";
      renderSlots();
      return;
    }
    const value = {
      demo: true, reference: "DEMO-" + Date.now().toString(36).toUpperCase() + "-" +
        Math.random().toString(36).slice(2, 7).toUpperCase(),
      city: page.city, category: page.category, slug: page.slug,
      business: page.business, person_id: person.id, professional: person.name,
      date: date.value, time: selectedTime
    };
    if (!save([value, ...read()])) {
      message.textContent = "Browser storage is blocked. This demo booking could not be saved.";
      return;
    }
    message.textContent = "Demo saved: " + value.reference +
      ". This is NOT a real appointment. No payment was made.";
    renderSlots();
  });
})();
