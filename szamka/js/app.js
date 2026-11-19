/* Szamka: sklep. Lista lokali, menu, koszyk, kasa, śledzenie zamówienia i historia.
   Cały stan siedzi w localStorage tej przeglądarki, strona nie ma serwera. */
(function () {
  'use strict';
  var SZ = window.SZ, art = SZ.art;
  var KEY = 'szamka:v1';
  var app, modalRoot, toastRoot;

  /* ================= narzędzia ================= */
  var ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return ESC[c]; }); }
  function r2(n) { return Math.round((+n || 0) * 100) / 100; }
  function zl(n) { return r2(n).toFixed(2).replace('.', ',') + ' zł'; }
  function zlShort(n) { n = r2(n); return (n % 1 === 0 ? String(n) : n.toFixed(2).replace('.', ',')) + ' zł'; }
  function dec(n, d) { return (+n || 0).toFixed(d == null ? 1 : d).replace('.', ','); }
  function count(n) { return String(Math.round(+n || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }
  function uid(p) { return (p || '') + Math.random().toString(36).slice(2, 9); }
  function clone(o) { return JSON.parse(JSON.stringify(o)); }
  function clamp(v, a, b) { return Math.min(b, Math.max(a, v)); }
  function pad(n) { return n < 10 ? '0' + n : '' + n; }
  function hhmm(ts) { var d = new Date(ts); return pad(d.getHours()) + ':' + pad(d.getMinutes()); }
  var MONTHS = ['sty', 'lut', 'mar', 'kwi', 'maj', 'cze', 'lip', 'sie', 'wrz', 'paź', 'lis', 'gru'];
  function whenPL(ts) {
    var d = new Date(ts), n = new Date();
    var d0 = new Date(n.getFullYear(), n.getMonth(), n.getDate()).getTime();
    var dd = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
    var diff = Math.round((d0 - dd) / 86400000);
    var day = diff === 0 ? 'dziś' : diff === 1 ? 'wczoraj' : diff === -1 ? 'jutro' :
      d.getDate() + ' ' + MONTHS[d.getMonth()] + (d.getFullYear() !== n.getFullYear() ? ' ' + d.getFullYear() : '');
    return day + ', ' + hhmm(ts);
  }
  function fold(s) {
    return String(s || '').toLowerCase().replace(/ł/g, 'l').normalize('NFD').replace(/[̀-ͯ]/g, '');
  }
  function plural(n, one, few, many) {
    var m10 = n % 10, m100 = n % 100;
    if (n === 1) return one;
    if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
    return many;
  }
  /* Tylko zwykłe adresy http(s), wgrane obrazki i pliki obok strony. */
  function safeImg(u) {
    u = String(u || '').trim();
    if (/^https?:\/\/[^\s"'<>]+$/i.test(u)) return u;
    if (/^data:image\/(png|jpe?g|webp|gif);base64,[a-z0-9+/=]+$/i.test(u)) return u;
    if (/^(\.{0,2}\/)?[\w\-./%]+\.(png|jpe?g|webp|gif)$/i.test(u)) return u;
    return '';
  }
  function initials(name) {
    var skip = { i: 1, na: 1, pod: 1, u: 1, w: 1, z: 1, 'do': 1, od: 1 };
    var w = String(name || '').trim().split(/\s+/).filter(function (x) { return x && !skip[x.toLowerCase()]; });
    if (!w.length) return '?';
    return (w[0].charAt(0) + (w[1] ? w[1].charAt(0) : '')).toUpperCase();
  }

  var ICONS = {
    pin: '<path d="M12 21s-6.5-5.6-6.5-10.5a6.5 6.5 0 1 1 13 0C18.5 15.4 12 21 12 21z"/><circle cx="12" cy="10.5" r="2.3"/>',
    clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    bike: '<circle cx="6" cy="16.5" r="3.5"/><circle cx="18" cy="16.5" r="3.5"/><path d="M6 16.5l4-7h5l3 7M10 9.5L8.5 6.5h-2M15 9.5l-3.5 7"/>',
    star: '<path d="M12 3.2l2.7 5.6 6.1.8-4.5 4.2 1.1 6-5.4-3-5.4 3 1.1-6L3.2 9.6l6.1-.8z"/>',
    bag: '<path d="M5.5 8.5h13l-1 11h-11z"/><path d="M9 8.5V7a3 3 0 0 1 6 0v1.5"/>',
    search: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
    plus: '<path d="M12 5.5v13M5.5 12h13"/>',
    minus: '<path d="M5.5 12h13"/>',
    x: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
    'chev-right': '<path d="M9.5 5.5L16 12l-6.5 6.5"/>',
    'chev-left': '<path d="M14.5 5.5L8 12l6.5 6.5"/>',
    'chev-down': '<path d="M5.5 9.5L12 16l6.5-6.5"/>',
    up: '<path d="M12 19V5M6 11l6-6 6 6"/>',
    down: '<path d="M12 5v14M6 13l6 6 6-6"/>',
    user: '<circle cx="12" cy="8.5" r="3.8"/><path d="M4.5 20c1-4 4-5.5 7.5-5.5s6.5 1.5 7.5 5.5"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    edit: '<path d="M4.5 19.5l1-4.2L16.3 4.5l3.2 3.2L8.7 18.5z"/><path d="M14 6.8l3.2 3.2"/>',
    trash: '<path d="M5 7.5h14M9.5 7.5V5h5v2.5M7 7.5l.8 12h8.4l.8-12"/>',
    copy: '<rect x="8.5" y="8.5" width="11" height="11" rx="2"/><path d="M15.5 8.5v-2a2 2 0 0 0-2-2h-7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h2"/>',
    share: '<circle cx="6.5" cy="12" r="2.5"/><circle cx="17.5" cy="6" r="2.5"/><circle cx="17.5" cy="18" r="2.5"/><path d="M8.7 10.8l6.6-3.6M8.7 13.2l6.6 3.6"/>',
    lock: '<rect x="5.5" y="10.5" width="13" height="9" rx="2"/><path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/>',
    info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.8v.4"/>',
    tag: '<path d="M4.5 12.5v-8h8l7.5 7.5-8 8z"/><circle cx="9" cy="9" r="1.3"/>',
    receipt: '<path d="M6.5 3.5h11v17l-2.2-1.5-1.8 1.5-1.5-1.5-1.5 1.5-1.8-1.5-2.2 1.5z"/><path d="M9.5 8.5h5M9.5 12h5"/>',
    home: '<path d="M4.5 11.5L12 5l7.5 6.5M6.5 10v9.5h11V10"/>',
    store: '<path d="M4.5 9.5l1.5-5h12l1.5 5M5.5 9.5v10h13v-10M4.5 9.5a2.5 2.5 0 0 0 5 0 2.5 2.5 0 0 0 5 0 2.5 2.5 0 0 0 5 0"/>',
    sliders: '<path d="M4.5 7.5h9M17.5 7.5h2M4.5 16.5h2M10.5 16.5h9"/><circle cx="15.5" cy="7.5" r="2"/><circle cx="8.5" cy="16.5" r="2"/>',
    eye: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="2.8"/>',
    'eye-off': '<path d="M4 4l16 16M9.9 6A8.6 8.6 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a16 16 0 0 1-2.7 3.5M6.2 7.8A15.6 15.6 0 0 0 2.5 12S6 18.5 12 18.5a8.7 8.7 0 0 0 3.8-.9"/>',
    download: '<path d="M12 4.5v11M7 11l5 5 5-5M5 19.5h14"/>',
    upload: '<path d="M12 16V5M7 9.5l5-5 5 5M5 19.5h14"/>',
    gear: '<circle cx="12" cy="12" r="3"/><path d="M12 3.5v2.2M12 18.3v2.2M3.5 12h2.2M18.3 12h2.2M6 6l1.6 1.6M16.4 16.4L18 18M18 6l-1.6 1.6M7.6 16.4L6 18"/>',
    link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>'
  };
  function icon(name, cls) {
    var filled = name === 'star';
    return '<svg class="ic' + (cls ? ' ' + cls : '') + '" viewBox="0 0 24 24" width="20" height="20" fill="' + (filled ? 'currentColor' : 'none') +
      '" stroke="' + (filled ? 'none' : 'currentColor') + '" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' + (ICONS[name] || '') + '</svg>';
  }

  /* ================= stan ================= */
  var state, saveWarned = false;
  function seedData() { return clone(window.SZAMKA_START); }
  function fresh() {
    var s = seedData();
    return {
      meta: { seed: s.seed, edited: false },
      settings: s.settings, restaurants: s.restaurants, orders: s.orders || [],
      basket: { rid: null, lines: [] }, user: s.user
    };
  }
  function normalize() {
    var s = seedData();
    state.meta = state.meta || { seed: '', edited: true };
    state.settings = Object.assign({}, s.settings, state.settings || {});
    state.settings.reveal = Object.assign({}, s.settings.reveal, state.settings.reveal || {});
    ['cuisines', 'vouchers', 'couriers'].forEach(function (k) {
      if (!Array.isArray(state.settings[k])) state.settings[k] = s.settings[k];
    });
    state.user = Object.assign({}, s.user, state.user || {});
    if (!Array.isArray(state.restaurants)) state.restaurants = s.restaurants;
    if (!Array.isArray(state.orders)) state.orders = [];
    if (!state.basket || !Array.isArray(state.basket.lines)) state.basket = { rid: null, lines: [] };
    state.orders = state.orders.filter(function (o) { return o && typeof o === 'object'; });
    state.orders.forEach(function (o) {
      o.id = o.id || uid('z'); o.no = o.no || orderNo();
      o.items = Array.isArray(o.items) ? o.items : [];
      o.times = Object.assign({ confirm: 2, prep: 15, ride: 15 }, o.times || {});
      o.courier = Object.assign({ name: 'Kamil', vehicle: 'rower' }, o.courier || {});
      o.customer = Object.assign({ name: '', phone: '' }, o.customer || {});
      o.reveal = Object.assign({ on: false, title: '', text: '' }, o.reveal || {});
      o.placedAt = isFinite(+o.placedAt) && +o.placedAt > 0 ? +o.placedAt : Date.now();
      o.rname = o.rname || 'Lokal';
    });
    state.restaurants.forEach(function (r) {
      r.menu = Array.isArray(r.menu) ? r.menu : [];
      r.cuisines = Array.isArray(r.cuisines) ? r.cuisines : [];
      r.menu.forEach(function (c) {
        c.items = Array.isArray(c.items) ? c.items : [];
        c.items.forEach(function (i) {
          i.variants = Array.isArray(i.variants) ? i.variants : [];
          i.extras = Array.isArray(i.extras) ? i.extras : [];
        });
      });
    });
  }
  function load() {
    var raw = null;
    try { raw = JSON.parse(localStorage.getItem(KEY)); } catch (e) { raw = null; }
    if (!raw || !Array.isArray(raw.restaurants)) { state = fresh(); return; }
    state = raw;
    var s = window.SZAMKA_START;
    /* Nowsze dane startowe trafiają do osób, które same niczego nie zmieniały. */
    if (state.meta && !state.meta.edited && state.meta.seed !== s.seed) {
      var f = fresh();
      state.settings = f.settings; state.restaurants = f.restaurants; state.meta.seed = s.seed;
      if (!state.restaurants.some(function (r) { return r.id === state.basket.rid; })) state.basket = { rid: null, lines: [] };
    }
    normalize();
  }
  function save(quiet) {
    try { localStorage.setItem(KEY, JSON.stringify(state)); return true; }
    catch (e) {
      if (!saveWarned && !quiet) { saveWarned = true; toast('Przeglądarka nie zapisała zmian. Pamięć jest pełna albo wyłączona.'); }
      return false;
    }
  }
  var saveT = 0;
  function saveSoon() { clearTimeout(saveT); saveT = setTimeout(save, 350); }

  function getR(id) { return state.restaurants.find(function (r) { return r.id === id; }); }
  function getItem(r, iid) {
    for (var c = 0; c < r.menu.length; c++) for (var i = 0; i < r.menu[c].items.length; i++) if (r.menu[c].items[i].id === iid) return r.menu[c].items[i];
    return null;
  }
  function getOrder(id) { return state.orders.find(function (o) { return o.id === id; }); }
  function visibleR() { return state.restaurants.filter(function (r) { return !r.hidden; }); }

  /* ================= koszyk i kwoty ================= */
  function basketCount() { return state.basket.lines.reduce(function (a, l) { return a + l.qty; }, 0); }
  function qtyInBasket(rid, iid) {
    if (state.basket.rid !== rid) return 0;
    return state.basket.lines.reduce(function (a, l) { return a + (l.iid === iid ? l.qty : 0); }, 0);
  }
  function totals(rid, lines, extra) {
    var r = getR(rid);
    var sub = r2(lines.reduce(function (a, l) { return a + l.price * l.qty; }, 0));
    var fee = r ? +r.fee || 0 : 0;
    if (r && r.freeFrom > 0 && sub >= r.freeFrom) fee = 0;
    var service = sub > 0 ? (+state.settings.serviceFee || 0) : 0;
    var tip = extra && extra.tip || 0, disc = 0, v = extra && extra.voucher;
    if (v) {
      if (v.kind === 'dostawa') disc = fee;
      else if (v.kind === 'procent') disc = sub * (+v.value || 0) / 100;
      else disc = Math.min(+v.value || 0, sub);
    }
    disc = r2(disc);
    return {
      sub: sub, fee: fee, service: service, tip: tip, disc: disc,
      total: r2(Math.max(0, sub + fee + service + tip - disc)),
      missing: r ? r2(Math.max(0, r.minOrder - sub)) : 0,
      toFree: r && r.freeFrom > 0 && r.fee > 0 ? r2(Math.max(0, r.freeFrom - sub)) : 0
    };
  }
  function addLine(rid, item, vi, eis, qty) {
    var parts = [], price = +item.price || 0;
    if (item.variants.length) { var v = item.variants[vi] || item.variants[0]; price += +v.price || 0; parts.push(v.name); }
    eis.forEach(function (k) { if (item.extras[k]) { price += +item.extras[k].price || 0; parts.push(item.extras[k].name); } });
    var key = item.id + '|' + vi + '|' + eis.join(',');
    if (state.basket.rid !== rid) state.basket = { rid: rid, lines: [] };
    var line = state.basket.lines.find(function (l) { return l.key === key; });
    if (line) line.qty += qty;
    else state.basket.lines.push({ key: key, iid: item.id, name: item.name, opts: parts.join(', '), price: r2(price), qty: qty });
    save(); refreshBasket();
  }
  function withBasketFor(rid, fn) {
    var b = state.basket, other = getR(b.rid);
    if (b.rid && b.rid !== rid && b.lines.length && other) {
      confirmBox('Zacząć nowy koszyk?', 'W koszyku masz już dania z lokalu ' + other.name + '. Jedno zamówienie może pochodzić tylko z jednego lokalu.',
        'Zacznij nowy koszyk', function () { state.basket = { rid: rid, lines: [] }; fn(); });
    } else fn();
  }

  /* ================= zamówienia ================= */
  var STAGES = ['zlozone', 'kuchnia', 'droga', 'dostarczone'];
  var STATUS = {
    zlozone: { chip: 'Wysłane do lokalu', step: 'Złożone' },
    kuchnia: { chip: 'W przygotowaniu', step: 'W kuchni' },
    droga: { chip: 'W drodze', step: 'W drodze' },
    dostarczone: { chip: 'Dostarczone', step: 'Dostarczone' },
    anulowane: { chip: 'Anulowane', step: 'Anulowane' }
  };
  var VEHICLES = { rower: 'na rowerze', skuter: 'na skuterze', samochod: 'samochodem' };
  var PAY = { blik: 'BLIK', karta: 'Karta płatnicza', portfel: 'Apple Pay lub Google Pay', gotowka: 'Gotówka przy odbiorze' };

  function orderTimes(o) {
    var t0 = +o.placedAt || 0, m = 60000, tm = o.times || {};
    var t1 = t0 + (+tm.confirm || 0) * m, t2 = t1 + (+tm.prep || 0) * m, t3 = t2 + (+tm.ride || 0) * m;
    return [t0, t1, t2, t3];
  }
  function orderStatus(o, now) {
    if (o.status && o.status !== 'auto' && STATUS[o.status]) return o.status;
    var t = orderTimes(o); now = now || Date.now();
    return now >= t[3] ? 'dostarczone' : now >= t[2] ? 'droga' : now >= t[1] ? 'kuchnia' : 'zlozone';
  }
  function rideProgress(o, now) {
    var st = orderStatus(o, now);
    if (st === 'dostarczone') return 1;
    if (st !== 'droga') return 0;
    if (o.status && o.status !== 'auto') return 0.55;
    var t = orderTimes(o); now = now || Date.now();
    return clamp((now - t[2]) / Math.max(1, t[3] - t[2]), 0.02, 0.98);
  }
  function orderSub(o) { return r2(o.items.reduce(function (a, i) { return a + (+i.price || 0) * (+i.qty || 0); }, 0)); }
  function orderTotal(o) { return r2(Math.max(0, orderSub(o) + (+o.fee || 0) + (+o.service || 0) + (+o.tip || 0) - (+o.disc || 0))); }
  function orderNo() { return String(Math.floor(100000 + Math.random() * 900000)); }
  function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
  function activeOrder() {
    var best = null;
    state.orders.forEach(function (o) {
      var st = orderStatus(o);
      if (st !== 'dostarczone' && st !== 'anulowane' && (!best || o.placedAt > best.placedAt)) best = o;
    });
    return best;
  }
  function newOrder(r, lines, extra) {
    extra = extra || {};
    var t = r ? totals(r.id, lines, extra) : { fee: 0, service: 0, tip: 0, disc: 0 };
    var lo = r ? +r.timeMin || 25 : 25, hi = r ? +r.timeMax || 40 : 40;
    var total = extra.minutes || Math.round(lo + Math.random() * Math.max(0, hi - lo));
    var confirm = 2, ride = clamp(Math.round(Math.min(total, hi) * 0.4), 5, 25), prep = Math.max(4, total - confirm - ride);
    var u = state.user;
    return {
      id: uid('z'), no: orderNo(),
      rid: r ? r.id : '', rname: r ? r.name : 'Lokal', art: r ? r.art : 'pizza', color: r ? r.color : '#2E6B4F', logo: r ? r.logo : '',
      items: lines.map(function (l) { return { name: l.name, opts: l.opts || '', qty: l.qty, price: l.price }; }),
      fee: t.fee, service: t.service, tip: t.tip, disc: t.disc, voucher: extra.voucher ? extra.voucher.code : '',
      address: extra.address || u.address || '', customer: { name: u.name || '', phone: u.phone || '' },
      pay: extra.pay || PAY.blik, note: extra.note || '',
      placedAt: Date.now(), times: { confirm: confirm, prep: prep, ride: ride }, status: 'auto',
      courier: { name: pick(state.settings.couriers.length ? state.settings.couriers : ['Kamil']), vehicle: pick(['rower', 'rower', 'skuter', 'samochod']) },
      reveal: clone(state.settings.reveal)
    };
  }

  /* ---- link do śledzenia: całe zamówienie spakowane w adresie ---- */
  function b64u(bytes) {
    var s = '';
    for (var i = 0; i < bytes.length; i += 8192) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
    return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  function unb64u(str) {
    str = str.replace(/-/g, '+').replace(/_/g, '/');
    while (str.length % 4) str += '=';
    var bin = atob(str), out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  function pack(obj) {
    var bytes = new TextEncoder().encode(JSON.stringify(obj));
    if (!window.CompressionStream) return Promise.resolve('j' + b64u(bytes));
    try {
      var cs = new Blob([bytes]).stream().pipeThrough(new CompressionStream('deflate-raw'));
      return new Response(cs).arrayBuffer().then(function (buf) {
        var z = new Uint8Array(buf);
        return z.length < bytes.length ? 'z' + b64u(z) : 'j' + b64u(bytes);
      }).catch(function () { return 'j' + b64u(bytes); });
    } catch (e) { return Promise.resolve('j' + b64u(bytes)); }
  }
  function unpack(str) {
    return new Promise(function (resolve, reject) {
      try {
        var kind = str.charAt(0), bytes = unb64u(str.slice(1));
        if (kind === 'j') return resolve(JSON.parse(new TextDecoder().decode(bytes)));
        if (kind !== 'z' || !window.DecompressionStream) return reject(new Error('format'));
        var ds = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
        new Response(ds).arrayBuffer().then(function (buf) {
          resolve(JSON.parse(new TextDecoder().decode(new Uint8Array(buf))));
        }).catch(reject);
      } catch (e) { reject(e); }
    });
  }
  function toShare(o) {
    return {
      v: 1, n: o.no, r: o.rname, a: o.art, c: o.color, l: /^https?:\/\//i.test(o.logo || '') ? o.logo : '',
      i: o.items.map(function (i) { return [i.name, i.qty, i.price, i.opts || '']; }),
      f: o.fee, s: o.service, t: o.tip, d: o.disc, ad: o.address, cu: o.customer.name, p: o.pay,
      pa: o.placedAt, tm: [o.times.confirm, o.times.prep, o.times.ride], st: o.status,
      co: [o.courier.name, o.courier.vehicle], rv: o.reveal && o.reveal.on ? [o.reveal.title, o.reveal.text] : 0
    };
  }
  function str(v, max) { return String(v == null ? '' : v).slice(0, max || 120); }
  function numIn(v, lo, hi) { v = +v; return isFinite(v) ? clamp(v, lo, hi) : lo; }
  /* Link przychodzi z zewnątrz, więc każde pole jest sprawdzane i przycinane. */
  function fromShare(x) {
    if (!x || typeof x !== 'object' || !Array.isArray(x.i)) throw new Error('format');
    var tm = Array.isArray(x.tm) ? x.tm : [2, 15, 15], co = Array.isArray(x.co) ? x.co : ['Kamil', 'rower'];
    return {
      id: 'udostepnione', no: str(x.n, 12), rid: '', rname: str(x.r, 60) || 'Lokal', art: art.dishKey(x.a), color: art.safeColor(x.c),
      logo: /^https?:\/\//i.test(x.l || '') ? str(x.l, 400) : '',
      items: x.i.slice(0, 60).map(function (i) {
        i = Array.isArray(i) ? i : [];
        return { name: str(i[0], 90), qty: numIn(i[1], 1, 999), price: numIn(i[2], 0, 99999), opts: str(i[3], 160) };
      }),
      fee: numIn(x.f, 0, 9999), service: numIn(x.s, 0, 9999), tip: numIn(x.t, 0, 9999), disc: numIn(x.d, 0, 99999),
      address: str(x.ad, 160), customer: { name: str(x.cu, 60), phone: '' }, pay: str(x.p, 40), note: '',
      placedAt: numIn(x.pa, 0, 4102444800000),
      times: { confirm: numIn(tm[0], 0, 600), prep: numIn(tm[1], 0, 600), ride: numIn(tm[2], 0, 600) },
      status: STATUS[x.st] ? x.st : 'auto',
      courier: { name: str(co[0], 30) || 'Kurier', vehicle: VEHICLES[co[1]] ? co[1] : 'rower' },
      reveal: Array.isArray(x.rv) ? { on: true, title: str(x.rv[0], 80), text: str(x.rv[1], 240) } : { on: false, title: '', text: '' }
    };
  }
  function shareLink(o) {
    return pack(toShare(o)).then(function (p) { return location.href.split('#')[0] + '#/s/' + p; });
  }
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text).then(function () { return true; }, function () { return false; });
    var ta = document.createElement('textarea'), ok = false;
    ta.value = text; ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;left:-999px;top:0';
    document.body.appendChild(ta); ta.select();
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return Promise.resolve(ok);
  }

  /* ================= okna i komunikaty ================= */
  var lastFocus = null, modalOnClose = null;
  function openModal(html, opt) {
    opt = opt || {};
    if (!modalRoot.firstChild) lastFocus = document.activeElement;
    modalOnClose = opt.onClose || null;
    modalRoot.innerHTML = '<div class="modal ' + (opt.cls || '') + '" role="dialog" aria-modal="true" aria-label="' + esc(opt.label || 'Okno') + '">' +
      '<div class="modal__back"' + (opt.locked ? '' : ' data-act="modal-close"') + '></div><div class="modal__box" tabindex="-1">' + html + '</div></div>';
    document.body.classList.add('no-scroll');
    var box = modalRoot.querySelector('.modal__box');
    var first = box.querySelector('[autofocus]') || box;
    setTimeout(function () { try { first.focus({ preventScroll: true }); } catch (e) { /* stare przeglądarki */ } }, 30);
  }
  function closeModal(silent) {
    if (!modalRoot.firstChild) return;
    modalRoot.innerHTML = '';
    document.body.classList.remove('no-scroll');
    var cb = modalOnClose; modalOnClose = null;
    if (cb && !silent) cb();
    if (lastFocus && document.contains(lastFocus)) { try { lastFocus.focus({ preventScroll: true }); } catch (e) { /* nic */ } }
    lastFocus = null;
  }
  var confirmCb = null;
  function confirmBox(title, text, okLabel, cb, danger) {
    confirmCb = cb;
    openModal('<div class="dlg"><h2>' + esc(title) + '</h2><p>' + esc(text) + '</p><div class="dlg__btns">' +
      '<button class="btn btn--ghost" type="button" data-act="modal-close">Anuluj</button>' +
      '<button class="btn ' + (danger ? 'btn--danger' : 'btn--primary') + '" type="button" data-act="confirm-ok" autofocus>' + esc(okLabel) + '</button></div></div>',
    { label: title, cls: 'modal--small' });
  }
  function toast(msg) {
    if (!toastRoot) return;
    while (toastRoot.children.length >= 2) toastRoot.removeChild(toastRoot.firstChild);
    var el = document.createElement('div');
    el.className = 'toast'; el.textContent = msg;
    toastRoot.appendChild(el);
    setTimeout(function () { el.classList.add('is-out'); }, 2600);
    setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 3000);
  }

  /* ================= wspólne kawałki strony ================= */
  var ui = {
    cuisine: 'all', q: '', sort: 'polecane', f: { open: false, free: false, promo: false, min: 0, rating: 0 },
    menuQ: '', rid: null, co: null, im: null, order: null, sharedKey: null, shared: null, sharedErr: false, route: '', filtersOpen: false
  };

  function coverHTML(r, wide) {
    var img = safeImg(r.cover);
    if (img) return '<img class="art art--img" src="' + esc(img) + '" alt=""' + (wide ? '' : ' loading="lazy"') + '>';
    return (wide ? art.banner : art.cover)(r.art, r.color, r.id || r.rname || r.name);
  }
  function logoHTML(r, cls) {
    var img = safeImg(r.logo), c = art.safeColor(r.color), dark = art.lum(c) < 0.62;
    return '<span class="rlogo ' + (cls || '') + '"' + (img ? '' : ' style="background:' + c + ';color:' + (dark ? '#fff' : '#24152B') + '"') + '>' +
      (img ? '<img src="' + esc(img) + '" alt="">' : esc(initials(r.name || r.rname))) + '</span>';
  }

  function header(opt) {
    var addr = state.user.address, n = basketCount(), br = getR(state.basket.rid);
    return '<header class="hdr"><div class="wrap hdr__in">' +
      '<a class="logo" href="#/" aria-label="Szamka, strona główna">' + art.logo(30) + '<span class="logo__word">szamka</span></a>' +
      (opt.minimal ? '' :
        '<button class="addr" type="button" data-act="addr-open">' + icon('pin') + '<span class="addr__txt">' + (addr ? esc(addr) : 'Podaj adres dostawy') + '</span>' + icon('chev-down', 'ic--s') + '</button>' +
        '<nav class="hdr__nav" aria-label="Twoje konto">' +
        '<a class="hdr__link" href="#/zamowienia">' + icon('receipt') + '<span>Zamówienia</span></a>' +
        (n && br ? '<a class="hdr__link" href="#/lokal/' + encodeURIComponent(br.id) + '">' + icon('bag') + '<span>Koszyk</span><b class="pill">' + n + '</b></a>' : '') +
        '</nav>') +
      '</div></header>';
  }
  function promoBar(opt) {
    var p = state.settings.promoBar;
    return p && !opt.minimal && !opt.noPromo ? '<div class="promo"><div class="wrap">' + icon('tag', 'ic--s') + '<span>' + esc(p) + '</span></div></div>' : '';
  }
  function activeBar(opt) {
    if (opt.minimal || opt.noActive) return '';
    var o = activeOrder();
    if (!o || o.id === opt.orderId) return '';
    var st = orderStatus(o), t = orderTimes(o);
    return '<a class="active" href="#/zamowienie/' + esc(o.id) + '"><div class="wrap active__in"><span class="active__dot"></span>' +
      '<span><b>' + esc(o.rname) + '</b>, ' + STATUS[st].chip.toLowerCase() + '. Dostawa około ' + hhmm(t[3]) + '</span><span class="active__go">Śledź' + icon('chev-right', 'ic--s') + '</span></div></a>';
  }
  function footer() {
    function col(title, links) {
      return '<div class="ftr__col"><h3>' + title + '</h3><ul>' + links.map(function (l) {
        return '<li><button type="button" class="ftr__a" data-act="soon">' + l + '</button></li>';
      }).join('') + '</ul></div>';
    }
    return '<footer class="ftr"><div class="wrap">' +
      '<div class="ftr__cols"><div class="ftr__brand"><a class="logo logo--inv" href="#/" aria-label="Szamka, strona główna">' + art.logo(30) + '<span class="logo__word">szamka</span></a>' +
      '<p>Jedzenie z okolicznych lokali, prosto pod Twoje drzwi.</p></div>' +
      col('Szamka', ['O nas', 'Kariera', 'Blog', 'Kontakt']) +
      col('Dla partnerów', ['Dodaj swój lokal', 'Zostań kurierem', 'Szamka dla firm']) +
      col('Pomoc', ['Najczęstsze pytania', 'Reklamacje', 'Regulamin', 'Prywatność']) +
      '</div><div class="ftr__bot"><span class="ftr__copy" data-act="secret">© 2026 Szamka</span>' +
      '<span>Serwis demonstracyjny. Zamówienia nie są realizowane ani opłacane.</span></div>' +
      '</div></footer>';
  }
  function shell(body, opt) {
    opt = opt || {};
    return '<a class="skip" href="#main" data-act="skip">Przejdź do treści</a>' + promoBar(opt) + header(opt) + activeBar(opt) +
      '<main id="main" class="main ' + (opt.cls || '') + '" tabindex="-1">' + body + '</main>' + footer() +
      (SZ.admin && !opt.minimal ? SZ.admin.pill(opt) : '');
  }
  function emptyState(title, text, btn, href, kind) {
    return '<div class="wrap"><div class="blank">' + art.dish(kind || 'salatka', 'dish blank__art') + '<h1>' + esc(title) + '</h1><p>' + esc(text) + '</p>' +
      (btn ? '<a class="btn btn--primary btn--lg" href="' + href + '">' + esc(btn) + '</a>' : '') + '</div></div>';
  }

  /* ================= strona główna ================= */
  function rcard(r) {
    return '<a class="rcard' + (r.open ? '' : ' is-closed') + '" href="#/lokal/' + encodeURIComponent(r.id) + '">' +
      '<div class="rcard__cover">' + coverHTML(r) +
      (r.badge ? '<span class="sticker">' + esc(r.badge) + '</span>' : '') +
      (!r.open ? '<span class="rcard__closed">Zamknięte' + (r.opensAt ? ', otwieramy o ' + esc(r.opensAt) : '') + '</span>' : '') +
      '</div><div class="rcard__body">' + logoHTML(r) +
      '<div class="rcard__top"><h3>' + esc(r.name) + '</h3><span class="rate">' + icon('star') + dec(r.rating) + '<i>(' + count(r.reviews) + ')</i></span></div>' +
      '<p class="rcard__kitchen">' + (r.sponsored ? '<span class="tagx">Sponsorowane</span>' : '') + (r.isNew ? '<span class="tagx tagx--new">Nowość</span>' : '') + esc(r.kitchen) + '</p>' +
      '<ul class="meta"><li>' + icon('clock') + esc(r.timeMin) + '–' + esc(r.timeMax) + ' min</li>' +
      '<li' + (r.fee > 0 ? '' : ' class="is-free"') + '>' + icon('bike') + (r.fee > 0 ? zl(r.fee) : 'Darmowa dostawa') + '</li>' +
      '<li>' + icon('bag') + 'Min. ' + zlShort(r.minOrder) + '</li></ul>' +
      '</div></a>';
  }
  function vHome() {
    var st = state.settings;
    var top = visibleR().filter(function (r) { return r.open; }).sort(function (a, b) { return b.rating - a.rating; }).slice(0, 3);
    return shell(
      '<section class="hero"><div class="hero__art">' + art.hero() + '</div><div class="wrap hero__in"><div class="hero__card">' +
      '<h1>' + esc(st.heroTitle) + '</h1><p class="hero__sub">' + esc(st.heroSub) + '</p>' +
      '<form class="addrform" data-form="addr-home"><label class="sr" for="addr-in">Adres dostawy</label>' +
      '<div class="addrform__field">' + icon('pin') + '<input id="addr-in" name="address" type="text" autocomplete="street-address" placeholder="Ulica i numer, miasto" value="' + esc(state.user.address) + '"></div>' +
      '<button class="btn btn--primary btn--lg" type="submit">Pokaż lokale</button></form>' +
      '<p class="hero__hint">Na przykład: Marszałkowska 10, Warszawa</p>' +
      '</div></div></section>' +

      '<section class="wrap sec"><h2>Wybierz kuchnię</h2><div class="kuchnie">' +
      st.cuisines.map(function (c) {
        return '<a class="kuch" href="#/lokale" data-act="pick-cuisine" data-id="' + esc(c.id) + '">' + art.dish(c.art) + '<span>' + esc(c.name) + '</span></a>';
      }).join('') + '</div></section>' +

      (top.length ? '<section class="wrap sec"><div class="sec__head"><h2>Najlepiej oceniane w okolicy</h2><a class="more" href="#/lokale" data-act="pick-cuisine" data-id="all">Wszystkie lokale' + icon('chev-right', 'ic--s') + '</a></div>' +
        '<div class="cards cards--3">' + top.map(rcard).join('') + '</div></section>' : '') +

      '<section class="how"><div class="wrap"><h2>Trzy kroki do obiadu</h2><ol class="how__list">' +
      '<li><b>Wpisz adres</b><span>Pokażemy tylko lokale, które do Ciebie dowożą, razem z czasem i ceną dostawy.</span></li>' +
      '<li><b>Wybierz lokal i dania</b><span>Koszyk od razu liczy dostawę i mówi, ile brakuje do minimalnej kwoty.</span></li>' +
      '<li><b>Śledź kuriera</b><span>Widzisz, kiedy kuchnia kończy i gdzie na mapie jest Twoje jedzenie.</span></li>' +
      '</ol></div></section>', { cls: 'main--home' });
  }

  /* ================= lista lokali ================= */
  var SORTS = { polecane: 'Polecane', ocena: 'Najwyżej oceniane', czas: 'Najszybsza dostawa', dostawa: 'Najtańsza dostawa', minimum: 'Najniższa kwota minimalna' };
  function filtered() {
    var q = fold(ui.q.trim()), f = ui.f;
    var arr = visibleR().filter(function (r) {
      if (ui.cuisine !== 'all' && r.cuisines.indexOf(ui.cuisine) < 0) return false;
      if (f.open && !r.open) return false;
      if (f.free && r.fee > 0) return false;
      if (f.promo && !r.badge) return false;
      if (f.min && r.minOrder > f.min) return false;
      if (f.rating && r.rating < f.rating) return false;
      if (q) {
        var hay = fold(r.name + ' ' + r.kitchen + ' ' + r.menu.map(function (c) { return c.items.map(function (i) { return i.name; }).join(' '); }).join(' '));
        if (hay.indexOf(q) < 0) return false;
      }
      return true;
    });
    var by = {
      polecane: function (a, b) { return (b.sponsored ? 1 : 0) - (a.sponsored ? 1 : 0); },
      ocena: function (a, b) { return b.rating - a.rating; },
      czas: function (a, b) { return a.timeMin - b.timeMin; },
      dostawa: function (a, b) { return a.fee - b.fee; },
      minimum: function (a, b) { return a.minOrder - b.minOrder; }
    }[ui.sort];
    arr = arr.map(function (r, i) { return { r: r, i: i }; }).sort(function (a, b) { return by(a.r, b.r) || a.i - b.i; }).map(function (x) { return x.r; });
    return { open: arr.filter(function (r) { return r.open; }), closed: arr.filter(function (r) { return !r.open; }) };
  }
  function filtersActive() { var f = ui.f; return f.open || f.free || f.promo || f.min || f.rating || ui.cuisine !== 'all' || ui.q.trim(); }
  function resultsHTML() {
    var res = filtered(), n = res.open.length + res.closed.length, addr = state.user.address;
    if (!n) {
      return '<div class="blank blank--in">' + art.dish('salatka', 'dish blank__art') + '<h2>Żaden lokal nie pasuje</h2><p>Zmień filtry albo poszukaj czegoś innego.</p>' +
        '<button class="btn btn--ghost" type="button" data-act="filters-clear">Wyczyść filtry</button></div>';
    }
    var head = '<p class="results__count"><b>' + n + ' ' + plural(n, 'lokal', 'lokale', 'lokali') + '</b> ' +
      (addr ? plural(n, 'dowozi', 'dowożą', 'dowozi') + ' pod adres ' + esc(addr) : 'w okolicy') + '</p>';
    return head + (res.open.length ? '<div class="cards">' + res.open.map(rcard).join('') + '</div>' : '') +
      (res.closed.length ? '<h2 class="results__sub">Teraz zamknięte</h2><div class="cards">' + res.closed.map(rcard).join('') + '</div>' : '');
  }
  function chipsHTML() {
    var all = [{ id: 'all', name: 'Wszystkie', art: null }].concat(state.settings.cuisines);
    return all.map(function (c) {
      return '<button type="button" class="chip' + (ui.cuisine === c.id ? ' is-on' : '') + '" data-act="cuisine" data-id="' + esc(c.id) + '" aria-pressed="' + (ui.cuisine === c.id) + '">' +
        (c.art ? art.dish(c.art, 'dish chip__dish') : '') + esc(c.name) + '</button>';
    }).join('');
  }
  function filtersHTML() {
    var f = ui.f;
    function chk(k, label) { return '<label class="chk"><input type="checkbox" data-on-change="filter" data-k="' + k + '"' + (f[k] ? ' checked' : '') + '><span>' + label + '</span></label>'; }
    function rad(k, v, label) { return '<label class="chk"><input type="radio" name="f-' + k + '" data-on-change="filter" data-k="' + k + '" value="' + v + '"' + (f[k] === v ? ' checked' : '') + '><span>' + label + '</span></label>'; }
    return '<div class="filters__box"><h2>Filtry</h2>' + chk('open', 'Otwarte teraz') + chk('free', 'Darmowa dostawa') + chk('promo', 'Z promocją') +
      '<h3>Minimalna kwota zamówienia</h3>' + rad('min', 0, 'Dowolna') + rad('min', 30, 'Do 30 zł') + rad('min', 40, 'Do 40 zł') +
      '<h3>Ocena</h3>' + rad('rating', 0, 'Dowolna') + rad('rating', 4.5, 'Od 4,5 w górę') + rad('rating', 4.7, 'Od 4,7 w górę') + '</div>';
  }
  function vList() {
    return shell('<div class="wrap listpage">' +
      '<div class="chips" id="chips">' + chipsHTML() + '</div>' +
      '<div class="listpage__grid">' +
      '<aside class="filters' + (ui.filtersOpen ? ' is-open' : '') + '" id="filters">' + filtersHTML() + '</aside>' +
      '<section class="results" aria-label="Lokale">' +
      '<div class="results__bar"><label class="search">' + icon('search') + '<span class="sr">Szukaj lokalu albo dania</span><input type="search" placeholder="Szukaj lokalu albo dania" value="' + esc(ui.q) + '" data-on-input="list-q"></label>' +
      '<button type="button" class="btn btn--ghost filters__toggle" data-act="filters-toggle" aria-expanded="' + ui.filtersOpen + '">' + icon('sliders') + 'Filtry</button>' +
      '<label class="sortsel"><span class="sr">Sortowanie</span><select data-on-change="sort">' + Object.keys(SORTS).map(function (k) {
        return '<option value="' + k + '"' + (ui.sort === k ? ' selected' : '') + '>' + SORTS[k] + '</option>';
      }).join('') + '</select></label></div>' +
      '<div id="results">' + resultsHTML() + '</div></section></div></div>');
  }
  function refreshList() {
    var el = document.getElementById('results'); if (el) el.innerHTML = resultsHTML();
    var ch = document.getElementById('chips'); if (ch) ch.innerHTML = chipsHTML();
  }

  /* ================= strona lokalu ================= */
  function catsOf(r) {
    var pop = [];
    r.menu.forEach(function (c) { c.items.forEach(function (i) { if (i.popular) pop.push(i); }); });
    return (pop.length ? [{ id: 'popularne', name: 'Popularne', items: pop }] : []).concat(r.menu.filter(function (c) { return c.items.length; }));
  }
  function mitem(r, i) {
    var img = safeImg(i.img), n = qtyInBasket(r.id, i.id);
    var vp = i.variants.map(function (v) { return +v.price || 0; });
    var min = (+i.price || 0) + (vp.length ? Math.min.apply(null, vp) : 0);
    var from = vp.length > 1 && Math.max.apply(null, vp) !== Math.min.apply(null, vp);
    return '<button class="mi" type="button" data-act="item" data-iid="' + esc(i.id) + '">' +
      '<span class="mi__txt"><span class="mi__name">' + esc(i.name) + '</span>' + (i.desc ? '<span class="mi__desc">' + esc(i.desc) + '</span>' : '') +
      '<span class="mi__price">' + (from ? 'od ' : '') + zl(min) + '</span></span>' +
      (img ? '<img class="mi__img" src="' + esc(img) + '" alt="" loading="lazy">' : '') +
      '<span class="mi__add' + (n ? ' has-qty' : '') + '" data-qty-for="' + esc(i.id) + '">' + (n ? n : icon('plus')) + '</span></button>';
  }
  function menuHTML(r) {
    var q = fold(ui.menuQ.trim());
    var out = catsOf(r).map(function (c) {
      var items = c.items.filter(function (i) { return !q || fold(i.name + ' ' + i.desc).indexOf(q) >= 0; });
      if (!items.length || (q && c.id === 'popularne')) return '';
      return '<section class="mcat" data-cat="' + esc(c.id) + '"><h2>' + esc(c.name) + '</h2><div class="mcat__list">' +
        items.map(function (i) { return mitem(r, i); }).join('') + '</div></section>';
    }).join('');
    return out || '<p class="mempty">W menu nie ma nic pasującego do „' + esc(ui.menuQ.trim()) + '”.</p>';
  }
  function basketHTML() {
    var b = state.basket, r = getR(b.rid), here = getR(ui.rid);
    if (!b.lines.length || !r) {
      return '<h2 class="basket__h">Koszyk</h2><div class="basket__empty">' + art.dish(here ? here.art : 'pizza') + '<p>Koszyk jest pusty.<br>Wybierz coś z menu.</p></div>';
    }
    var t = totals(b.rid, b.lines), other = ui.rid && ui.rid !== b.rid;
    return '<h2 class="basket__h">Koszyk</h2>' +
      '<p class="basket__from">' + (other ? 'W koszyku masz dania z lokalu ' : 'Zamawiasz z lokalu ') +
      (other ? '<a href="#/lokal/' + encodeURIComponent(r.id) + '">' + esc(r.name) + '</a>' : '<b>' + esc(r.name) + '</b>') + '</p>' +
      linesHTML(b.lines, true) + sumHTML(t) +
      (t.missing > 0 ? '<p class="notice notice--warn">Brakuje ' + zl(t.missing) + ' do minimalnej kwoty zamówienia (' + zlShort(r.minOrder) + ').</p>' :
        t.toFree > 0 ? '<p class="notice">Dodaj jeszcze za ' + zl(t.toFree) + ', a dostawa będzie za darmo.</p>' : '') +
      (r.open ? '' : '<p class="notice notice--warn">Lokal jest teraz zamknięty' + (r.opensAt ? ', otwiera się o ' + esc(r.opensAt) : '') + '.</p>') +
      '<button class="btn btn--primary btn--block btn--lg" type="button" data-act="checkout"' + (t.missing > 0 || !r.open ? ' disabled' : '') + '>Przejdź do kasy</button>' +
      '<button class="linkbtn" type="button" data-act="basket-clear">Opróżnij koszyk</button>';
  }
  function linesHTML(lines, editable) {
    return '<ul class="lines">' + lines.map(function (l) {
      return '<li class="line">' + (editable ?
        '<div class="qty"><button type="button" data-act="dec" data-key="' + esc(l.key) + '" aria-label="Jedna sztuka mniej: ' + esc(l.name) + '">' + icon('minus', 'ic--s') + '</button><span>' + l.qty + '</span>' +
        '<button type="button" data-act="inc" data-key="' + esc(l.key) + '" aria-label="Jedna sztuka więcej: ' + esc(l.name) + '">' + icon('plus', 'ic--s') + '</button></div>' :
        '<span class="line__n">' + esc(l.qty) + '×</span>') +
        '<div class="line__txt"><b>' + esc(l.name) + '</b>' + (l.opts ? '<small>' + esc(l.opts) + '</small>' : '') + '</div>' +
        '<span class="line__price">' + zl(l.price * l.qty) + '</span></li>';
    }).join('') + '</ul>';
  }
  function sumHTML(t) {
    return '<dl class="sum"><div><dt>Wartość dań</dt><dd>' + zl(t.sub) + '</dd></div>' +
      '<div><dt>Dostawa</dt><dd>' + (t.fee > 0 ? zl(t.fee) : 'Za darmo') + '</dd></div>' +
      (t.service > 0 ? '<div><dt>Opłata serwisowa</dt><dd>' + zl(t.service) + '</dd></div>' : '') +
      (t.tip > 0 ? '<div><dt>Napiwek dla kuriera</dt><dd>' + zl(t.tip) + '</dd></div>' : '') +
      (t.disc > 0 ? '<div class="sum__disc"><dt>Rabat</dt><dd>−' + zl(t.disc) + '</dd></div>' : '') +
      '<div class="sum__total"><dt>Razem</dt><dd>' + zl(t.total) + '</dd></div></dl>';
  }
  function bagbarHTML() {
    var b = state.basket, n = basketCount();
    if (!n || !getR(b.rid)) return '';
    return '<button class="bagbar" type="button" data-act="bag-open"><span>' + icon('bag') + 'Koszyk<b class="pill pill--inv">' + n + '</b></span><b>' + zl(totals(b.rid, b.lines).total) + '</b></button>';
  }
  function vRestaurant(id) {
    var r = getR(id);
    if (!r || r.hidden) return shell(emptyState('Nie ma takiego lokalu', 'Mógł zniknąć z okolicy albo link jest nieaktualny.', 'Zobacz inne lokale', '#/lokale', 'obiad'));
    if (ui.rid !== id) { ui.rid = id; ui.menuQ = ''; }
    var cats = catsOf(r);
    return shell(
      '<div class="rhead"><div class="rhead__cover">' + coverHTML(r, true) + '</div><div class="wrap rhead__in">' + logoHTML(r, 'rlogo--xl') +
      '<div class="rhead__txt"><h1>' + esc(r.name) + '</h1><p class="rhead__kitchen">' + esc(r.kitchen) + '</p>' +
      '<ul class="meta meta--lg"><li class="rate">' + icon('star') + dec(r.rating) + '<i>(' + count(r.reviews) + ' ' + plural(+r.reviews, 'opinia', 'opinie', 'opinii') + ')</i></li>' +
      '<li>' + icon('clock') + esc(r.timeMin) + '–' + esc(r.timeMax) + ' min</li>' +
      '<li' + (r.fee > 0 ? '' : ' class="is-free"') + '>' + icon('bike') + (r.fee > 0 ? 'Dostawa ' + zl(r.fee) : 'Darmowa dostawa') + '</li>' +
      '<li>' + icon('bag') + 'Minimum ' + zlShort(r.minOrder) + '</li></ul>' +
      (r.badge ? '<p class="rhead__promo"><span class="sticker sticker--flat">' + esc(r.badge) + '</span></p>' : '') + '</div>' +
      '<button class="btn btn--ghost rhead__info" type="button" data-act="rinfo">' + icon('info') + 'O lokalu</button></div></div>' +
      (!r.open ? '<div class="wrap"><p class="notice notice--warn notice--wide">Lokal jest teraz zamknięty' + (r.opensAt ? ', otwiera się o ' + esc(r.opensAt) : '') + '. Możesz przejrzeć menu, zamówisz po otwarciu.</p></div>' : '') +
      '<div class="wrap rpage"><div class="rpage__menu">' +
      (cats.length ? '<div class="catnav" id="catnav"><div class="catnav__scroll">' + cats.map(function (c, i) {
        return '<button type="button" class="catnav__b' + (i ? '' : ' is-on') + '" data-act="cat" data-id="' + esc(c.id) + '">' + esc(c.name) + '</button>';
      }).join('') + '</div><label class="search search--menu">' + icon('search') + '<span class="sr">Szukaj w menu</span><input type="search" placeholder="Szukaj w menu" value="' + esc(ui.menuQ) + '" data-on-input="menu-q"></label></div>' +
        '<div id="menu">' + menuHTML(r) + '</div>' : '<p class="mempty">Ten lokal nie dodał jeszcze menu.</p>') +
      '</div><aside class="rpage__side" aria-label="Koszyk"><div class="basket" id="basket">' + basketHTML() + '</div></aside></div>' +
      '<div id="bagbar">' + bagbarHTML() + '</div>', { rid: id, cls: 'main--rest' });
  }
  function refreshBasket() {
    var el = document.getElementById('basket'); if (el) el.innerHTML = basketHTML();
    var sh = document.getElementById('sheet-basket'); if (sh) sh.innerHTML = basketHTML();
    var bb = document.getElementById('bagbar'); if (bb) bb.innerHTML = bagbarHTML();
    var co = document.getElementById('co-sum'); if (co) co.innerHTML = coSumHTML();
    var nav = document.querySelector('.hdr');
    if (nav) { var tmp = document.createElement('div'); tmp.innerHTML = header({}); nav.parentNode.replaceChild(tmp.firstChild, nav); }
    var r = getR(ui.rid);
    if (r) {
      document.querySelectorAll('[data-qty-for]').forEach(function (b) {
        var n = qtyInBasket(r.id, b.getAttribute('data-qty-for'));
        b.classList.toggle('has-qty', n > 0);
        b.innerHTML = n ? n : icon('plus');
      });
    }
  }
  function openItem(r, i) {
    var img = safeImg(i.img);
    ui.im = { rid: r.id, iid: i.id, qty: 1 };
    openModal('<form class="im" data-form="item">' +
      (img ? '<img class="im__img" src="' + esc(img) + '" alt="">' : '') +
      '<div class="im__head"><h2>' + esc(i.name) + '</h2><button type="button" class="xbtn" data-act="modal-close" aria-label="Zamknij">' + icon('x') + '</button></div>' +
      (i.desc ? '<p class="im__desc">' + esc(i.desc) + '</p>' : '') +
      (i.variants.length ? '<fieldset class="opts"><legend>Wybierz wariant</legend>' + i.variants.map(function (v, k) {
        return '<label class="opt"><input type="radio" name="v" value="' + k + '"' + (k ? '' : ' checked') + ' data-on-change="im"><span>' + esc(v.name) + '</span><em>' + (v.price > 0 ? '+' + zl(v.price) : '') + '</em></label>';
      }).join('') + '</fieldset>' : '') +
      (i.extras.length ? '<fieldset class="opts"><legend>Dodatki</legend>' + i.extras.map(function (e, k) {
        return '<label class="opt"><input type="checkbox" name="e" value="' + k + '" data-on-change="im"><span>' + esc(e.name) + '</span><em>' + (e.price > 0 ? '+' + zl(e.price) : 'gratis') + '</em></label>';
      }).join('') + '</fieldset>' : '') +
      '<div class="im__foot"><div class="qty qty--lg"><button type="button" data-act="im-dec" aria-label="Jedna sztuka mniej">' + icon('minus') + '</button><span id="im-qty">1</span>' +
      '<button type="button" data-act="im-inc" aria-label="Jedna sztuka więcej">' + icon('plus') + '</button></div>' +
      '<button class="btn btn--primary btn--lg" type="submit" id="im-add"></button></div></form>', { label: i.name, cls: 'modal--item' });
    updateItemModal();
  }
  function itemChoice() {
    var form = modalRoot.querySelector('form.im'), r = getR(ui.im.rid), i = r && getItem(r, ui.im.iid);
    if (!form || !i) return null;
    var v = form.querySelector('input[name="v"]:checked'), vi = v ? +v.value : 0, eis = [];
    form.querySelectorAll('input[name="e"]:checked').forEach(function (e) { eis.push(+e.value); });
    var price = +i.price || 0;
    if (i.variants.length) price += +i.variants[vi].price || 0;
    eis.forEach(function (k) { price += +i.extras[k].price || 0; });
    return { r: r, i: i, vi: vi, eis: eis, price: price };
  }
  function updateItemModal() {
    var c = itemChoice(); if (!c) return;
    document.getElementById('im-qty').textContent = ui.im.qty;
    document.getElementById('im-add').textContent = 'Dodaj za ' + zl(c.price * ui.im.qty);
  }
  var spy = null;
  function setupSpy() {
    if (spy) { window.removeEventListener('scroll', spy); spy = null; }
    var nav = document.getElementById('catnav'); if (!nav) return;
    var tick = false;
    spy = function () {
      if (tick) return; tick = true;
      requestAnimationFrame(function () {
        tick = false;
        var secs = document.querySelectorAll('.mcat'), cur = null, line = nav.getBoundingClientRect().bottom + 24;
        secs.forEach(function (s) { if (s.getBoundingClientRect().top <= line) cur = s.getAttribute('data-cat'); });
        if (!cur && secs.length) cur = secs[0].getAttribute('data-cat');
        nav.querySelectorAll('.catnav__b').forEach(function (b) {
          var on = b.getAttribute('data-id') === cur;
          if (on && !b.classList.contains('is-on')) {
            var sc = b.parentNode; sc.scrollTo({ left: b.offsetLeft - sc.clientWidth / 2 + b.clientWidth / 2, behavior: 'smooth' });
          }
          b.classList.toggle('is-on', on);
        });
      });
    };
    window.addEventListener('scroll', spy, { passive: true });
  }

  /* ================= kasa ================= */
  function splitAddr(a) {
    var p = String(a || '').split(','), street = (p.shift() || '').trim();
    return { street: street, city: p.join(',').trim() };
  }
  function coState() {
    if (!ui.co) ui.co = { tip: 0, voucher: null, pay: 'blik', when: 'asap', slot: 0, vmsg: '' };
    return ui.co;
  }
  function coSumHTML() {
    var b = state.basket, r = getR(b.rid), co = coState();
    if (!r) return '';
    var t = totals(b.rid, b.lines, co);
    return '<h2 class="basket__h">Twoje zamówienie</h2><p class="basket__from">Z lokalu <b>' + esc(r.name) + '</b></p>' + linesHTML(b.lines, false) + sumHTML(t) +
      '<button class="btn btn--primary btn--block btn--lg" type="submit">Zamawiam i płacę ' + zl(t.total) + '</button>' +
      '<p class="co__legal">Klikając, potwierdzasz zamówienie z obowiązkiem zapłaty.</p>';
  }
  function slots(r) {
    var out = [], start = Date.now() + (+r.timeMax || 40) * 60000, q = 15 * 60000;
    start = Math.ceil(start / q) * q;
    for (var i = 0; i < 10; i++) out.push(start + i * q);
    return out;
  }
  function vCheckout() {
    var b = state.basket, r = getR(b.rid);
    if (!r || !b.lines.length) return shell(emptyState('Koszyk jest pusty', 'Wybierz lokal i dodaj coś do koszyka, a potem wróć tutaj.', 'Zobacz lokale', '#/lokale', 'pizza'));
    var co = coState(), u = state.user, a = splitAddr(u.address);
    function field(id, label, val, attrs, hint) {
      return '<div class="fld"><label for="co-' + id + '">' + label + '</label><input id="co-' + id + '" name="' + id + '" value="' + esc(val) + '" ' + (attrs || '') + '>' +
        (hint ? '<small>' + hint + '</small>' : '') + '<p class="fld__err" id="err-' + id + '" hidden></p></div>';
    }
    function payTile(k, sub) {
      return '<label class="tile"><input type="radio" name="pay" value="' + k + '"' + (co.pay === k ? ' checked' : '') + ' data-on-change="co-pay"><span><b>' + PAY[k] + '</b><small>' + sub + '</small></span></label>';
    }
    return shell('<div class="wrap copage"><a class="back" href="#/lokal/' + encodeURIComponent(r.id) + '">' + icon('chev-left', 'ic--s') + 'Wróć do menu</a><h1>Dokończ zamówienie</h1>' +
      '<form class="co" data-form="order" novalidate><div class="co__main">' +
      '<section class="card"><h2>Adres dostawy</h2><div class="grid2">' +
      field('street', 'Ulica i numer', a.street, 'autocomplete="address-line1" required') +
      field('city', 'Miasto', a.city, 'autocomplete="address-level2"') +
      field('apt', 'Numer mieszkania', u.apt, 'inputmode="numeric" autocomplete="address-line2"') +
      field('floor', 'Piętro', u.floor, 'inputmode="numeric"') + '</div>' +
      '<div class="fld"><label for="co-note">Wskazówki dla kuriera</label><textarea id="co-note" name="note" rows="2" placeholder="Na przykład kod do domofonu albo którędy wejść">' + esc(co.note || '') + '</textarea></div></section>' +
      '<section class="card"><h2>Twoje dane</h2><div class="grid2">' +
      field('name', 'Imię i nazwisko', u.name, 'autocomplete="name" required') +
      field('phone', 'Telefon', u.phone, 'type="tel" inputmode="tel" autocomplete="tel" required', 'Kurier zadzwoni, jeśli nie trafi pod drzwi.') + '</div>' +
      field('email', 'E-mail', u.email, 'type="email" autocomplete="email"', 'Tu wyślemy potwierdzenie.') + '</section>' +
      '<section class="card"><h2>Kiedy dostarczyć</h2><div class="tiles">' +
      '<label class="tile"><input type="radio" name="when" value="asap"' + (co.when === 'asap' ? ' checked' : '') + ' data-on-change="co-when"><span><b>Jak najszybciej</b><small>Około ' + esc(r.timeMin) + '–' + esc(r.timeMax) + ' min</small></span></label>' +
      '<label class="tile"><input type="radio" name="when" value="later"' + (co.when === 'later' ? ' checked' : '') + ' data-on-change="co-when"><span><b>Na konkretną godzinę</b><small><select name="slot" data-on-change="co-slot" aria-label="Godzina dostawy">' +
      slots(r).map(function (s, i) { return '<option value="' + s + '"' + (co.slot === s || (!co.slot && !i) ? ' selected' : '') + '>' + whenPL(s) + '</option>'; }).join('') + '</select></small></span></label></div></section>' +
      '<section class="card"><h2>Płatność</h2><div class="tiles tiles--2">' +
      payTile('blik', 'Zatwierdzasz w aplikacji banku') + payTile('karta', 'Visa albo Mastercard') + payTile('portfel', 'Jednym dotknięciem') + payTile('gotowka', 'Płacisz kurierowi') + '</div></section>' +
      '<section class="card"><h2>Napiwek dla kuriera</h2><p class="card__sub">Cała kwota trafia do kuriera.</p><div class="tips" id="tips">' + tipsHTML() + '</div></section>' +
      '<section class="card"><h2>Kod rabatowy</h2><div class="voucher"><input name="voucher" id="co-voucher" placeholder="Wpisz kod" autocapitalize="characters" aria-label="Kod rabatowy" value="' + esc(co.voucher ? co.voucher.code : '') + '">' +
      '<button class="btn btn--ghost" type="button" data-act="voucher">Użyj kodu</button></div><p class="voucher__msg" id="voucher-msg" role="status">' + esc(co.vmsg || '') + '</p></section>' +
      '</div><aside class="co__side"><div class="basket" id="co-sum">' + coSumHTML() + '</div></aside></form></div>', { cls: 'main--soft', noPromo: true });
  }
  function tipsHTML() {
    var co = coState();
    return [0, 3, 5, 10].map(function (v) {
      return '<button type="button" class="chip' + (co.tip === v ? ' is-on' : '') + '" data-act="tip" data-v="' + v + '" aria-pressed="' + (co.tip === v) + '">' + (v ? zlShort(v) : 'Bez napiwku') + '</button>';
    }).join('');
  }

  /* ================= śledzenie zamówienia ================= */
  function headline(o, st) {
    if (st === 'zlozone') return ['Czekamy, aż lokal potwierdzi zamówienie', 'Zwykle trwa to minutę albo dwie.'];
    if (st === 'kuchnia') return [o.rname + ' przygotowuje Twoje zamówienie', 'Kurier odbierze je, gdy tylko będzie gotowe.'];
    if (st === 'droga') return [o.courier.name + ' jedzie do Ciebie', 'Miej telefon pod ręką, kurier może zadzwonić.'];
    if (st === 'dostarczone') return ['Dostarczone. Smacznego!', 'Dziękujemy za zamówienie.'];
    return ['Zamówienie anulowane', 'Nic nie zostało pobrane z Twojego konta.'];
  }
  function etaText(o, st) {
    var t = orderTimes(o), left = Math.ceil((t[3] - Date.now()) / 60000);
    if (st === 'dostarczone' || st === 'anulowane') return '';
    return left > 0 ? 'za ' + left + ' min' : 'lada chwila';
  }
  function stepsHTML(o, st) {
    var t = orderTimes(o), idx = STAGES.indexOf(st), auto = !o.status || o.status === 'auto';
    return '<ol class="steps" style="--p:' + (idx < 0 ? 0 : idx / 3) + '">' + STAGES.map(function (s, i) {
      var cls = i < idx ? 'is-done' : i === idx ? (st === 'dostarczone' ? 'is-done' : 'is-now') : '';
      var time = auto ? (i <= idx ? hhmm(t[i]) : 'ok. ' + hhmm(t[i])) : i === 0 ? hhmm(t[0]) : (i === 3 && idx < 3 ? 'ok. ' + hhmm(t[3]) : '');
      return '<li class="' + cls + '"><span class="steps__dot">' + (i < idx || st === 'dostarczone' ? icon('check', 'ic--s') : '') + '</span><b>' + STATUS[s].step + '</b><small>' + time + '</small></li>';
    }).join('') + '</ol>';
  }
  function orderHTML(o, shared) {
    var st = orderStatus(o), t = orderTimes(o), h = headline(o, st), total = orderTotal(o), sub = orderSub(o);
    var cancelled = st === 'anulowane';
    return '<div class="wrap trk">' +
      (shared ? '' : '<a class="back" href="#/zamowienia">' + icon('chev-left', 'ic--s') + 'Twoje zamówienia</a>') +
      '<div class="trk__grid"><div class="trk__main">' +
      '<section class="card trk__status' + (cancelled ? ' is-cancelled' : '') + '" aria-live="polite">' +
      '<div class="trk__rest">' + logoHTML(o) + '<span>Zamówienie nr ' + esc(o.no) + ' z lokalu <b>' + esc(o.rname) + '</b></span></div>' +
      '<h1>' + esc(h[0]) + '</h1><p class="trk__sub">' + esc(h[1]) + '</p>' +
      (cancelled ? '' : '<div class="eta"><span class="eta__label">' + (st === 'dostarczone' ? 'Dostarczono o' : 'Dostawa około') + '</span>' +
        '<span class="eta__time">' + hhmm(st === 'dostarczone' && o.status === 'dostarczone' ? Math.min(t[3], Date.now()) : t[3]) + '</span>' +
        (st === 'dostarczone' ? '' : '<span class="eta__left" id="eta-left">' + esc(etaText(o, st)) + '</span>') + '</div>' + stepsHTML(o, st)) +
      '</section>' +
      (cancelled ? '' : '<section class="card trk__mapcard"><div class="trk__map" id="map">' + art.map() + '</div>' +
        '<div class="courier">' + (st === 'droga' || st === 'dostarczone' ?
          '<span class="avatar">' + esc(initials(o.courier.name)) + '</span><div><b>' + esc(o.courier.name) + '</b><small>Twój kurier, ' + (st === 'dostarczone' ? 'przyjechał ' : 'jedzie ') + (VEHICLES[o.courier.vehicle] || VEHICLES.rower) + '</small></div>' :
          '<span class="avatar avatar--wait">' + icon('bike') + '</span><div><b>Szukamy kuriera w pobliżu</b><small>Przydzielimy go, zanim kuchnia skończy.</small></div>') +
        '</div></section>') +
      '</div><aside class="trk__side"><section class="card"><h2>Szczegóły zamówienia</h2>' +
      '<p class="trk__when">Złożone ' + whenPL(t[0]) + '</p>' + linesHTML(o.items, false) +
      sumHTML({ sub: sub, fee: +o.fee || 0, service: +o.service || 0, tip: +o.tip || 0, disc: +o.disc || 0, total: total }) +
      '<dl class="facts">' + (o.address ? '<div><dt>' + icon('pin', 'ic--s') + 'Adres</dt><dd>' + esc(o.address) + '</dd></div>' : '') +
      (o.customer && o.customer.name ? '<div><dt>' + icon('user', 'ic--s') + 'Odbiorca</dt><dd>' + esc(o.customer.name) + '</dd></div>' : '') +
      '<div><dt>' + icon('receipt', 'ic--s') + 'Płatność</dt><dd>' + esc(o.pay || 'BLIK') + '</dd></div>' +
      (o.note ? '<div><dt>' + icon('info', 'ic--s') + 'Dla kuriera</dt><dd>' + esc(o.note) + '</dd></div>' : '') + '</dl>' +
      (shared ? '' : '<div class="trk__btns"><button class="btn btn--ghost btn--block" type="button" data-act="order-share">' + icon('share') + 'Udostępnij śledzenie</button>' +
        (getR(o.rid) ? '<button class="btn btn--ghost btn--block" type="button" data-act="order-again">' + icon('bag') + 'Zamów to samo jeszcze raz</button>' : '') + '</div>') +
      '</section></aside></div></div>';
  }
  function placeCourier() {
    var o = ui.order && ui.order.o, box = document.getElementById('map');
    if (!o || !box) return;
    var path = box.querySelector('.map__done'), courier = box.querySelector('.map__courier');
    if (!path || !courier || !path.getTotalLength) return;
    var st = orderStatus(o), p = rideProgress(o), len = path.getTotalLength(), pt = path.getPointAtLength(len * p);
    path.style.strokeDasharray = len;
    path.style.strokeDashoffset = len * (1 - p);
    courier.removeAttribute('transform');
    courier.style.transform = 'translate(' + pt.x.toFixed(1) + 'px,' + pt.y.toFixed(1) + 'px)';
    courier.style.display = st === 'droga' ? '' : 'none';
    box.classList.toggle('is-delivered', st === 'dostarczone');
  }
  var orderTimer = 0;
  function stopTimers() { clearInterval(orderTimer); orderTimer = 0; }
  function startOrderTimer() {
    stopTimers();
    if (!ui.order) return;
    ui.order.st = orderStatus(ui.order.o);
    placeCourier();
    maybeReveal();
    orderTimer = setInterval(function () {
      var o = ui.order && ui.order.o; if (!o) return stopTimers();
      var st = orderStatus(o);
      if (st !== ui.order.st) { render(true); return; }
      var el = document.getElementById('eta-left');
      if (el && st !== 'dostarczone') el.textContent = etaText(o, st);
      placeCourier();
    }, 1000);
  }
  function maybeReveal() {
    var x = ui.order; if (!x) return;
    var o = x.o, rv = o.reveal;
    if (!rv || (!rv.on && !x.force)) return;
    if (!x.force && (orderStatus(o) !== 'dostarczone' || (!x.shared && o.revealSeen) || x.shown)) return;
    x.shown = true; x.force = false;
    if (!x.shared && !o.revealSeen) { o.revealSeen = true; save(); }
    openModal('<div class="reveal"><svg class="reveal__art" viewBox="0 0 120 120" aria-hidden="true"><circle cx="62" cy="64" r="57" fill="#000" opacity=".1"/><circle cx="60" cy="60" r="57" fill="#fff"/>' +
      '<circle cx="60" cy="60" r="46" fill="none" stroke="#ECE6E1" stroke-width="1.5"/><g fill="#D9A45B"><circle cx="34" cy="70" r="1.6"/><circle cx="86" cy="74" r="2"/><circle cx="80" cy="34" r="1.3"/><circle cx="40" cy="38" r="1.2"/><circle cx="62" cy="90" r="1"/></g>' +
      '<circle cx="49" cy="52" r="3.2" fill="#24152B"/><circle cx="71" cy="52" r="3.2" fill="#24152B"/><path d="M44 64c6 9 26 9 32 0" fill="none" stroke="#24152B" stroke-width="3" stroke-linecap="round"/></svg>' +
      '<h2>' + esc(rv.title || 'To był żart!') + '</h2><p>' + esc(rv.text || '') + '</p>' +
      '<button class="btn btn--primary btn--lg" type="button" data-act="modal-close" autofocus>No dobra</button></div>', { label: rv.title || 'To był żart', cls: 'modal--reveal' });
    confetti();
  }
  function confetti() {
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var c = document.createElement('canvas'), ctx = c.getContext('2d'); if (!ctx) return;
    var W = c.width = window.innerWidth, H = c.height = window.innerHeight;
    c.className = 'confetti'; document.body.appendChild(c);
    var cols = ['#E0312B', '#FFCE3A', '#17834E', '#24152B', '#F2835A', '#7FB9E6'], ps = [], t0 = performance.now();
    for (var i = 0; i < 120; i++) ps.push({ x: W / 2 + (Math.random() - .5) * 120, y: H * .35, vx: (Math.random() - .5) * 14, vy: -6 - Math.random() * 10, s: 5 + Math.random() * 6, r: Math.random() * 6.3, vr: (Math.random() - .5) * .4, c: cols[i % cols.length] });
    (function frame(now) {
      var dt = now - t0;
      ctx.clearRect(0, 0, W, H);
      ps.forEach(function (p) {
        p.vy += 0.28; p.vx *= 0.99; p.x += p.vx; p.y += p.vy; p.r += p.vr;
        ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.fillStyle = p.c; ctx.globalAlpha = Math.max(0, 1 - dt / 3200);
        ctx.fillRect(-p.s / 2, -p.s / 3, p.s, p.s * .66); ctx.restore();
      });
      if (dt < 3200) requestAnimationFrame(frame); else if (c.parentNode) c.parentNode.removeChild(c);
    })(t0);
  }
  function vOrderPage(id, extra) {
    var o = getOrder(id);
    if (!o) { ui.order = null; return shell(emptyState('Nie ma takiego zamówienia', 'Mogło zostać usunięte albo link jest nieaktualny.', 'Twoje zamówienia', '#/zamowienia', 'obiad')); }
    if (!ui.order || ui.order.o !== o) ui.order = { o: o, shared: false };
    if (extra === 'zart' && !ui.order.zartDone) { ui.order.force = true; ui.order.zartDone = true; }
    return shell(orderHTML(o, false), { orderId: id, cls: 'main--soft', noPromo: true });
  }
  function vShared(payload) {
    if (ui.sharedKey !== payload) {
      ui.sharedKey = payload; ui.shared = null; ui.sharedErr = false; ui.order = null;
      unpack(payload).then(function (x) { ui.shared = fromShare(x); render(true); }).catch(function () { ui.sharedErr = true; render(true); });
    }
    if (ui.sharedErr) return shell(emptyState('Ten link nie działa', 'Jest niepełny albo uszkodzony. Poproś o wysłanie go jeszcze raz.', 'Przejdź do Szamki', '#/', 'obiad'), { minimal: true });
    if (!ui.shared) return shell('<div class="wrap"><p class="loading">Wczytujemy zamówienie…</p></div>', { minimal: true });
    if (!ui.order || ui.order.o !== ui.shared) ui.order = { o: ui.shared, shared: true };
    return shell(orderHTML(ui.shared, true), { minimal: true, cls: 'main--soft' });
  }
  function vOrders() {
    var list = state.orders.slice().sort(function (a, b) { return b.placedAt - a.placedAt; });
    if (!list.length) return shell(emptyState('Nie masz jeszcze zamówień', 'Gdy coś zamówisz, znajdziesz to tutaj razem ze śledzeniem dostawy.', 'Zobacz lokale', '#/lokale', 'burger'));
    return shell('<div class="wrap hist"><h1>Twoje zamówienia</h1><ul class="hist__list">' + list.map(function (o) {
      var st = orderStatus(o), n = o.items.reduce(function (a, i) { return a + (+i.qty || 0); }, 0);
      var names = o.items.slice(0, 3).map(function (i) { return (i.qty > 1 ? i.qty + '× ' : '') + i.name; }).join(', ') + (o.items.length > 3 ? ' i jeszcze ' + (o.items.length - 3) : '');
      return '<li class="hrow">' + logoHTML(o) + '<div class="hrow__txt"><a href="#/zamowienie/' + esc(o.id) + '"><b>' + esc(o.rname) + '</b></a>' +
        '<span class="hrow__items">' + esc(names || 'Bez pozycji') + '</span><span class="hrow__meta">' + whenPL(o.placedAt) + ', ' + n + ' ' + plural(n, 'pozycja', 'pozycje', 'pozycji') + ', nr ' + esc(o.no) + '</span></div>' +
        '<div class="hrow__end"><span class="status status--' + st + '">' + STATUS[st].chip + '</span><b>' + zl(orderTotal(o)) + '</b>' +
        '<a class="btn btn--ghost btn--small" href="#/zamowienie/' + esc(o.id) + '">' + (st === 'dostarczone' || st === 'anulowane' ? 'Szczegóły' : 'Śledź') + '</a></div></li>';
    }).join('') + '</ul></div>', { cls: 'main--soft' });
  }

  /* ================= router ================= */
  function parseHash() {
    var p = location.hash.replace(/^#\/?/, '').split('/');
    var dec1 = function (s) { try { return decodeURIComponent(s || ''); } catch (e) { return s || ''; } };
    return { name: p[0] || '', a: dec1(p[1]), b: dec1(p[2]), c: dec1(p[3]) };
  }
  var TITLES = { '': 'Szamka: jedzenie z dostawą', lokale: 'Lokale z dostawą | Szamka', kasa: 'Kasa | Szamka', zamowienia: 'Twoje zamówienia | Szamka', admin: 'Panel | Szamka' };
  function render(keepScroll) {
    var rt = parseHash(), key = location.hash, html, changed = key !== ui.route;
    stopTimers();
    if (changed) closeModal(true);
    if (rt.name !== 'zamowienie' && rt.name !== 's') ui.order = null;
    if (rt.name !== 'lokal') ui.rid = null;
    switch (rt.name) {
      case '': html = vHome(); break;
      case 'lokale': html = vList(); break;
      case 'lokal': html = vRestaurant(rt.a); break;
      case 'kasa': html = vCheckout(); break;
      case 'zamowienie': html = vOrderPage(rt.a, rt.b); break;
      case 'zamowienia': html = vOrders(); break;
      case 's': html = vShared(rt.a); break;
      case 'admin': html = SZ.admin ? SZ.admin.view(rt) : null; break;
      default: html = null;
    }
    if (html == null) html = shell(emptyState('Nie ma takiej strony', 'Sprawdź adres albo wróć na stronę główną.', 'Strona główna', '#/', 'obiad'));
    app.innerHTML = html;
    var r = rt.name === 'lokal' && getR(rt.a), o = ui.order && ui.order.o;
    document.title = r ? r.name + ': menu i dostawa | Szamka' : o ? 'Zamówienie z ' + o.rname + ' | Szamka' : (TITLES[rt.name] || TITLES['']);
    if (rt.name === 'lokal') setupSpy(); else if (spy) { window.removeEventListener('scroll', spy); spy = null; }
    if (rt.name === 'zamowienie' || rt.name === 's') startOrderTimer();
    if (rt.name === 'admin' && SZ.admin && SZ.admin.after) SZ.admin.after(rt);
    if (changed && keepScroll !== true) window.scrollTo(0, 0);
    ui.route = key;
  }

  /* ================= akcje ================= */
  var actions = {}, forms = {}, onInput = {}, onChange = {};

  actions['modal-close'] = function () { closeModal(); };
  actions['confirm-ok'] = function () { var cb = confirmCb; confirmCb = null; closeModal(true); if (cb) cb(); };
  actions.soon = function () { toast('Ta podstrona jest jeszcze w przygotowaniu.'); };
  actions.skip = function (el, e) { e.preventDefault(); var m = document.getElementById('main'); if (m) m.focus(); };
  var taps = [];
  actions.secret = function () {
    var now = Date.now();
    taps = taps.filter(function (t) { return now - t < 2500; }); taps.push(now);
    if (taps.length >= 5) { taps = []; location.hash = '#/admin'; }
  };

  actions['addr-open'] = function () {
    openModal('<form class="dlg" data-form="addr"><h2>Dokąd dowieźć?</h2><p>Od adresu zależy, które lokale dowożą i ile kosztuje dostawa.</p>' +
      '<div class="fld"><label for="addr-m">Adres dostawy</label><input id="addr-m" name="address" autocomplete="street-address" placeholder="Ulica i numer, miasto" value="' + esc(state.user.address) + '" autofocus></div>' +
      '<div class="dlg__btns"><button class="btn btn--ghost" type="button" data-act="modal-close">Anuluj</button><button class="btn btn--primary" type="submit">Zapisz adres</button></div></form>',
    { label: 'Adres dostawy', cls: 'modal--small' });
  };
  function setAddress(v) { state.user.address = String(v || '').trim().slice(0, 140); save(); }
  forms.addr = function (f) { setAddress(f.elements.namedItem('address').value); closeModal(true); render(true); };
  forms['addr-home'] = function (f) {
    var inp = f.elements.namedItem('address'), v = inp.value.trim();
    if (!v) { inp.focus(); toast('Wpisz adres, żeby zobaczyć lokale w okolicy.'); return; }
    setAddress(v); ui.cuisine = 'all'; location.hash = '#/lokale';
  };
  actions['pick-cuisine'] = function (el) { ui.cuisine = el.getAttribute('data-id') || 'all'; ui.q = ''; };
  actions.cuisine = function (el) { ui.cuisine = el.getAttribute('data-id'); refreshList(); };
  actions['filters-clear'] = function () {
    ui.cuisine = 'all'; ui.q = ''; ui.f = { open: false, free: false, promo: false, min: 0, rating: 0 }; render(true);
  };
  actions['filters-toggle'] = function (el) {
    ui.filtersOpen = !ui.filtersOpen;
    var f = document.getElementById('filters'); if (f) f.classList.toggle('is-open', ui.filtersOpen);
    el.setAttribute('aria-expanded', ui.filtersOpen);
  };
  onChange.filter = function (el) {
    var k = el.getAttribute('data-k');
    ui.f[k] = el.type === 'checkbox' ? el.checked : +el.value;
    refreshList();
  };
  onChange.sort = function (el) { ui.sort = el.value; refreshList(); };
  onInput['list-q'] = function (el) { ui.q = el.value; refreshList(); };

  onInput['menu-q'] = function (el) {
    ui.menuQ = el.value;
    var r = getR(ui.rid), m = document.getElementById('menu');
    if (r && m) m.innerHTML = menuHTML(r);
  };
  actions.cat = function (el) {
    var id = el.getAttribute('data-id'), sec = null, nav = document.getElementById('catnav');
    document.querySelectorAll('.mcat').forEach(function (x) { if (x.getAttribute('data-cat') === id) sec = x; });
    if (!sec) return;
    var off = (nav ? nav.offsetHeight : 0) + 64 + 12;
    window.scrollTo({ top: sec.getBoundingClientRect().top + window.pageYOffset - off, behavior: 'smooth' });
  };
  actions.item = function (el) {
    var r = getR(ui.rid), i = r && getItem(r, el.getAttribute('data-iid'));
    if (!i) return;
    if (!r.open) { toast('Lokal jest teraz zamknięty' + (r.opensAt ? ', otwiera się o ' + r.opensAt : '') + '.'); return; }
    if (i.variants.length || i.extras.length || safeImg(i.img)) { openItem(r, i); return; }
    withBasketFor(r.id, function () { addLine(r.id, i, 0, [], 1); toast('Dodano do koszyka: ' + i.name); });
  };
  onChange.im = function () { updateItemModal(); };
  actions['im-inc'] = function () { ui.im.qty = Math.min(50, ui.im.qty + 1); updateItemModal(); };
  actions['im-dec'] = function () { ui.im.qty = Math.max(1, ui.im.qty - 1); updateItemModal(); };
  forms.item = function () {
    var c = itemChoice(); if (!c) return;
    var qty = ui.im.qty;
    closeModal(true);
    withBasketFor(c.r.id, function () { addLine(c.r.id, c.i, c.vi, c.eis, qty); toast('Dodano do koszyka: ' + c.i.name); });
  };
  function changeQty(key, d) {
    var b = state.basket, l = b.lines.find(function (x) { return x.key === key; });
    if (!l) return;
    l.qty += d;
    if (l.qty <= 0) b.lines = b.lines.filter(function (x) { return x !== l; });
    if (!b.lines.length) b.rid = null;
    save(); refreshBasket();
    if (!b.lines.length && parseHash().name === 'kasa') render(true);
  }
  actions.inc = function (el) { changeQty(el.getAttribute('data-key'), 1); };
  actions.dec = function (el) { changeQty(el.getAttribute('data-key'), -1); };
  actions['basket-clear'] = function () { state.basket = { rid: null, lines: [] }; save(); refreshBasket(); };
  actions['bag-open'] = function () {
    openModal('<div class="sheet"><button type="button" class="xbtn sheet__x" data-act="modal-close" aria-label="Zamknij koszyk">' + icon('x') + '</button><div class="basket basket--sheet" id="sheet-basket">' + basketHTML() + '</div></div>',
      { label: 'Koszyk', cls: 'modal--sheet' });
  };
  actions.checkout = function () { closeModal(true); ui.co = null; location.hash = '#/kasa'; };
  actions.rinfo = function () {
    var r = getR(ui.rid); if (!r) return;
    openModal('<div class="dlg"><h2>' + esc(r.name) + '</h2><dl class="facts facts--dlg">' +
      '<div><dt>' + icon('store', 'ic--s') + 'Adres lokalu</dt><dd>' + esc(r.address || 'Nie podano') + '</dd></div>' +
      '<div><dt>' + icon('clock', 'ic--s') + 'Dziś</dt><dd>' + (r.open ? 'Otwarte, przyjmuje zamówienia' : 'Zamknięte' + (r.opensAt ? ', otwiera się o ' + esc(r.opensAt) : '')) + '</dd></div>' +
      '<div><dt>' + icon('bike', 'ic--s') + 'Dostawa</dt><dd>' + (r.fee > 0 ? zl(r.fee) : 'Za darmo') + (r.freeFrom > 0 && r.fee > 0 ? ', za darmo od ' + zlShort(r.freeFrom) : '') + '</dd></div>' +
      '<div><dt>' + icon('bag', 'ic--s') + 'Minimalna kwota</dt><dd>' + zlShort(r.minOrder) + '</dd></div>' +
      '<div><dt>' + icon('star', 'ic--s') + 'Ocena</dt><dd>' + dec(r.rating) + ' na 5, ' + count(r.reviews) + ' ' + plural(+r.reviews, 'opinia', 'opinie', 'opinii') + '</dd></div></dl>' +
      '<div class="dlg__btns"><button class="btn btn--primary" type="button" data-act="modal-close" autofocus>Zamknij</button></div></div>', { label: 'O lokalu', cls: 'modal--small' });
  };

  /* --- kasa --- */
  function refreshCoSum() { var el = document.getElementById('co-sum'); if (el) el.innerHTML = coSumHTML(); }
  actions.tip = function (el) { coState().tip = +el.getAttribute('data-v') || 0; var t = document.getElementById('tips'); if (t) t.innerHTML = tipsHTML(); refreshCoSum(); };
  onChange['co-pay'] = function (el) { coState().pay = el.value; };
  onChange['co-when'] = function (el) { coState().when = el.value; };
  onChange['co-slot'] = function (el) {
    var co = coState(); co.slot = +el.value; co.when = 'later';
    var rd = document.querySelector('input[name="when"][value="later"]'); if (rd) rd.checked = true;
  };
  actions.voucher = function () {
    var inp = document.getElementById('co-voucher'), msg = document.getElementById('voucher-msg'), co = coState();
    var code = (inp.value || '').trim().toUpperCase();
    var v = state.settings.vouchers.find(function (x) { return String(x.code || '').toUpperCase() === code; });
    if (!code) { co.voucher = null; co.vmsg = ''; }
    else if (!v) { co.voucher = null; co.vmsg = 'Nie znamy kodu ' + code + '. Sprawdź, czy nie ma literówki.'; }
    else {
      co.voucher = { code: code, kind: v.kind, value: +v.value || 0 };
      co.vmsg = v.kind === 'dostawa' ? 'Kod działa: dostawa za darmo.' : v.kind === 'procent' ? 'Kod działa: ' + (+v.value) + '% taniej.' : 'Kod działa: ' + zlShort(v.value) + ' taniej.';
    }
    msg.textContent = co.vmsg; msg.classList.toggle('is-ok', !!co.voucher);
    refreshCoSum();
  };
  function fv(f, k) { var el = f.elements.namedItem(k); return el ? String(el.value || '').trim() : ''; }
  function fe(f, k) { return f.elements.namedItem(k); }
  onInput.co = function (el) {
    var u = state.user, f = el.form; if (!f) return;
    if (el.name === 'street' || el.name === 'city') u.address = [fv(f, 'street'), fv(f, 'city')].filter(Boolean).join(', ');
    else if (el.name === 'note') coState().note = el.value;
    else if (u.hasOwnProperty(el.name)) u[el.name] = el.value;
    var err = document.getElementById('err-' + el.name);
    if (err && !err.hidden) { err.hidden = true; el.removeAttribute('aria-invalid'); }
    saveSoon();
  };
  forms.order = function (f) {
    var b = state.basket, r = getR(b.rid), co = coState();
    if (!r || !b.lines.length) return;
    if (!r.open) { toast('Lokal jest teraz zamknięty' + (r.opensAt ? ', otwiera się o ' + r.opensAt : '') + '.'); return; }
    var errs = {};
    if (!fv(f, 'street')) errs.street = 'Wpisz ulicę i numer domu.';
    if (!fv(f, 'name')) errs.name = 'Wpisz imię i nazwisko odbiorcy.';
    if (fv(f, 'phone').replace(/\D/g, '').length < 9) errs.phone = 'Wpisz numer telefonu, minimum 9 cyfr.';
    if (fv(f, 'email') && !/^\S+@\S+\.\S+$/.test(fv(f, 'email'))) errs.email = 'Ten adres e-mail wygląda na niepełny.';
    ['street', 'name', 'phone', 'email'].forEach(function (k) {
      var e = document.getElementById('err-' + k), inp = fe(f, k);
      if (e) { e.hidden = !errs[k]; e.textContent = errs[k] || ''; }
      if (inp) inp.setAttribute('aria-invalid', errs[k] ? 'true' : 'false');
    });
    var first = Object.keys(errs)[0];
    if (first) { fe(f, first).focus(); return; }
    var t = totals(b.rid, b.lines, co);
    if (t.missing > 0) { toast('Brakuje ' + zl(t.missing) + ' do minimalnej kwoty zamówienia.'); return; }
    var u = state.user;
    u.name = fv(f, 'name'); u.phone = fv(f, 'phone'); u.email = fv(f, 'email');
    u.apt = fv(f, 'apt'); u.floor = fv(f, 'floor');
    u.address = [fv(f, 'street'), fv(f, 'city')].filter(Boolean).join(', ');
    var full = fv(f, 'street') + (u.apt ? ' m. ' + u.apt : '') + (u.floor ? ', piętro ' + u.floor : '') + (fv(f, 'city') ? ', ' + fv(f, 'city') : '');
    var minutes = 0;
    if (co.when === 'later') { var slot = +fv(f, 'slot') || 0; minutes = Math.max(10, Math.round((slot - Date.now()) / 60000)); }
    var o = newOrder(r, b.lines, { tip: co.tip, voucher: co.voucher, address: full, pay: PAY[co.pay] || PAY.blik, note: fv(f, 'note'), minutes: minutes });
    openModal('<div class="sending"><span class="spinner" aria-hidden="true"></span><h2>Wysyłamy zamówienie do lokalu</h2><p>To potrwa tylko chwilę.</p></div>', { label: 'Wysyłamy zamówienie', cls: 'modal--small', locked: true });
    setTimeout(function () {
      o.placedAt = Date.now();
      state.orders.push(o); state.basket = { rid: null, lines: [] }; ui.co = null;
      save(); closeModal(true);
      location.hash = '#/zamowienie/' + o.id;
    }, 1500);
  };

  /* --- zamówienie --- */
  actions['order-share'] = function () {
    var o = ui.order && ui.order.o; if (!o) return;
    shareLink(o).then(function (url) {
      var local = location.protocol === 'file:';
      openModal('<div class="dlg"><h2>Link do śledzenia</h2><p>Kto otworzy ten link, zobaczy to zamówienie na żywo: status, mapę i szczegóły.</p>' +
        '<div class="fld"><label for="share-url">Link</label><input id="share-url" readonly value="' + esc(url) + '" data-act="select-all"></div>' +
        (local ? '<p class="notice notice--warn">Strona jest teraz otwarta z pliku na dysku. Link zadziała u innych dopiero, gdy strona będzie w internecie.</p>' : '') +
        '<div class="dlg__btns"><button class="btn btn--ghost" type="button" data-act="modal-close">Zamknij</button>' +
        (navigator.share ? '<button class="btn btn--ghost" type="button" data-act="share-native">' + icon('share') + 'Wyślij dalej</button>' : '') +
        '<button class="btn btn--primary" type="button" data-act="share-copy" autofocus>' + icon('copy') + 'Skopiuj link</button></div></div>', { label: 'Link do śledzenia', cls: 'modal--small' });
    });
  };
  actions['select-all'] = function (el) { el.select(); };
  actions['share-copy'] = function () {
    var inp = document.getElementById('share-url'); if (!inp) return;
    copyText(inp.value).then(function (ok) { toast(ok ? 'Link skopiowany.' : 'Nie udało się skopiować. Zaznacz link i skopiuj go ręcznie.'); if (ok) closeModal(); });
  };
  actions['share-native'] = function () {
    var inp = document.getElementById('share-url'); if (!inp || !navigator.share) return;
    navigator.share({ title: 'Zamówienie w Szamce', url: inp.value }).catch(function () { /* anulowane */ });
  };
  actions['order-again'] = function () {
    var o = ui.order && ui.order.o, r = o && getR(o.rid); if (!r) return;
    withBasketFor(r.id, function () {
      state.basket = { rid: r.id, lines: o.items.map(function (i, k) { return { key: 'p' + k + '|' + i.name + '|' + i.opts, iid: '', name: i.name, opts: i.opts || '', price: +i.price || 0, qty: +i.qty || 1 }; }) };
      save(); location.hash = '#/lokal/' + encodeURIComponent(r.id);
    });
  };

  /* ================= start ================= */
  function closest(el, sel) { return el && el.closest ? el.closest(sel) : null; }
  function boot() {
    app = document.getElementById('app'); modalRoot = document.getElementById('modal-root'); toastRoot = document.getElementById('toast-root');
    document.getElementById('sprite').innerHTML = art.sprite();
    load();
    document.addEventListener('click', function (e) {
      var el = closest(e.target, '[data-act]'); if (!el) return;
      var fn = actions[el.getAttribute('data-act')]; if (fn) fn(el, e);
    });
    document.addEventListener('submit', function (e) {
      var f = closest(e.target, 'form[data-form]'); if (!f) return;
      e.preventDefault();
      var fn = forms[f.getAttribute('data-form')]; if (fn) fn(f, e);
    });
    document.addEventListener('input', function (e) {
      var el = closest(e.target, '[data-on-input]');
      if (el && onInput[el.getAttribute('data-on-input')]) onInput[el.getAttribute('data-on-input')](el, e);
      else if (closest(e.target, 'form[data-form="order"]')) onInput.co(e.target, e);
      if (SZ.admin && SZ.admin.onInput) SZ.admin.onInput(e);
    });
    document.addEventListener('change', function (e) {
      var el = closest(e.target, '[data-on-change]');
      if (el && onChange[el.getAttribute('data-on-change')]) onChange[el.getAttribute('data-on-change')](el, e);
      if (SZ.admin && SZ.admin.onChange) SZ.admin.onChange(e);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && modalRoot.firstChild && !modalRoot.querySelector('.modal__back:not([data-act])')) closeModal();
    });
    window.addEventListener('hashchange', function () { render(); });
    window.addEventListener('storage', function (e) { if (e.key === KEY) { load(); render(true); } });
    render();
  }

  SZ.app = {
    s: function () { return state; }, replace: function (next) { state = next; normalize(); },
    fresh: fresh, load: load, save: save, saveSoon: saveSoon, render: render, shell: shell, KEY: KEY,
    esc: esc, zl: zl, zlShort: zlShort, dec: dec, count: count, icon: icon, uid: uid, clone: clone, clamp: clamp, r2: r2, hhmm: hhmm, whenPL: whenPL, plural: plural,
    safeImg: safeImg, initials: initials, toast: toast, openModal: openModal, closeModal: closeModal, confirmBox: confirmBox,
    getR: getR, getOrder: getOrder, coverHTML: coverHTML, logoHTML: logoHTML, rcard: rcard, parseHash: parseHash,
    orderStatus: orderStatus, orderTimes: orderTimes, orderTotal: orderTotal, orderSub: orderSub, newOrder: newOrder, shareLink: shareLink, copyText: copyText,
    STATUS: STATUS, STAGES: STAGES, VEHICLES: VEHICLES, PAY: PAY, actions: actions, forms: forms, ui: ui
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
