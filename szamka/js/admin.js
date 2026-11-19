/* Szamka: panel admina. Wejście: adres kończący się na #/admin albo pięć szybkich kliknięć w „© 2026 Szamka” w stopce.
   Panel edytuje ten sam stan co sklep, więc zmiany widać od razu po powrocie na stronę. */
(function () {
  'use strict';
  var SZ = window.SZ, A = SZ.app, art = SZ.art;
  var esc = A.esc, zl = A.zl, icon = A.icon, toast = A.toast;
  var UNLOCK = 'szamka:admin', memUnlocked = false, ctx = null, pinError = false;

  function S() { return A.s(); }
  function unlocked() {
    try { return sessionStorage.getItem(UNLOCK) === '1'; } catch (e) { return memUnlocked; }
  }
  function setUnlocked(v) {
    memUnlocked = v;
    try { if (v) sessionStorage.setItem(UNLOCK, '1'); else sessionStorage.removeItem(UNLOCK); } catch (e) { /* tryb prywatny */ }
  }
  function touch() { S().meta.edited = true; }
  var flashT = 0;
  function flash() {
    var el = document.getElementById('adm-saved'); if (!el) return;
    el.classList.add('is-on'); clearTimeout(flashT);
    flashT = setTimeout(function () { el.classList.remove('is-on'); }, 1400);
  }
  function commit() { touch(); A.save(); flash(); }
  function rerender() { A.render(true); }

  /* ---------- dostęp do pól po ścieżce, np. restaurants.3.menu.0.items.2.price ---------- */
  function getPath(path) { return path.split('.').reduce(function (o, k) { return o == null ? undefined : o[k]; }, S()); }
  function setPath(path, val) {
    var ks = path.split('.'), last = ks.pop();
    var o = ks.reduce(function (acc, k) { return acc == null ? undefined : acc[k]; }, S());
    if (o != null) o[last] = val;
  }
  function parseNum(v) { var n = parseFloat(String(v).replace(',', '.').replace(/[^\d.\-]/g, '')); return isFinite(n) ? n : 0; }
  function numStr(v) { return v == null || v === '' ? '' : String(v).replace('.', ','); }
  function pad(n) { return n < 10 ? '0' + n : '' + n; }
  function toLocal(ts) { var d = new Date(ts); return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + 'T' + pad(d.getHours()) + ':' + pad(d.getMinutes()); }
  function pairsToText(arr) {
    return (arr || []).map(function (p) { return p.name + (p.price ? ' | ' + numStr(p.price) : ''); }).join('\n');
  }
  function textToPairs(txt) {
    return String(txt || '').split('\n').map(function (l) {
      var p = l.split(/[|;]/), name = (p[0] || '').trim();
      return name ? { name: name.slice(0, 80), price: A.r2(Math.max(0, parseNum(p[1] || 0))) } : null;
    }).filter(Boolean);
  }

  /* ---------- klocki formularzy ---------- */
  function inp(label, path, o) {
    o = o || {};
    var t = o.t || 'text', v = getPath(path);
    var val = t === 'num' || t === 'int' ? numStr(v) : t === 'time' ? toLocal(v || Date.now()) : t === 'list' ? (v || []).join(', ') : (v == null ? '' : v);
    return '<div class="fld ' + (o.cls || '') + '"><label>' + label + '<input' + (t === 'time' ? ' type="datetime-local"' : t === 'pin' ? ' type="text" inputmode="numeric" autocomplete="off"' : ' type="text"') +
      (t === 'num' || t === 'int' ? ' inputmode="decimal"' : '') + ' data-bind="' + path + '" data-t="' + t + '" value="' + esc(val) + '"' +
      (o.ph ? ' placeholder="' + esc(o.ph) + '"' : '') + (o.list ? ' list="' + o.list + '"' : '') + (o.max ? ' maxlength="' + o.max + '"' : '') + '></label>' +
      (o.hint ? '<small>' + o.hint + '</small>' : '') + '</div>';
  }
  function area(label, path, o) {
    o = o || {};
    var v = getPath(path), val = o.t === 'pairs' ? pairsToText(v) : (v == null ? '' : v);
    return '<div class="fld"><label>' + label + '<textarea rows="' + (o.rows || 3) + '" data-bind="' + path + '" data-t="' + (o.t || 'text') + '"' + (o.ph ? ' placeholder="' + esc(o.ph) + '"' : '') + '>' + esc(val) + '</textarea></label>' +
      (o.hint ? '<small>' + o.hint + '</small>' : '') + '</div>';
  }
  function chk(label, path, re, hint) {
    return '<label class="chk"><input type="checkbox" data-bind="' + path + '" data-t="bool"' + (re ? ' data-re' : '') + (getPath(path) ? ' checked' : '') + '><span>' + label + (hint ? '<small>' + hint + '</small>' : '') + '</span></label>';
  }
  function sel(label, path, options, o) {
    o = o || {};
    var v = getPath(path);
    return '<div class="fld ' + (o.cls || '') + '"><label>' + label + '<select data-bind="' + path + '" data-t="' + (o.t || 'text') + '"' + (o.re ? ' data-re' : '') + (o.hook ? ' data-hook="' + o.hook + '"' : '') + '>' +
      options.map(function (x) { return '<option value="' + esc(x[0]) + '"' + (String(v == null ? '' : v) === String(x[0]) ? ' selected' : '') + '>' + esc(x[1]) + '</option>'; }).join('') +
      '</select></label>' + (o.hint ? '<small>' + o.hint + '</small>' : '') + '</div>';
  }
  function imgField(label, path, max, hint) {
    var v = getPath(path) || '', isData = /^data:/i.test(v), ok = A.safeImg(v);
    return '<div class="imgf" data-imgf="' + path + '" data-label="' + esc(label) + '" data-max="' + (max || 1000) + '" data-hint="' + esc(hint || '') + '"><span class="lbl">' + label + '</span><div class="imgf__row">' +
      '<span class="imgf__prev">' + (ok ? '<img src="' + esc(ok) + '" alt="">' : icon('upload')) + '</span><div class="imgf__ctl">' +
      '<input type="url" data-bind="' + path + '" data-t="img" aria-label="' + esc(label) + ': adres zdjęcia" placeholder="' + (isData ? 'Wgrane zdjęcie. Wklej adres, żeby je zastąpić' : 'Wklej adres zdjęcia, https://…') + '" value="' + esc(isData ? '' : v) + '">' +
      '<div class="imgf__btns"><label class="btn btn--ghost btn--small">' + icon('upload', 'ic--s') + 'Wgraj z dysku<input type="file" accept="image/*" class="sr" data-upload="' + path + '"></label>' +
      (v ? '<button type="button" class="btn btn--ghost btn--small" data-act="adm-img-clear" data-path="' + path + '">Usuń zdjęcie</button>' : '') + '</div>' +
      (hint ? '<small>' + hint + '</small>' : '') + '</div></div></div>';
  }
  function refreshImgField(path) {
    var el = document.querySelector('[data-imgf="' + path + '"]'); if (!el) return;
    var tmp = document.createElement('div');
    tmp.innerHTML = imgField(el.getAttribute('data-label'), path, +el.getAttribute('data-max'), el.getAttribute('data-hint'));
    el.parentNode.replaceChild(tmp.firstChild, el);
  }
  function ibtn(label, act, ic, attrs, cls) {
    return '<button type="button" class="ibtn ' + (cls || '') + '" data-act="' + act + '" ' + (attrs || '') + ' aria-label="' + esc(label) + '" title="' + esc(label) + '">' + icon(ic, 'ic--s') + '</button>';
  }
  function head(title, text, btns, back) {
    return (back ? '<a class="back" href="' + back[0] + '">' + icon('chev-left', 'ic--s') + back[1] + '</a>' : '') +
      '<div class="adm-head"><div><h1>' + title + '</h1>' + (text ? '<p>' + text + '</p>' : '') + '</div>' + (btns ? '<div class="adm-head__btns">' + btns + '</div>' : '') + '</div>';
  }
  function card(title, body, sub, id) {
    return '<section class="card"' + (id ? ' id="' + id + '"' : '') + '><h2>' + title + '</h2>' + (sub ? '<p class="card__sub">' + sub + '</p>' : '') + body + '</section>';
  }
  var ART_OPTS = art.DISHES.map(function (k) { return [k, art.DISH_NAMES[k]]; });

  /* ---------- wejście i rama ---------- */
  function gate() {
    return '<div class="adm-gate"><form class="card adm-gate__box" data-form="adm-pin"><a class="logo" href="#/">' + art.logo(30) + '<span class="logo__word">szamka</span></a>' +
      '<h1>Panel</h1><p>Wpisz PIN, żeby edytować lokale, menu i zamówienia.</p>' +
      '<div class="fld"><label>PIN<input type="password" name="pin" inputmode="numeric" autocomplete="off" autofocus' + (pinError ? ' aria-invalid="true"' : '') + '></label>' +
      (pinError ? '<p class="fld__err">To nie ten PIN. Spróbuj jeszcze raz.</p>' : '') + '</div>' +
      '<button class="btn btn--primary btn--block btn--lg" type="submit">Wejdź do panelu</button><a class="linkbtn" href="#/">Wróć na stronę</a></form></div>';
  }
  var TABS = [['zamowienia', 'Zamówienia', 'receipt'], ['lokale', 'Lokale', 'store'], ['ustawienia', 'Ustawienia', 'gear'], ['dane', 'Dane', 'download']];
  function layout(tab, body) {
    return '<div class="adm"><header class="adm__bar"><div class="wrap adm__barin"><a class="logo logo--inv" href="#/admin">' + art.logo(28) + '<span class="logo__word">szamka</span><span class="adm__tag">panel</span></a>' +
      '<nav class="adm__tabs" aria-label="Sekcje panelu">' + TABS.map(function (t) {
        return '<a class="adm__tab' + (t[0] === tab ? ' is-on' : '') + '" href="#/admin/' + t[0] + '"' + (t[0] === tab ? ' aria-current="page"' : '') + '>' + icon(t[2], 'ic--s') + '<span>' + t[1] + '</span></a>';
      }).join('') + '</nav><div class="adm__right"><span class="adm__saved" id="adm-saved" role="status">Zapisano</span>' +
      '<a class="btn btn--ghost btn--small" href="#/">' + icon('eye', 'ic--s') + '<span>Strona</span></a>' +
      '<button class="btn btn--ghost btn--small" type="button" data-act="adm-lock">' + icon('lock', 'ic--s') + '<span>Zablokuj</span></button></div></div></header>' +
      '<main class="wrap adm__body" id="main" tabindex="-1">' + body + '</main></div>';
  }
  function view(rt) {
    if (!unlocked()) {
      if (S().settings.pin) return gate();
      setUnlocked(true);
    }
    ctx = null;
    var tab = rt.a || 'zamowienia', body;
    if (tab === 'zamowienie') { body = vOrder(rt.b); tab = 'zamowienia'; }
    else if (tab === 'lokale') body = vRests();
    else if (tab === 'lokal') { body = vRest(rt.b); tab = 'lokale'; }
    else if (tab === 'ustawienia') body = vSettings();
    else if (tab === 'dane') body = vData();
    else { body = vOrders(); tab = 'zamowienia'; }
    return layout(tab, body);
  }
  function pill(opt) {
    if (!unlocked()) return '';
    var r = opt.rid && A.getR(opt.rid), o = opt.orderId && A.getOrder(opt.orderId);
    return '<div class="adminpill" role="region" aria-label="Skróty panelu"><a href="#/admin">' + icon('gear', 'ic--s') + 'Panel</a>' +
      (r ? '<a href="#/admin/lokal/' + encodeURIComponent(r.id) + '">' + icon('edit', 'ic--s') + 'Edytuj ten lokal</a>' : '') +
      (o ? '<a href="#/admin/zamowienie/' + encodeURIComponent(o.id) + '">' + icon('edit', 'ic--s') + 'Edytuj to zamówienie</a>' : '') +
      '<button type="button" data-act="adm-lock" aria-label="Zablokuj panel i schowaj ten pasek" title="Zablokuj panel i schowaj ten pasek">' + icon('lock', 'ic--s') + '</button></div>';
  }

  /* ---------- zamówienia ---------- */
  function statusOptions() {
    return [['auto', 'Zmienia się sam z upływem czasu']].concat(['zlozone', 'kuchnia', 'droga', 'dostarczone', 'anulowane'].map(function (k) { return [k, 'Na stałe: ' + A.STATUS[k].chip.toLowerCase()]; }));
  }
  function itemsSummary(o) {
    return o.items.slice(0, 3).map(function (i) { return (i.qty > 1 ? i.qty + '× ' : '') + i.name; }).join(', ') + (o.items.length > 3 ? ' i jeszcze ' + (o.items.length - 3) : '') || 'Bez pozycji';
  }
  function vOrders() {
    var rows = S().orders.map(function (o, i) { return { o: o, i: i }; }).sort(function (a, b) { return b.o.placedAt - a.o.placedAt; });
    return head('Zamówienia', 'Dodawaj zamówienia, zmieniaj im lokal, pozycje, godziny i status. Trafiają tu też zamówienia złożone zwyczajnie przez stronę.',
      '<button class="btn btn--primary" type="button" data-act="adm-order-new">' + icon('plus') + 'Nowe zamówienie</button>') +
      (rows.length ? '<ul class="adm-list">' + rows.map(function (x) {
        var o = x.o, st = A.orderStatus(o), id = esc(o.id);
        return '<li class="adm-row">' + A.logoHTML(o) + '<div class="adm-row__txt"><a href="#/admin/zamowienie/' + id + '"><b>' + esc(o.rname) + '</b></a><span>' + esc(itemsSummary(o)) + '</span>' +
          '<small>nr ' + esc(o.no) + ', złożone ' + A.whenPL(o.placedAt) + ', ' + zl(A.orderTotal(o)) + '</small></div>' +
          '<span class="status status--' + st + '">' + A.STATUS[st].chip + '</span>' +
          '<div class="adm-row__btns"><a class="btn btn--ghost btn--small" href="#/admin/zamowienie/' + id + '">' + icon('edit', 'ic--s') + 'Edytuj</a>' +
          '<a class="ibtn" href="#/zamowienie/' + id + '" aria-label="Zobacz stronę zamówienia" title="Zobacz stronę zamówienia">' + icon('eye', 'ic--s') + '</a>' +
          ibtn('Link dla znajomego', 'adm-order-link', 'link', 'data-id="' + id + '"') + ibtn('Usuń zamówienie', 'adm-order-del', 'trash', 'data-id="' + id + '"', 'ibtn--danger') + '</div></li>';
      }).join('') + '</ul>' :
        '<div class="adm-empty">' + art.dish('burger', 'dish adm-empty__art') + '<h2>Nie ma jeszcze zamówień</h2><p>Dodaj pierwsze tutaj albo zamów coś zwyczajnie przez stronę.</p></div>');
  }
  function vOrder(id) {
    var s = S(), i = s.orders.findIndex(function (o) { return o.id === id; });
    if (i < 0) return head('Nie ma takiego zamówienia', 'Mogło zostać usunięte.', '', ['#/admin/zamowienia', 'Zamówienia']);
    var o = s.orders[i], p = 'orders.' + i, r = A.getR(o.rid), t = A.orderTimes(o), st = A.orderStatus(o);
    ctx = { kind: 'order', i: i };
    var restOpts = s.restaurants.map(function (x) { return [x.id, x.name + (x.hidden ? ' (ukryty)' : '')]; }).concat([['', 'Inny lokal, nazwę wpiszę sam']]);
    var menuOpts = r ? '<div class="fld"><label>Dodaj pozycję z menu lokalu<select data-hook="order-menu-add"><option value="">Wybierz danie…</option>' + r.menu.map(function (c) {
      return '<optgroup label="' + esc(c.name) + '">' + c.items.map(function (it) { return '<option value="' + esc(it.id) + '">' + esc(it.name) + ', ' + zl(it.price) + '</option>'; }).join('') + '</optgroup>';
    }).join('') + '</select></label></div>' : '';
    return head('Zamówienie nr <span data-live="' + p + '.no">' + esc(o.no) + '</span>', '', '<a class="btn btn--ghost" href="#/zamowienie/' + esc(o.id) + '">' + icon('eye') + 'Zobacz stronę zamówienia</a>' +
      '<button class="btn btn--primary" type="button" data-act="adm-order-link" data-id="' + esc(o.id) + '">' + icon('link') + 'Link dla znajomego</button>', ['#/admin/zamowienia', 'Zamówienia']) +
      '<div class="adm-cols"><div>' +

      card('Lokal', sel('Z którego lokalu', p + '.rid', restOpts, { hook: 'order-rest' }) +
        '<div class="grid2">' + inp('Nazwa lokalu widoczna w zamówieniu', p + '.rname', { max: 60 }) + inp('Numer zamówienia', p + '.no', { max: 12 }) + '</div>' +
        (r ? '' : '<div class="grid2">' + sel('Ilustracja', p + '.art', ART_OPTS) + '<div class="fld"><label>Kolor<input type="color" data-bind="' + p + '.color" data-t="text" value="' + esc(art.safeColor(o.color)) + '"></label></div></div>')) +

      card('Pozycje', '<ul class="orows">' + o.items.map(function (it, k) {
        var q = p + '.items.' + k;
        return '<li class="orow"><input class="orow__q" inputmode="numeric" aria-label="Liczba sztuk" data-bind="' + q + '.qty" data-t="int" value="' + esc(it.qty) + '">' +
          '<input class="orow__n" aria-label="Nazwa pozycji" placeholder="Nazwa" data-bind="' + q + '.name" data-t="text" value="' + esc(it.name) + '">' +
          '<input class="orow__o" aria-label="Wariant i dodatki" placeholder="Wariant, dodatki" data-bind="' + q + '.opts" data-t="text" value="' + esc(it.opts || '') + '">' +
          '<input class="orow__p" inputmode="decimal" aria-label="Cena za sztukę" data-bind="' + q + '.price" data-t="num" value="' + esc(numStr(it.price)) + '">' +
          ibtn('Usuń pozycję', 'adm-oitem-del', 'trash', 'data-k="' + k + '"', 'ibtn--danger') + '</li>';
      }).join('') + '</ul><button class="btn btn--ghost btn--small" type="button" data-act="adm-oitem-add">' + icon('plus', 'ic--s') + 'Dodaj pustą pozycję</button>' + menuOpts,
      'Kolumny: sztuki, nazwa, wariant i dodatki, cena za sztukę.') +

      card('Kwoty', '<div class="grid4">' + inp('Dostawa', p + '.fee', { t: 'num' }) + inp('Opłata serwisowa', p + '.service', { t: 'num' }) + inp('Napiwek', p + '.tip', { t: 'num' }) + inp('Rabat', p + '.disc', { t: 'num' }) + '</div>') +

      card('Kiedy i na jakim etapie', '<p class="lbl">Ustaw jednym kliknięciem, żeby teraz było:</p><div class="stagebtns">' +
        [['zlozone', 'Przed chwilą złożone'], ['kuchnia', 'Kuchnia gotuje'], ['droga', 'Kurier w drodze'], ['dostarczone', 'Już dostarczone']].map(function (x) {
          return '<button type="button" class="chip' + (st === x[0] ? ' is-on' : '') + '" data-act="adm-stage" data-s="' + x[0] + '">' + x[1] + '</button>';
        }).join('') + '</div>' +
        '<div class="grid2">' + inp('Złożone', p + '.placedAt', { t: 'time' }) + sel('Status', p + '.status', statusOptions(), { re: true }) + '</div>' +
        '<div class="grid3">' + inp('Potwierdzenie przez lokal, min', p + '.times.confirm', { t: 'int' }) + inp('Przygotowanie, min', p + '.times.prep', { t: 'int' }) + inp('Dojazd kuriera, min', p + '.times.ride', { t: 'int' }) + '</div>',
      'Zamówienie samo przechodzi przez etapy: złożone, w przygotowaniu, w drodze, dostarczone. O tempie decydują trzy czasy poniżej.') +

      card('Odbiorca i dostawa', '<div class="grid2">' + inp('Imię i nazwisko', p + '.customer.name', { max: 60 }) + inp('Telefon', p + '.customer.phone', { max: 20 }) + '</div>' +
        inp('Adres dostawy', p + '.address', { max: 160 }) +
        '<div class="grid2">' + inp('Płatność', p + '.pay', { list: 'adm-pay', max: 40 }) + inp('Wskazówki dla kuriera', p + '.note', { max: 160 }) + '</div>' +
        '<datalist id="adm-pay">' + Object.keys(A.PAY).map(function (k) { return '<option value="' + esc(A.PAY[k]) + '">'; }).join('') + '</datalist>') +

      card('Kurier', '<div class="grid2">' + inp('Imię kuriera', p + '.courier.name', { max: 30 }) +
        sel('Czym jedzie', p + '.courier.vehicle', [['rower', 'Rowerem'], ['skuter', 'Skuterem'], ['samochod', 'Samochodem']]) + '</div>') +

      card('Żart', chk('Po dostarczeniu pokaż okno z napisem, że to był żart', p + '.reveal.on') +
        '<div class="grid2">' + inp('Nagłówek', p + '.reveal.title', { max: 80 }) + inp('Tekst pod nagłówkiem', p + '.reveal.text', { max: 240 }) + '</div>' +
        '<button class="btn btn--ghost btn--small" type="button" data-act="adm-reveal-now" data-id="' + esc(o.id) + '">' + icon('eye', 'ic--s') + 'Pokaż to okno teraz</button>',
      'Okno wyskakuje na stronie zamówienia i u każdego, kto otworzy link do śledzenia.') +

      '<button class="btn btn--danger" type="button" data-act="adm-order-del" data-id="' + esc(o.id) + '" data-back="1">' + icon('trash') + 'Usuń to zamówienie</button>' +
      '</div><aside class="adm-side"><section class="card adm-calc"><h2>Tak to teraz wygląda</h2><dl class="facts">' +
      '<div><dt>Etap</dt><dd><b id="calc-status">' + A.STATUS[st].chip + '</b></dd></div>' +
      '<div><dt>Dostawa</dt><dd id="calc-eta">' + A.whenPL(t[3]) + '</dd></div>' +
      '<div><dt>Wartość dań</dt><dd id="calc-sub">' + zl(A.orderSub(o)) + '</dd></div>' +
      '<div><dt>Razem</dt><dd><b id="calc-total">' + zl(A.orderTotal(o)) + '</b></dd></div></dl>' +
      '<p class="adm-note">Zmiany zapisują się same. Strona zamówienia pokazuje je od razu, link dla znajomego trzeba po zmianach wygenerować jeszcze raz.</p></section></aside></div>';
  }
  function recalc() {
    if (!ctx) return;
    if (ctx.kind === 'order') {
      var o = S().orders[ctx.i]; if (!o) return;
      var t = A.orderTimes(o), st = A.orderStatus(o);
      setText('calc-status', A.STATUS[st].chip); setText('calc-eta', A.whenPL(t[3]));
      setText('calc-sub', zl(A.orderSub(o))); setText('calc-total', zl(A.orderTotal(o)));
    } else if (ctx.kind === 'rest') {
      var r = S().restaurants[ctx.i], el = document.getElementById('adm-prev');
      if (r && el) el.innerHTML = A.rcard(r);
    }
  }
  function setText(id, txt) { var el = document.getElementById(id); if (el) el.textContent = txt; }

  /* ---------- lokale ---------- */
  function vRests() {
    var list = S().restaurants;
    return head('Lokale', 'Lokale pokazują się na stronie w tej kolejności. Każdy ma własne menu, ceny, czasy dostawy i wygląd.',
      '<button class="btn btn--primary" type="button" data-act="adm-r-new">' + icon('plus') + 'Dodaj lokal</button>') +
      '<ul class="adm-list">' + list.map(function (r, i) {
        var n = r.menu.reduce(function (a, c) { return a + c.items.length; }, 0), id = esc(r.id);
        return '<li class="adm-row' + (r.hidden ? ' is-hidden' : '') + '">' + A.logoHTML(r) + '<div class="adm-row__txt"><a href="#/admin/lokal/' + encodeURIComponent(r.id) + '"><b>' + esc(r.name) + '</b></a><span>' + esc(r.kitchen) + '</span>' +
          '<small>' + n + ' ' + A.plural(n, 'danie', 'dania', 'dań') + ', dostawa ' + (r.fee > 0 ? zl(r.fee) : 'za darmo') + ', minimum ' + A.zlShort(r.minOrder) + '</small></div>' +
          (r.hidden ? '<span class="status status--anulowane">Ukryty</span>' : r.open ? '<span class="status status--dostarczone">Otwarty</span>' : '<span class="status">Zamknięty</span>') +
          '<div class="adm-row__btns"><a class="btn btn--ghost btn--small" href="#/admin/lokal/' + encodeURIComponent(r.id) + '">' + icon('edit', 'ic--s') + 'Edytuj</a>' +
          ibtn('Przesuń wyżej', 'adm-r-move', 'up', 'data-id="' + id + '" data-d="-1"' + (i ? '' : ' disabled')) + ibtn('Przesuń niżej', 'adm-r-move', 'down', 'data-id="' + id + '" data-d="1"' + (i < list.length - 1 ? '' : ' disabled')) +
          ibtn(r.hidden ? 'Pokaż na stronie' : 'Ukryj na stronie', 'adm-r-hide', r.hidden ? 'eye' : 'eye-off', 'data-id="' + id + '"') +
          ibtn('Zrób kopię lokalu', 'adm-r-dup', 'copy', 'data-id="' + id + '"') + ibtn('Usuń lokal', 'adm-r-del', 'trash', 'data-id="' + id + '"', 'ibtn--danger') + '</div></li>';
      }).join('') + '</ul>';
  }
  function menuEditor(r, p) {
    return r.menu.map(function (c, ci) {
      var cp = p + '.menu.' + ci;
      return '<div class="mcatE"><div class="mcatE__head"><input aria-label="Nazwa kategorii" placeholder="Nazwa kategorii" data-bind="' + cp + '.name" data-t="text" value="' + esc(c.name) + '">' +
        ibtn('Przesuń kategorię wyżej', 'adm-cat-move', 'up', 'data-c="' + ci + '" data-d="-1"' + (ci ? '' : ' disabled')) +
        ibtn('Przesuń kategorię niżej', 'adm-cat-move', 'down', 'data-c="' + ci + '" data-d="1"' + (ci < r.menu.length - 1 ? '' : ' disabled')) +
        ibtn('Usuń kategorię z daniami', 'adm-cat-del', 'trash', 'data-c="' + ci + '"', 'ibtn--danger') + '</div><ul class="mrows">' +
        c.items.map(function (it, ii) {
          var ip = cp + '.items.' + ii, extra = (it.variants.length ? it.variants.length + ' ' + A.plural(it.variants.length, 'wariant', 'warianty', 'wariantów') : '') +
            (it.extras.length ? (it.variants.length ? ', ' : '') + it.extras.length + ' ' + A.plural(it.extras.length, 'dodatek', 'dodatki', 'dodatków') : '');
          return '<li class="mrowE"><input class="mrowE__n" aria-label="Nazwa dania" placeholder="Nazwa dania" data-bind="' + ip + '.name" data-t="text" value="' + esc(it.name) + '">' +
            '<input class="mrowE__p" inputmode="decimal" aria-label="Cena" data-bind="' + ip + '.price" data-t="num" value="' + esc(numStr(it.price)) + '">' +
            '<div class="mrowE__btns">' + ibtn(it.popular ? 'Zdejmij z Popularnych' : 'Pokaż w Popularnych', 'adm-item-pop', 'star', 'data-c="' + ci + '" data-i="' + ii + '" aria-pressed="' + !!it.popular + '"', it.popular ? 'is-on' : '') +
            '<button type="button" class="btn btn--ghost btn--small" data-act="adm-item-edit" data-c="' + ci + '" data-i="' + ii + '">' + icon('edit', 'ic--s') + 'Opis, zdjęcie, warianty</button>' +
            ibtn('Przesuń danie wyżej', 'adm-item-move', 'up', 'data-c="' + ci + '" data-i="' + ii + '" data-d="-1"' + (ii ? '' : ' disabled')) +
            ibtn('Przesuń danie niżej', 'adm-item-move', 'down', 'data-c="' + ci + '" data-i="' + ii + '" data-d="1"' + (ii < c.items.length - 1 ? '' : ' disabled')) +
            ibtn('Usuń danie', 'adm-item-del', 'trash', 'data-c="' + ci + '" data-i="' + ii + '"', 'ibtn--danger') + '</div>' +
            (it.desc || extra ? '<small class="mrowE__sub">' + esc([it.desc, extra].filter(Boolean).join(' / ')) + '</small>' : '') + '</li>';
        }).join('') + '</ul><button class="btn btn--ghost btn--small" type="button" data-act="adm-item-add" data-c="' + ci + '">' + icon('plus', 'ic--s') + 'Dodaj danie</button></div>';
    }).join('') + '<button class="btn btn--dark" type="button" data-act="adm-cat-add">' + icon('plus') + 'Dodaj kategorię</button>';
  }
  function vRest(id) {
    var s = S(), i = s.restaurants.findIndex(function (r) { return r.id === id; });
    if (i < 0) return head('Nie ma takiego lokalu', 'Mógł zostać usunięty.', '', ['#/admin/lokale', 'Lokale']);
    var r = s.restaurants[i], p = 'restaurants.' + i;
    ctx = { kind: 'rest', i: i };
    return head('<span data-live="' + p + '.name">' + esc(r.name) + '</span>', '', '<a class="btn btn--ghost" href="#/lokal/' + encodeURIComponent(r.id) + '">' + icon('eye') + 'Zobacz stronę lokalu</a>', ['#/admin/lokale', 'Lokale']) +
      '<div class="adm-cols"><div>' +
      card('Podstawy', '<div class="grid2">' + inp('Nazwa lokalu', p + '.name', { max: 60 }) + inp('Opis pod nazwą', p + '.kitchen', { max: 80, ph: 'Np. Pizza, włoska' }) + '</div>' +
        inp('Adres lokalu', p + '.address', { max: 120 }) +
        '<p class="lbl">Kuchnie, w których lokal się pokazuje</p><div class="cuis">' + s.settings.cuisines.map(function (c) {
          return '<label class="chipchk"><input type="checkbox" data-hook="rest-cui" value="' + esc(c.id) + '"' + (r.cuisines.indexOf(c.id) >= 0 ? ' checked' : '') + '><span>' + esc(c.name) + '</span></label>';
        }).join('') + '</div>') +

      card('Wygląd', '<div class="grid2">' + sel('Ilustracja na okładce', p + '.art', ART_OPTS) +
        '<div class="fld"><label>Kolor stołu i logo<input type="color" data-bind="' + p + '.color" data-t="text" value="' + esc(art.safeColor(r.color)) + '"></label></div></div>' +
        imgField('Zdjęcie na okładkę', p + '.cover', 1200, 'Jeśli dodasz zdjęcie, zastąpi ilustrację. Najlepiej poziome.') +
        imgField('Logo', p + '.logo', 240, 'Bez logo pokazujemy inicjały na kolorowym tle.')) +

      card('Dostawa i oceny', '<div class="grid4">' + inp('Czas dostawy od, min', p + '.timeMin', { t: 'int' }) + inp('Czas dostawy do, min', p + '.timeMax', { t: 'int' }) +
        inp('Koszt dostawy', p + '.fee', { t: 'num' }) + inp('Minimalna kwota', p + '.minOrder', { t: 'num' }) + '</div>' +
        '<div class="grid4">' + inp('Darmowa dostawa od', p + '.freeFrom', { t: 'num', hint: '0 wyłącza próg.' }) + inp('Ocena', p + '.rating', { t: 'num', hint: 'Od 1 do 5.' }) + inp('Liczba opinii', p + '.reviews', { t: 'int' }) + '</div>') +

      card('Stan i promocje', '<div class="grid2">' + inp('Naklejka promocyjna', p + '.badge', { max: 40, ph: 'Np. Druga pizza −50%', hint: 'Pusta naklejka znika.' }) +
        inp('Godzina otwarcia', p + '.opensAt', { max: 10, ph: 'Np. 16:00', hint: 'Widać ją, gdy lokal jest zamknięty.' }) + '</div>' +
        '<div class="chks">' + chk('Lokal jest otwarty i przyjmuje zamówienia', p + '.open') + chk('Oznacz jako sponsorowany', p + '.sponsored') +
        chk('Oznacz jako nowość', p + '.isNew') + chk('Ukryj lokal na stronie', p + '.hidden') + '</div>') +

      card('Menu', '<div id="adm-menu">' + menuEditor(r, p) + '</div>', 'Nazwę i cenę zmienisz od razu w wierszu. Gwiazdka dodaje danie do sekcji Popularne.') +
      '<button class="btn btn--danger" type="button" data-act="adm-r-del" data-id="' + esc(r.id) + '" data-back="1">' + icon('trash') + 'Usuń ten lokal</button>' +
      '</div><aside class="adm-side"><p class="lbl">Podgląd karty na liście lokali</p><div id="adm-prev" class="adm-prev">' + A.rcard(r) + '</div>' +
      '<p class="adm-note">Zmiany zapisują się same i od razu widać je na stronie w tej przeglądarce.</p></aside></div>';
  }
  function openItemEditor(ci, ii) {
    if (!ctx || ctx.kind !== 'rest') return;
    var ip = 'restaurants.' + ctx.i + '.menu.' + ci + '.items.' + ii;
    if (!getPath(ip)) return;
    A.openModal('<div class="dlg adm-dlg"><h2>Szczegóły dania</h2><div class="grid2">' + inp('Nazwa', ip + '.name', { max: 90 }) + inp('Cena', ip + '.price', { t: 'num' }) + '</div>' +
      area('Opis', ip + '.desc', { rows: 2, ph: 'Składniki albo krótki opis' }) +
      imgField('Zdjęcie dania', ip + '.img', 700, 'Dania bez zdjęcia też wyglądają dobrze.') +
      area('Warianty do wyboru', ip + '.variants', { t: 'pairs', rows: 3, ph: '32 cm\n42 cm | 12', hint: 'Każdy wariant w osobnej linii. Po kresce dopłata do ceny, np. „42 cm | 12”. Klient wybiera jeden.' }) +
      area('Dodatki', ip + '.extras', { t: 'pairs', rows: 3, ph: 'Dodatkowy ser | 6\nSos czosnkowy | 3', hint: 'Każdy dodatek w osobnej linii, po kresce cena. Klient może zaznaczyć kilka.' }) +
      chk('Pokazuj w sekcji Popularne', ip + '.popular') +
      '<div class="dlg__btns"><button class="btn btn--primary" type="button" data-act="modal-close">Gotowe</button></div></div>', { label: 'Szczegóły dania', cls: 'modal--wide', onClose: rerender });
  }

  /* ---------- ustawienia ---------- */
  function vSettings() {
    var st = S().settings;
    return head('Ustawienia', 'Teksty na stronie głównej, kuchnie, kody rabatowe, domyślne dane w kasie i PIN.') +
      '<div class="adm-one">' +
      card('Strona główna', inp('Duży nagłówek', 'settings.heroTitle', { max: 80 }) + inp('Tekst pod nagłówkiem', 'settings.heroSub', { max: 160 }) +
        inp('Żółty pasek na górze strony', 'settings.promoBar', { max: 140, hint: 'Pusty pasek znika.' })) +
      card('Kuchnie', '<ul class="srows">' + st.cuisines.map(function (c, i) {
        return '<li class="srow"><input aria-label="Nazwa kuchni" placeholder="Nazwa" data-bind="settings.cuisines.' + i + '.name" data-t="text" value="' + esc(c.name) + '">' +
          '<select aria-label="Ilustracja" data-bind="settings.cuisines.' + i + '.art" data-t="text">' + ART_OPTS.map(function (x) { return '<option value="' + x[0] + '"' + (c.art === x[0] ? ' selected' : '') + '>' + esc(x[1]) + '</option>'; }).join('') + '</select>' +
          ibtn('Usuń kuchnię', 'adm-cui-del', 'trash', 'data-i="' + i + '"', 'ibtn--danger') + '</li>';
      }).join('') + '</ul><button class="btn btn--ghost btn--small" type="button" data-act="adm-cui-add">' + icon('plus', 'ic--s') + 'Dodaj kuchnię</button>',
      'To kafelki na stronie głównej i filtry nad listą lokali. Przypisanie lokalu do kuchni ustawiasz w edycji lokalu.') +
      card('Kody rabatowe', '<ul class="srows">' + st.vouchers.map(function (v, i) {
        return '<li class="srow srow--v"><input aria-label="Kod" placeholder="KOD" data-bind="settings.vouchers.' + i + '.code" data-t="upper" value="' + esc(v.code) + '">' +
          '<select aria-label="Rodzaj rabatu" data-bind="settings.vouchers.' + i + '.kind" data-t="text">' + [['kwota', 'Kwota w złotych'], ['procent', 'Procent od dań'], ['dostawa', 'Darmowa dostawa']].map(function (x) {
            return '<option value="' + x[0] + '"' + (v.kind === x[0] ? ' selected' : '') + '>' + x[1] + '</option>';
          }).join('') + '</select><input inputmode="decimal" aria-label="Wartość rabatu" placeholder="Wartość" data-bind="settings.vouchers.' + i + '.value" data-t="num" value="' + esc(numStr(v.value)) + '">' +
          ibtn('Usuń kod', 'adm-v-del', 'trash', 'data-i="' + i + '"', 'ibtn--danger') + '</li>';
      }).join('') + '</ul><button class="btn btn--ghost btn--small" type="button" data-act="adm-v-add">' + icon('plus', 'ic--s') + 'Dodaj kod</button>') +
      card('Opłaty i kurierzy', '<div class="grid2">' + inp('Opłata serwisowa', 'settings.serviceFee', { t: 'num', hint: 'Doliczana do każdego zamówienia. 0 ją wyłącza.' }) +
        inp('Imiona kurierów', 'settings.couriers', { t: 'list', hint: 'Po przecinku. Losujemy z nich kuriera do nowego zamówienia.' }) + '</div>') +
      card('Domyślne dane w kasie', '<div class="grid2">' + inp('Imię i nazwisko', 'user.name', { max: 60 }) + inp('Telefon', 'user.phone', { max: 20 }) + '</div>' +
        '<div class="grid2">' + inp('Adres dostawy', 'user.address', { max: 140, ph: 'Ulica i numer, miasto' }) + inp('E-mail', 'user.email', { max: 80 }) + '</div>' +
        '<div class="grid2">' + inp('Numer mieszkania', 'user.apt', { max: 10 }) + inp('Piętro', 'user.floor', { max: 10 }) + '</div>', 'Tym wypełnia się formularz zamówienia w tej przeglądarce.') +
      card('Żart w nowych zamówieniach', chk('Po dostarczeniu pokaż okno z napisem, że to był żart', 'settings.reveal.on') +
        '<div class="grid2">' + inp('Nagłówek', 'settings.reveal.title', { max: 80 }) + inp('Tekst pod nagłówkiem', 'settings.reveal.text', { max: 240 }) + '</div>',
      'Każde zamówienie dostaje te ustawienia na start. W edycji zamówienia możesz je zmienić osobno.') +
      card('PIN do panelu', inp('PIN', 'settings.pin', { t: 'pin', max: 12, hint: 'Pusty PIN oznacza wejście bez pytania. PIN chroni tylko przed przypadkowym wejściem, nie jest prawdziwym zabezpieczeniem.' })) +
      '</div>';
  }

  /* ---------- dane ---------- */
  function vData() {
    return head('Dane', 'Kopia zapasowa, przenoszenie zmian na inne urządzenie i powrót do ustawień początkowych.') +
      '<div class="adm-one">' +
      card('Gdzie są zapisane zmiany', '<p class="adm-text">Wszystko, co zmieniasz w panelu, zapisuje się w tej przeglądarce na tym urządzeniu. Na innym telefonie albo komputerze strona pokaże dane startowe, czyli te z pliku <code>js/dane.js</code>.</p>' +
        '<p class="adm-text">Zamówienie pokażesz komuś na jego urządzeniu linkiem do śledzenia. Link niesie w sobie całe zamówienie, więc działa wszędzie.</p>') +
      card('Kopia zapasowa', '<p class="adm-text">Kopia zawiera lokale, menu, ustawienia, zamówienia i dane z kasy. Wczytasz ją tutaj albo w tej samej stronie na innym urządzeniu.</p>' +
        '<div class="adm-btnrow"><button class="btn btn--primary" type="button" data-act="adm-export">' + icon('download') + 'Pobierz kopię</button>' +
        '<label class="btn btn--ghost">' + icon('upload') + 'Wczytaj kopię<input type="file" accept="application/json,.json" class="sr" data-hook="import"></label></div>') +
      card('Zmiany dla wszystkich odwiedzających', '<p class="adm-text">Pobierz nowy plik <code>dane.js</code> i podmień nim plik <code>js/dane.js</code> na serwerze. Od tej chwili każdy zobaczy Twoje lokale, menu i ustawienia.</p>' +
        '<p class="adm-text">Do tego pliku nie trafiają zamówienia ani dane z kasy. Trafia do niego PIN, więc każdy, kto zajrzy do pliku, go pozna.</p>' +
        '<div class="adm-btnrow"><button class="btn btn--ghost" type="button" data-act="adm-export-js">' + icon('download') + 'Pobierz dane.js</button></div>') +
      card('Powrót do początku', '<p class="adm-text">Usuwa z tej przeglądarki wszystkie zmiany, zamówienia i koszyk. Zostają dane startowe.</p>' +
        '<div class="adm-btnrow"><button class="btn btn--danger" type="button" data-act="adm-reset">' + icon('trash') + 'Przywróć dane startowe</button></div>') +
      '</div>';
  }
  function download(name, text, mime) {
    var a = document.createElement('a'), url = URL.createObjectURL(new Blob([text], { type: mime }));
    a.href = url; a.download = name; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(url); if (a.parentNode) a.parentNode.removeChild(a); }, 800);
  }

  /* ---------- wiązanie pól ze stanem ---------- */
  function apply(el) {
    var path = el.getAttribute('data-bind'), t = el.getAttribute('data-t') || 'text', v;
    if (el.type === 'checkbox') v = el.checked;
    else if (t === 'num') v = A.r2(parseNum(el.value));
    else if (t === 'int') v = Math.round(parseNum(el.value));
    else if (t === 'time') { v = el.value ? new Date(el.value).getTime() : Date.now(); if (!isFinite(v)) return; }
    else if (t === 'pairs') v = textToPairs(el.value);
    else if (t === 'list') v = el.value.split(',').map(function (x) { return x.trim(); }).filter(Boolean);
    else if (t === 'upper') v = el.value.trim().toUpperCase();
    else if (t === 'pin') v = el.value.trim();
    else if (t === 'img') {
      v = el.value.trim();
      if (!v && /^data:/i.test(getPath(path) || '')) return;      /* puste pole nie kasuje wgranego zdjęcia */
    }
    else v = el.value;
    setPath(path, v); touch();
    if (/\.items\.\d+\./.test(path) && ctx && ctx.kind === 'order') { var o = S().orders[ctx.i]; if (o) o.sample = false; }
    document.querySelectorAll('[data-live="' + path + '"]').forEach(function (n) { n.textContent = v; });
    if (t === 'img') {
      var box = el.closest('.imgf'), prev = box && box.querySelector('.imgf__prev'), ok = A.safeImg(v);
      if (prev) prev.innerHTML = ok ? '<img src="' + esc(ok) + '" alt="">' : icon('upload');
    }
    recalc();
  }
  var hooks = {};
  hooks['order-rest'] = function (el) {
    var o = S().orders[ctx.i], r = A.getR(el.value); if (!o) return;
    o.rid = r ? r.id : '';
    if (r) {
      o.rname = r.name; o.art = r.art; o.color = r.color; o.logo = r.logo; o.fee = +r.fee || 0;
      if (o.sample) o.items = sampleItems(r);
    } else { o.logo = ''; }
    commit(); rerender();
  };
  hooks['order-menu-add'] = function (el) {
    var o = S().orders[ctx.i], r = o && A.getR(o.rid); if (!r || !el.value) return;
    var it = null;
    r.menu.forEach(function (c) { c.items.forEach(function (x) { if (x.id === el.value) it = x; }); });
    if (!it) return;
    if (o.sample) { o.items = []; o.sample = false; }
    var v = it.variants[0];
    o.items.push({ name: it.name, opts: v ? v.name : '', qty: 1, price: A.r2((+it.price || 0) + (v ? +v.price || 0 : 0)) });
    commit(); rerender();
  };
  hooks['rest-cui'] = function (el) {
    var r = S().restaurants[ctx.i]; if (!r) return;
    var k = r.cuisines.indexOf(el.value);
    if (el.checked && k < 0) r.cuisines.push(el.value);
    if (!el.checked && k >= 0) r.cuisines.splice(k, 1);
    commit();
  };
  hooks['import'] = function (el) {
    var file = el.files && el.files[0]; if (!file) return;
    var rd = new FileReader();
    rd.onload = function () {
      var obj = null;
      try { obj = JSON.parse(rd.result); } catch (e) { obj = null; }
      if (!obj || !Array.isArray(obj.restaurants) || !obj.settings) { toast('To nie wygląda na kopię z Szamki. Wybierz plik pobrany przyciskiem „Pobierz kopię”.'); return; }
      A.confirmBox('Wczytać tę kopię?', 'Zastąpi wszystkie lokale, menu, ustawienia i zamówienia zapisane teraz w tej przeglądarce.', 'Wczytaj kopię', function () {
        obj.meta = { seed: (obj.meta && obj.meta.seed) || 'kopia', edited: true };
        A.replace(obj); A.save(); rerender(); toast('Kopia wczytana.');
      });
    };
    rd.readAsText(file);
  };
  function upload(el) {
    var file = el.files && el.files[0], path = el.getAttribute('data-upload'); if (!file) return;
    var box = el.closest('.imgf'), max = box ? +box.getAttribute('data-max') || 1000 : 1000;
    if (!/^image\//.test(file.type)) { toast('To nie jest plik ze zdjęciem.'); return; }
    var rd = new FileReader();
    rd.onload = function () {
      var img = new Image();
      img.onload = function () {
        var k = Math.min(1, max / Math.max(img.width, img.height)), c = document.createElement('canvas');
        c.width = Math.max(1, Math.round(img.width * k)); c.height = Math.max(1, Math.round(img.height * k));
        var g = c.getContext('2d');
        g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height); g.drawImage(img, 0, 0, c.width, c.height);
        var before = getPath(path);
        setPath(path, c.toDataURL('image/jpeg', 0.82)); touch();
        if (!A.save(true)) {
          setPath(path, before); A.save(true);
          toast('To zdjęcie nie mieści się już w pamięci przeglądarki. Wklej zamiast niego adres zdjęcia z internetu.');
        } else flash();
        refreshImgField(path); recalc();
      };
      img.onerror = function () { toast('Nie udało się odczytać tego zdjęcia. Spróbuj z plikiem JPG albo PNG.'); };
      img.src = rd.result;
    };
    rd.readAsDataURL(file);
  }
  function onInput(e) {
    var el = e.target;
    if (!el.getAttribute || !el.getAttribute('data-bind') || !unlocked() || el.type === 'checkbox' || el.tagName === 'SELECT') return;
    apply(el); A.saveSoon(); flash();
  }
  function onChange(e) {
    var el = e.target;
    if (!el.getAttribute || !unlocked()) return;
    if (el.getAttribute('data-upload')) { upload(el); return; }
    var hook = el.getAttribute('data-hook');
    if (el.getAttribute('data-bind')) { apply(el); A.save(); flash(); }
    if (hook && hooks[hook]) { if (ctx || hook === 'import') hooks[hook](el); return; }
    if (el.hasAttribute('data-re')) rerender();
  }

  /* ---------- akcje ---------- */
  var act = A.actions;
  function guard(fn) { return function (el, e) { if (unlocked()) fn(el, e); }; }
  function sampleItems(r) {
    var out = [];
    r.menu.forEach(function (c) { c.items.forEach(function (i) { if (i.popular && out.length < 2) out.push(i); }); });
    if (!out.length && r.menu[0] && r.menu[0].items[0]) out.push(r.menu[0].items[0]);
    return out.map(function (i) { var v = i.variants[0]; return { name: i.name, opts: v ? v.name : '', qty: 1, price: A.r2((+i.price || 0) + (v ? +v.price || 0 : 0)) }; });
  }
  function moveIn(arr, i, d) {
    var j = i + d; if (j < 0 || j >= arr.length) return;
    var x = arr[i]; arr[i] = arr[j]; arr[j] = x;
  }
  function curRest() { return ctx && ctx.kind === 'rest' ? S().restaurants[ctx.i] : null; }
  function curOrder() { return ctx && ctx.kind === 'order' ? S().orders[ctx.i] : null; }

  A.forms['adm-pin'] = function (f) {
    var v = f.elements.namedItem('pin').value.trim();
    if (v === String(S().settings.pin || '')) { pinError = false; setUnlocked(true); } else pinError = true;
    rerender();
  };
  act['adm-lock'] = function () {
    setUnlocked(false); pinError = false;
    if (A.parseHash().name === 'admin') location.hash = '#/'; else rerender();
    toast('Panel zablokowany.');
  };

  act['adm-order-new'] = guard(function () {
    var s = S(), r = s.restaurants.filter(function (x) { return !x.hidden; })[0] || s.restaurants[0] || null;
    var lines = r ? sampleItems(r).map(function (i) { return { name: i.name, opts: i.opts, qty: i.qty, price: i.price }; }) : [];
    var o = A.newOrder(r, lines, {});
    o.sample = true;
    s.orders.push(o); commit();
    location.hash = '#/admin/zamowienie/' + o.id;
  });
  act['adm-order-del'] = guard(function (el) {
    var id = el.getAttribute('data-id'), back = el.getAttribute('data-back'), o = A.getOrder(id); if (!o) return;
    A.confirmBox('Usunąć zamówienie?', 'Zamówienie nr ' + o.no + ' z lokalu ' + o.rname + ' zniknie z historii. Wysłane wcześniej linki do śledzenia dalej będą działać.', 'Usuń zamówienie', function () {
      var s = S(); s.orders = s.orders.filter(function (x) { return x.id !== id; }); commit();
      if (back) location.hash = '#/admin/zamowienia'; else rerender();
    }, true);
  });
  act['adm-order-link'] = guard(function (el) {
    var o = A.getOrder(el.getAttribute('data-id')); if (!o) return;
    A.save();
    A.shareLink(o).then(function (url) {
      A.copyText(url).then(function (ok) {
        A.openModal('<div class="dlg"><h2>Link dla znajomego</h2><p>' + (ok ? 'Link jest już skopiowany. ' : '') + 'Kto go otworzy, zobaczy to zamówienie na żywo: etap, mapę z kurierem i szczegóły.</p>' +
          '<div class="fld"><label>Link<input readonly id="share-url" value="' + esc(url) + '" data-act="select-all"></label></div>' +
          (location.protocol === 'file:' ? '<p class="notice notice--warn">Strona jest teraz otwarta z pliku na dysku. Link zadziała u innych dopiero, gdy strona będzie w internecie.</p>' : '') +
          '<div class="dlg__btns"><button class="btn btn--ghost" type="button" data-act="modal-close">Zamknij</button><button class="btn btn--primary" type="button" data-act="share-copy" autofocus>' + icon('copy') + 'Skopiuj link</button></div></div>',
        { label: 'Link dla znajomego', cls: 'modal--small' });
      });
    });
  });
  act['adm-oitem-add'] = guard(function () {
    var o = curOrder(); if (!o) return;
    o.items.push({ name: '', opts: '', qty: 1, price: 0 }); o.sample = false; commit(); rerender();
    var rows = document.querySelectorAll('.orow__n'); if (rows.length) rows[rows.length - 1].focus();
  });
  act['adm-oitem-del'] = guard(function (el) {
    var o = curOrder(); if (!o) return;
    o.items.splice(+el.getAttribute('data-k'), 1); o.sample = false; commit(); rerender();
  });
  act['adm-stage'] = guard(function (el) {
    var o = curOrder(); if (!o) return;
    var m = 60000, c = +o.times.confirm || 0, p = +o.times.prep || 0, r = +o.times.ride || 0, now = Date.now(), s = el.getAttribute('data-s');
    if (s === 'zlozone') o.placedAt = now;
    else if (s === 'kuchnia') o.placedAt = now - Math.round((c + p * 0.35) * m);
    else if (s === 'droga') o.placedAt = now - Math.round((c + p + r * 0.3) * m);
    else o.placedAt = now - (c + p + r + 4) * m;
    o.status = 'auto'; o.revealSeen = false;
    commit(); rerender();
  });
  act['adm-reveal-now'] = guard(function (el) { A.save(); location.hash = '#/zamowienie/' + el.getAttribute('data-id') + '/zart'; });

  act['adm-r-new'] = guard(function () {
    var s = S(), id = A.uid('lokal-');
    s.restaurants.unshift({
      id: id, name: 'Nowy lokal', kitchen: '', cuisines: [], art: 'pizza', color: '#2E6B4F', cover: '', logo: '',
      rating: 4.6, reviews: 120, timeMin: 25, timeMax: 40, fee: 4.99, minOrder: 30, freeFrom: 0,
      open: true, opensAt: '', badge: '', sponsored: false, isNew: true, hidden: false, address: '',
      menu: [{ id: A.uid('k'), name: 'Dania', items: [{ id: A.uid('d'), name: 'Pierwsze danie', desc: '', price: 25, img: '', popular: true, variants: [], extras: [] }] }]
    });
    commit(); location.hash = '#/admin/lokal/' + id;
  });
  act['adm-r-del'] = guard(function (el) {
    var id = el.getAttribute('data-id'), back = el.getAttribute('data-back'), r = A.getR(id); if (!r) return;
    A.confirmBox('Usunąć lokal?', r.name + ' zniknie ze strony razem z całym menu. Złożone wcześniej zamówienia zostaną w historii.', 'Usuń lokal', function () {
      var s = S(); s.restaurants = s.restaurants.filter(function (x) { return x.id !== id; });
      if (s.basket.rid === id) s.basket = { rid: null, lines: [] };
      commit();
      if (back) location.hash = '#/admin/lokale'; else rerender();
    }, true);
  });
  act['adm-r-dup'] = guard(function (el) {
    var s = S(), i = s.restaurants.findIndex(function (x) { return x.id === el.getAttribute('data-id'); }); if (i < 0) return;
    var c = A.clone(s.restaurants[i]);
    c.id = A.uid('lokal-'); c.name = c.name + ' (kopia)';
    c.menu.forEach(function (k) { k.id = A.uid('k'); k.items.forEach(function (it) { it.id = A.uid('d'); }); });
    s.restaurants.splice(i + 1, 0, c); commit(); rerender(); toast('Kopia lokalu dodana pod oryginałem.');
  });
  act['adm-r-move'] = guard(function (el) {
    var s = S(), i = s.restaurants.findIndex(function (x) { return x.id === el.getAttribute('data-id'); }); if (i < 0) return;
    moveIn(s.restaurants, i, +el.getAttribute('data-d')); commit(); rerender();
  });
  act['adm-r-hide'] = guard(function (el) {
    var r = A.getR(el.getAttribute('data-id')); if (!r) return;
    r.hidden = !r.hidden; commit(); rerender();
  });
  act['adm-cat-add'] = guard(function () {
    var r = curRest(); if (!r) return;
    r.menu.push({ id: A.uid('k'), name: '', items: [] }); commit(); rerender();
    var heads = document.querySelectorAll('.mcatE__head input'); if (heads.length) heads[heads.length - 1].focus();
  });
  act['adm-cat-del'] = guard(function (el) {
    var r = curRest(), ci = +el.getAttribute('data-c'); if (!r || !r.menu[ci]) return;
    var c = r.menu[ci];
    function go() { r.menu.splice(ci, 1); commit(); rerender(); }
    if (!c.items.length) return go();
    A.confirmBox('Usunąć kategorię?', 'Kategoria ' + (c.name || 'bez nazwy') + ' zniknie razem z daniami (' + c.items.length + ').', 'Usuń kategorię', go, true);
  });
  act['adm-cat-move'] = guard(function (el) {
    var r = curRest(); if (!r) return;
    moveIn(r.menu, +el.getAttribute('data-c'), +el.getAttribute('data-d')); commit(); rerender();
  });
  act['adm-item-add'] = guard(function (el) {
    var r = curRest(), ci = +el.getAttribute('data-c'); if (!r || !r.menu[ci]) return;
    r.menu[ci].items.push({ id: A.uid('d'), name: '', desc: '', price: 0, img: '', popular: false, variants: [], extras: [] });
    commit(); rerender();
    var cat = document.querySelectorAll('.mcatE')[ci], rows = cat ? cat.querySelectorAll('.mrowE__n') : [];
    if (rows.length) rows[rows.length - 1].focus();
  });
  act['adm-item-del'] = guard(function (el) {
    var r = curRest(), c = r && r.menu[+el.getAttribute('data-c')]; if (!c) return;
    c.items.splice(+el.getAttribute('data-i'), 1); commit(); rerender();
  });
  act['adm-item-move'] = guard(function (el) {
    var r = curRest(), c = r && r.menu[+el.getAttribute('data-c')]; if (!c) return;
    moveIn(c.items, +el.getAttribute('data-i'), +el.getAttribute('data-d')); commit(); rerender();
  });
  act['adm-item-pop'] = guard(function (el) {
    var r = curRest(), c = r && r.menu[+el.getAttribute('data-c')], it = c && c.items[+el.getAttribute('data-i')]; if (!it) return;
    it.popular = !it.popular; commit(); rerender();
  });
  act['adm-item-edit'] = guard(function (el) { openItemEditor(+el.getAttribute('data-c'), +el.getAttribute('data-i')); });
  act['adm-img-clear'] = guard(function (el) {
    var path = el.getAttribute('data-path');
    setPath(path, ''); commit(); refreshImgField(path); recalc();
  });

  act['adm-cui-add'] = guard(function () {
    S().settings.cuisines.push({ id: A.uid('kuchnia-'), name: '', art: 'pizza' }); commit(); rerender();
    var rows = document.querySelectorAll('.srow input[data-bind^="settings.cuisines"]'); if (rows.length) rows[rows.length - 1].focus();
  });
  act['adm-cui-del'] = guard(function (el) {
    var s = S(), i = +el.getAttribute('data-i'), c = s.settings.cuisines[i]; if (!c) return;
    s.settings.cuisines.splice(i, 1);
    s.restaurants.forEach(function (r) { r.cuisines = r.cuisines.filter(function (x) { return x !== c.id; }); });
    if (A.ui.cuisine === c.id) A.ui.cuisine = 'all';
    commit(); rerender();
  });
  act['adm-v-add'] = guard(function () { S().settings.vouchers.push({ code: '', kind: 'kwota', value: 10 }); commit(); rerender(); });
  act['adm-v-del'] = guard(function (el) { S().settings.vouchers.splice(+el.getAttribute('data-i'), 1); commit(); rerender(); });

  act['adm-export'] = guard(function () {
    A.save();
    download('szamka-kopia-' + toLocal(Date.now()).slice(0, 10) + '.json', JSON.stringify(S(), null, 1), 'application/json');
  });
  act['adm-export-js'] = guard(function () {
    var s = S();
    var out = { seed: 'panel-' + Date.now(), settings: s.settings, user: { address: '', apt: '', floor: '', name: '', phone: '', email: '' }, restaurants: s.restaurants, orders: [] };
    download('dane.js', '/* Szamka: dane startowe wygenerowane w panelu ' + toLocal(Date.now()).replace('T', ' ') + '. Podmień tym plikiem js/dane.js. */\nwindow.SZAMKA_START = ' + JSON.stringify(out, null, 1) + ';\n', 'text/javascript');
  });
  act['adm-reset'] = guard(function () {
    A.confirmBox('Przywrócić dane startowe?', 'Znikną wszystkie zmiany w lokalach i menu, wszystkie zamówienia i koszyk zapisane w tej przeglądarce. Tego nie da się cofnąć.', 'Przywróć dane startowe', function () {
      try { localStorage.removeItem(A.KEY); } catch (e) { /* nic */ }
      A.replace(A.fresh()); A.save(); rerender(); toast('Wróciły dane startowe.');
    }, true);
  });

  SZ.admin = { view: view, pill: pill, onInput: onInput, onChange: onChange, after: function () { recalc(); } };
})();
