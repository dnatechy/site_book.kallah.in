/* Shared deterministic dining quote engine for the static demo and Node preview. */
"use strict";
(() => {
  const minutes = value => { const [h,m]=String(value).split(':').map(Number); return h*60+m; };
  const hhmm = n => `${String(Math.floor(n/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`;
  const indiaDate = (now=new Date()) => new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
  const dateAfter = (date,days) => new Date(Date.parse(date+'T00:00:00Z')+days*86400000).toISOString().slice(0,10);
  const slots = config => config.sessions.flatMap(session => {const times=[]; for(let t=minutes(session.opens);t+config.duration_minutes<=minutes(session.closes);t+=config.slot_minutes)times.push(hhmm(t));return times;});
  const whole = value => (typeof value === 'number' && Number.isInteger(value)) || (typeof value === 'string' && /^-?\d+$/.test(value.trim()));
  function quote(config,input,reservations=[],now=new Date()) {
    const guests=Number(input.guests), date=input.date, time=input.time;
    if (!whole(input.guests)||!Number.isInteger(guests)||guests<1||guests>config.max_party_size) throw new Error(`Choose 1–${config.max_party_size} guests.`);
    if(!/^\d{4}-\d{2}-\d{2}$/.test(date||'')||!Number.isFinite(Date.parse(date+'T00:00:00Z'))||new Date(date+'T00:00:00Z').toISOString().slice(0,10)!==date)throw new Error('Choose a valid dining date.');
    if(date>dateAfter(indiaDate(now),config.advance_days))throw new Error('The selected date is outside the advance booking window.');
    const start=Date.parse(`${date}T${time}:00+05:30`);
    if(!slots(config).includes(time))throw new Error('Choose an arrival slot within the dining hours.');
    if(start<now.getTime()+config.lead_minutes*60000)throw new Error(`Reserve at least ${config.lead_minutes} minutes before arrival.`);
    const startMinute=minutes(time),end=startMinute+config.duration_minutes;
    const relevant=[...reservations.filter(r=>r.date===date),...(config.demo_daily_reservations||[]).map(r=>({...r,date})),...(config.blocked_reservations||[]).filter(r=>r.date===date)];
    const busy=new Set();
    for(const r of relevant)if(startMinute<minutes(r.time)+(r.duration_minutes||config.duration_minutes)&&minutes(r.time)<end)for(const id of r.table_ids||[])busy.add(id);
    const tables=new Map(config.tables.map(t=>[t.id,t.seats]));
    const options=config.seating_options.filter(o=>o.table_ids.length&&new Set(o.table_ids).size===o.table_ids.length&&o.table_ids.every(id=>tables.has(id)&&!busy.has(id))).map(o=>({...o,capacity:o.table_ids.reduce((n,id)=>n+tables.get(id),0)})).sort((a,b)=>a.capacity-b.capacity||a.table_ids.length-b.table_ids.length||a.id.localeCompare(b.id));
    const selected=options.find(o=>o.capacity>=guests)||null;
    if(!Array.isArray(input.items)||input.items.length>100)throw new Error('Choose dishes from the menu.');
    const quantities=new Map(),dishes=new Map(config.menu.map(d=>[d.id,d]));
    for(const item of input.items){if(!item||!dishes.has(item.dish_id))throw new Error('A selected dish is no longer on the menu.');const qty=Number(item.quantity);if(!whole(item.quantity)||!Number.isInteger(qty)||qty<0)throw new Error('Dish quantities must be whole numbers, zero or more.');quantities.set(item.dish_id,(quantities.get(item.dish_id)||0)+qty);}
    const lines=[];
    for(const [id,quantity] of quantities){if(!quantity)continue;const dish=dishes.get(id);const sold=relevant.filter(r=>r.time===time).flatMap(r=>r.items||[]).filter(i=>i.dish_id===id).reduce((n,i)=>n+i.quantity,0);const remaining=Math.max(0,(dish.stock_per_slot??50)-sold);if(!dish.available||quantity>Math.min(dish.max_per_order??20,remaining))throw new Error(`${dish.name} is unavailable in that quantity for this slot.`);lines.push({dish_id:id,name:dish.name,quantity,unit_price_paise:dish.price_paise,total_paise:quantity*dish.price_paise});}
    const total=lines.reduce((n,line)=>n+line.total_paise,0);
    return {available:!!selected,guests,date,time,end_time:hhmm(end),duration_minutes:config.duration_minutes,seating:selected,largest_available_group:Math.max(0,...options.map(o=>o.capacity)),table_ids:selected?.table_ids||[],items:lines,food_total_paise:total,pay_now_paise:total,currency:'INR',prices_include_tax:config.payment?.prices_include_tax===true,payment_mode:'demo',time_zone:config.time_zone};
  }
  globalThis.KallahDining={quote,slots,indiaDate,dateAfter};
})();
