"use strict";
(() => {
  const data = document.getElementById('room-booking-data');
  if (!data) return;
  const page = JSON.parse(data.textContent), room = page.room;
  const form = document.getElementById('room-booking-form');
  const arrival = document.getElementById('room-check-in'), departure = document.getElementById('room-check-out');
  const time = document.getElementById('room-arrival-time'), hours = document.getElementById('room-hours');
  const guests = document.getElementById('room-guests'), submit = document.getElementById('room-book-button');
  const availability = document.getElementById('room-availability'), message = document.getElementById('room-booking-message');
  const storageKey = 'kallah-book:demo-bookings:v1', pendingKey = 'kallah-book:pending-room:v1';
  const money = value => '₹' + new Intl.NumberFormat('en-IN').format(value);
  const todayParts = new Intl.DateTimeFormat('en-CA', {timeZone: room.time_zone || 'Asia/Kolkata', year:'numeric', month:'2-digit', day:'2-digit'}).formatToParts(new Date());
  const part = name => todayParts.find(p => p.type === name).value;
  const today = `${part('year')}-${part('month')}-${part('day')}`;
  const wallTime = (date, value='00:00') => Date.parse(`${date}T${value}:00Z`);
  const iso = ms => new Date(ms).toISOString().slice(0, 16);
  const dateAfter = (date, days=1) => new Date(wallTime(date) + days * 86400000).toISOString().slice(0, 10);
  const read = () => { try { const list = JSON.parse(localStorage.getItem(storageKey) || '[]'); return Array.isArray(list) ? list.filter(b => b?.demo === true) : []; } catch { return []; } };
  const mode = () => form.querySelector('[name="stay-mode"]:checked').value;
  const state = () => ({mode:mode(), check_in:arrival.value, check_out:departure.value, start_time:time.value, hours:hours.value, guests:guests.value});
  arrival.min = today; arrival.value = today; departure.value = dateAfter(today);

  function quote() {
    const input = state(), count = Number(input.guests);
    if (!input.check_in || input.check_in < today) throw new Error('Choose a check-in date from today onwards.');
    if (!Number.isInteger(count) || count < 1 || count > room.max_guests) throw new Error(`This room accommodates up to ${room.max_guests} guests.`);
    let start, end, units, rate;
    if (input.mode === 'night') {
      units = (wallTime(input.check_out) - wallTime(input.check_in)) / 86400000;
      if (!Number.isInteger(units) || units < 1 || units > room.max_nights) throw new Error(`Choose a check-out date after check-in, up to ${room.max_nights} nights.`);
      start = wallTime(input.check_in, room.check_in_time); end = wallTime(input.check_out, room.check_out_time);
      rate = room.nightly_rate_inr;
    } else {
      if (!room.booking_modes.includes('hour') || !room.hourly) throw new Error('Hourly stays are not offered for this room.');
      units = Number(input.hours); rate = room.hourly.rate_inr;
      if (!Number.isInteger(units) || units < room.hourly.min_hours || units > room.hourly.max_hours) throw new Error(`Choose ${room.hourly.min_hours}–${room.hourly.max_hours} hours.`);
      start = wallTime(input.check_in, input.start_time); end = start + units * 3600000;
      if (!Number.isFinite(start) || start < wallTime(input.check_in, room.hourly.opens) || end > wallTime(input.check_in, room.hourly.closes)) throw new Error(`Hourly stays must fit between ${room.hourly.opens} and ${room.hourly.closes}.`);
    }
    const reservations = [...(room.blocked_stays || []), ...read().filter(b => b.kind === 'room' && b.city === page.city && b.slug === page.business.slug && b.room_id === room.id)];
    const events = [];
    for (const booking of reservations) {
      const from = Date.parse(booking.check_in + 'Z'), to = Date.parse(booking.check_out + 'Z');
      if (from < end && start < to) { events.push([Math.max(start,from),1],[Math.min(end,to),-1]); }
    }
    let active = 0, peak = 0;
    events.sort((a,b)=>a[0]-b[0] || a[1]-b[1]).forEach(event=>{active+=event[1];peak=Math.max(peak,active);});
    return {mode:input.mode, check_in:iso(start), check_out:iso(end), units, rate_inr:rate, total_inr:rate*units, guests:count, available:peak<room.inventory};
  }
  function update() {
    const hourly = mode() === 'hour';
    document.querySelector('.room-rate-heading strong').textContent = money(hourly ? room.hourly.rate_inr : room.nightly_rate_inr);
    document.querySelector('.room-rate-heading span').textContent = hourly ? '/ hour' : '/ night';
    document.getElementById('room-hour-fields').hidden = !hourly;
    document.getElementById('room-check-out-field').hidden = hourly;
    departure.disabled = hourly; time.disabled = !hourly; hours.disabled = !hourly;
    if (arrival.value) departure.min = dateAfter(arrival.value);
    availability.classList.remove('is-unavailable');
    try {
      const q = quote();
      document.getElementById('room-price-breakdown').textContent = `${money(q.rate_inr)} × ${q.units} ${hourly ? (q.units===1?'hour':'hours') : (q.units===1?'night':'nights')} · departure ${q.check_out.replace('T',' ')}`;
      document.getElementById('room-total').textContent = money(q.total_inr);
      availability.textContent = q.available ? 'Available for your selected stay.' : 'Already booked for part of this stay. Try different dates or hours.';
      availability.classList.toggle('is-unavailable', !q.available); submit.disabled = !q.available;
      return q;
    } catch(error) {
      availability.textContent = error.message; availability.classList.add('is-unavailable');
      document.getElementById('room-total').textContent = '—'; document.getElementById('room-price-breakdown').textContent = 'Choose your stay details.';
      submit.disabled = true; return null;
    }
  }
  try {
    const pending = JSON.parse(sessionStorage.getItem(pendingKey) || 'null');
    if (pending?.path === location.pathname) {
      const p = pending.values;
      const option = form.querySelector(`[name="stay-mode"][value="${p.mode === 'hour' ? 'hour' : 'night'}"]`); if(option)option.checked=true;
      arrival.value=p.check_in;departure.value=p.check_out;time.value=p.start_time;hours.value=p.hours;guests.value=p.guests;
      sessionStorage.removeItem(pendingKey);
    }
  } catch { /* Browser storage may be disabled. */ }
  form.addEventListener('input',()=>{message.textContent='';update();});
  form.addEventListener('change',()=>{message.textContent='';update();});
  window.addEventListener('storage', event=>{if(event.key===storageKey || event.key===null)update();});
  form.addEventListener('submit', event=>{
    event.preventDefault(); const q=update(); if(!q?.available)return;
    let user;
    try { user=JSON.parse(localStorage.getItem('kallah-book:user:v1') || 'null'); } catch { user=null; }
    if (!user || !/^(?:\+91)?\d{10}$/.test(user.phone || '')) {
      try {sessionStorage.setItem(pendingKey,JSON.stringify({path:location.pathname,values:state()}));}catch{message.textContent='Browser storage is blocked. This demo reservation cannot be saved.';return;}
      location.assign('/login?next='+encodeURIComponent(location.pathname));return;
    }
    const booking={...q,kind:'room',demo:true,reference:'KR-'+Date.now().toString(36).toUpperCase()+'-'+Math.random().toString(36).slice(2,6).toUpperCase(),city:page.city,category:'hotels',slug:page.business.slug,business:page.business.name,room_id:room.id,room_name:room.name,user_phone:user.phone,channel:user.channel,time_zone:room.time_zone};
    try {localStorage.setItem(storageKey,JSON.stringify([booking,...read()].slice(0,50)));}
    catch{message.textContent='Browser storage is blocked. Reservation could not be saved.';return;}
    message.textContent=`Demo room reservation saved (${booking.reference}) · ${room.name} · ${q.check_in.replace('T',' ')} → ${q.check_out.replace('T',' ')}.`;
    update();
  });
  update();
})();
