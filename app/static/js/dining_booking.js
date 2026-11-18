"use strict";
(() => {
  const data=document.getElementById('dining-data'); if(!data)return;
  const page=JSON.parse(data.textContent),config=page.dining,engine=globalThis.KallahDining;
  const byId=id=>document.getElementById(id),guest=byId('dining-guests'),date=byId('dining-date'),slotArea=byId('dining-time-slots');
  const availability=byId('dining-availability'),message=byId('dining-message'),checkout=byId('dining-checkout'),dialog=byId('dining-checkout-dialog'),confirm=byId('dining-confirm');
  const storageKey='kallah-book:demo-bookings:v1',pendingKey='kallah-book:pending-dining:v1';
  const money=paise=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:paise%100?2:0}).format(paise/100);
  const timeLabel=value=>{const [h,m]=value.split(':').map(Number);return `${h%12||12}:${String(m).padStart(2,'0')} ${h>=12?'PM':'AM'}`;};
  const node=(tag,text,className)=>{const el=document.createElement(tag);el.textContent=text;if(className)el.className=className;return el;};
  const read=()=>{try{const all=JSON.parse(localStorage.getItem(storageKey)||'[]');return Array.isArray(all)?all.filter(b=>b?.demo===true):[];}catch{return [];}};
  const reservations=()=>read().filter(b=>b.kind==='dining'&&b.city===page.city&&b.slug===page.business.slug);
  let selectedTime='12:00',saved=false,savedQuote=null,submitting=false;
  const quantityInputs=[...document.querySelectorAll('[data-dish-quantity]')];
  const values=()=>({guests:guest.value,date:date.value,time:selectedTime,items:quantityInputs.map(input=>({dish_id:input.dataset.dishQuantity,quantity:input.value}))});
  date.min=engine.indiaDate(); date.max=engine.dateAfter(date.min,config.advance_days); date.value=engine.dateAfter(date.min,1);
  function renderLines(target,lines){target.replaceChildren();if(!lines.length){target.append(node('p','Seats only — no food pre-order.','muted'));return;}for(const item of lines){const line=node('div','','dining-cart-line');line.append(node('span',`${item.quantity} × ${item.name}`),node('span',money(item.total_paise)));target.append(line);}}
  function quote(){return engine.quote(config,values(),reservations());}
  function renderSlots(){
    for(const time of engine.slots(config)){
      let button=slotArea.querySelector(`[data-time="${time}"]`);
      if(!button){button=node('button',timeLabel(time),'dining-time-slot');button.type='button';button.dataset.time=time;button.addEventListener('click',()=>{selectedTime=time;saved=false;message.textContent='';update();});slotArea.append(button);}
      button.setAttribute('aria-pressed',String(time===selectedTime));
      try{const q=engine.quote(config,{guests:guest.value,date:date.value,time,items:[]},reservations());button.disabled=!q.available;button.title=q.available?`Seats together for ${guest.value} people`:'No suitable table group for your party';}catch(error){button.disabled=true;button.title=error.message;}
    }
  }
  function update(){
    renderSlots();
    for(const button of document.querySelectorAll('[data-quantity]')){const input=quantityInputs.find(i=>i.dataset.dishQuantity===button.dataset.quantity);const n=Number(input.value);button.disabled=Number(button.dataset.delta)<0?n<=0:n>=Number(input.max);}
    availability.classList.remove('is-unavailable');
    const summary=byId('dining-summary-visit');summary.replaceChildren(node('strong',`${guest.value||'—'} people · ${date.value||'Choose a date'}`),node('p',selectedTime?`${timeLabel(selectedTime)} arrival · ${config.duration_minutes} minutes`:'Choose an arrival time'));
    checkout.disabled=true;
    try{
      const q=saved?savedQuote:quote();
      availability.textContent=saved?'Your group reservation is saved on this device.':q.available?`Your ${q.guests} guests can sit together · ${q.seating.label}.`:`No connected table group for ${q.guests} guests at ${timeLabel(q.time)}. Largest available group: ${q.largest_available_group}. Choose another time or party size.`;
      availability.classList.toggle('is-unavailable',!q.available);
      if(q.available)summary.append(node('p',q.seating.label,'muted'));
      renderLines(byId('dining-cart'),q.items);byId('dining-food-total').textContent=money(q.food_total_paise);byId('dining-pay-total').textContent=money(q.pay_now_paise);
      checkout.textContent=saved?'Reservation saved':q.items.length?'Review & pay '+money(q.pay_now_paise):'Review seat reservation';checkout.disabled=!q.available||saved;return q;
    }catch(error){availability.textContent=error.message;availability.classList.add('is-unavailable');byId('dining-food-total').textContent='—';byId('dining-pay-total').textContent='—';byId('dining-cart').replaceChildren(node('p','Check your group details and dish quantities.','muted'));return null;}
  }
  function closeCheckout(){dialog.close();document.body.classList.remove('dining-checkout-open');checkout.focus();}
  async function openCheckout(){const q=update();if(!q?.available||saved)return;try{const response=await fetch(`/api/v1/locations/${encodeURIComponent(page.city)}/restaurants/businesses/${encodeURIComponent(page.business.slug)}/dining/quote`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(values())});const payload=await response.json();if(!response.ok||!payload.quote?.available||payload.quote.pay_now_paise!==q.pay_now_paise){message.textContent=payload.error?.message||payload.error||'Please refresh availability and review your order.';return;}}catch(error){message.textContent='Unable to verify seating with the booking API. Please try again.';return;}const details=byId('dining-checkout-details');details.replaceChildren(node('strong',page.business.name),node('p',`${q.guests} people · ${q.date} · ${timeLabel(q.time)}–${timeLabel(q.end_time)}`),node('p',q.seating.label));const lines=node('div','','dining-cart');renderLines(lines,q.items);details.append(lines,node('strong',`Pay at booking: ${money(q.pay_now_paise)}`));confirm.textContent=q.items.length?'Simulate payment & reserve':'Confirm demo seat reservation';byId('dining-checkout-error').textContent='';confirm.disabled=false;dialog.showModal();document.body.classList.add('dining-checkout-open');}
  byId('dining-visit-form').addEventListener('submit',e=>e.preventDefault());
  for(const input of [guest,date,...quantityInputs])input.addEventListener('input',()=>{saved=false;message.textContent='';update();});
  for(const button of document.querySelectorAll('[data-quantity]'))button.addEventListener('click',()=>{const input=quantityInputs.find(i=>i.dataset.dishQuantity===button.dataset.quantity);input.value=Math.min(Number(input.max),Math.max(0,(Number(input.value)||0)+Number(button.dataset.delta)));saved=false;message.textContent='';update();});
  for(const filter of document.querySelectorAll('[data-diet]'))filter.addEventListener('click',()=>{for(const b of document.querySelectorAll('[data-diet]'))b.setAttribute('aria-pressed',String(b===filter));for(const card of document.querySelectorAll('[data-dish-card]'))card.hidden=filter.dataset.diet!=='all'&&card.dataset.dishDiet!==filter.dataset.diet;});
  checkout.addEventListener('click',openCheckout);byId('dining-close-checkout').addEventListener('click',closeCheckout);
  dialog.addEventListener('cancel',event=>{event.preventDefault();closeCheckout();});
  window.addEventListener('storage',event=>{if(event.key===storageKey||event.key===null){update();if(dialog.open){closeCheckout();message.textContent='Availability changed in another tab. Review your dining plan again.';}}});
  confirm.addEventListener('click',()=>{
    if(submitting)return;
    const q=update();if(!q?.available){byId('dining-checkout-error').textContent='Availability or quantity changed. Close checkout and review your plan.';return;}
    let user;try{user=JSON.parse(localStorage.getItem('kallah-book:user:v1')||'null');}catch{user=null;}
    if(!user||!/^(?:\+91)?\d{10}$/.test(user.phone||'')){
      try{sessionStorage.setItem(pendingKey,JSON.stringify({path:location.pathname,values:values(),checkout:true}));}catch{byId('dining-checkout-error').textContent='Browser storage is blocked. This demo cannot be saved.';return;}
      location.assign('/login?next='+encodeURIComponent(location.pathname));return;
    }
    submitting=true;confirm.disabled=true;
    const booking={...q,kind:'dining',demo:true,reference:'KD-'+Date.now().toString(36).toUpperCase()+'-'+Math.random().toString(36).slice(2,6).toUpperCase(),city:page.city,category:'restaurants',slug:page.business.slug,business:page.business.name,user_phone:user.phone,channel:user.channel,payment_status:q.items.length?'demo_paid':'no_payment_required'};
    try{localStorage.setItem(storageKey,JSON.stringify([booking,...read()].slice(0,50)));saved=true;savedQuote=q;closeCheckout();message.replaceChildren(node('strong',`Demo reservation saved · ${booking.reference}`),node('p',q.items.length?`Demo payment ${money(q.pay_now_paise)} · no money charged.`:'Seats reserved without a food pre-order.'));update();}
    catch{byId('dining-checkout-error').textContent='Browser storage is blocked. No reservation or payment was made.';confirm.disabled=false;}
    submitting=false;
  });
  let resumeCheckout=false;
  try{const pending=JSON.parse(sessionStorage.getItem(pendingKey)||'null');if(pending?.path===location.pathname){const v=pending.values;guest.value=v.guests;date.value=v.date;selectedTime=v.time;for(const input of quantityInputs)input.value=v.items.find(i=>i.dish_id===input.dataset.dishQuantity)?.quantity||0;resumeCheckout=pending.checkout;sessionStorage.removeItem(pendingKey);}}catch{/* Invalid demo draft is ignored. */}
  update();if(resumeCheckout)openCheckout();
})();
