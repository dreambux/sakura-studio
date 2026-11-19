/* Szamka: ilustracje rysowane w SVG, bez zdjęć.
   Talerze widziane z góry (symbole d-*), okładki lokali, stół na stronie głównej i mapa dostawy. */
(function () {
  'use strict';
  var SZ = window.SZ = window.SZ || {};

  /* ---------- pomocnicze ---------- */
  function rng(seed) {
    var t = seed >>> 0;
    return function () {
      t = (t + 0x6D2B79F5) >>> 0;
      var x = Math.imul(t ^ (t >>> 15), 1 | t);
      x ^= x + Math.imul(x ^ (x >>> 7), 61 | x);
      return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
    };
  }
  function hash(str) {
    var h = 2166136261;
    str = String(str);
    for (var i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function f(n) { return Math.round(n * 10) / 10; }
  function ring(n, r, fn, off, cx, cy) {
    var s = '';
    cx = cx == null ? 60 : cx; cy = cy == null ? 60 : cy; off = off || 0;
    for (var i = 0; i < n; i++) {
      var a = off + i * 2 * Math.PI / n;
      s += fn(f(cx + r * Math.cos(a)), f(cy + r * Math.sin(a)), f(a * 180 / Math.PI), i);
    }
    return s;
  }
  function plate(fill, rim) {
    return '<circle cx="60" cy="60" r="57" fill="' + (fill || '#FFFFFF') + '"/>' +
      '<circle cx="60" cy="60" r="46" fill="none" stroke="' + (rim || '#ECE6E1') + '" stroke-width="1.5"/>';
  }
  function leaf(x, y, a, c, k) {
    k = k || 1;
    return '<path d="M0 0c' + f(3.5 * k) + '-' + f(5.5 * k) + ' ' + f(10.5 * k) + '-' + f(5.5 * k) + ' ' + f(14 * k) + ' 0-' +
      f(3.5 * k) + ' ' + f(5.5 * k) + '-' + f(10.5 * k) + ' ' + f(5.5 * k) + '-' + f(14 * k) + ' 0z" fill="' + (c || '#2E8B3D') +
      '" transform="translate(' + x + ' ' + y + ') rotate(' + a + ')"/>';
  }
  function cup(x, y, r, c, extra) {
    return '<circle cx="' + x + '" cy="' + y + '" r="' + r + '" fill="#fff" stroke="#E6DFD8" stroke-width="1.2"/>' +
      '<circle cx="' + x + '" cy="' + y + '" r="' + f(r * 0.72) + '" fill="' + c + '"/>' + (extra || '');
  }

  /* ---------- dania (viewBox 0 0 120 120) ---------- */
  var D = {};

  D.pizza = function () {
    var s = plate();
    s += '<circle cx="60" cy="60" r="47" fill="#D79A48"/><circle cx="60" cy="60" r="42.5" fill="#C63B27"/><circle cx="60" cy="60" r="40.5" fill="#F3CB58"/>';
    s += '<g fill="#F9E08E" opacity=".75"><circle cx="45" cy="47" r="9"/><circle cx="75" cy="72" r="11"/><circle cx="72" cy="42" r="7"/><circle cx="42" cy="74" r="8"/></g>';
    s += '<g stroke="#B47E2C" stroke-width="1" opacity=".5">' + [0, 45, 90, 135].map(function (a) {
      return '<path d="M60 14v92" transform="rotate(' + a + ' 60 60)"/>';
    }).join('') + '</g>';
    s += ring(6, 26, function (x, y) {
      return '<circle cx="' + x + '" cy="' + y + '" r="6.6" fill="#AE2A1B"/><circle cx="' + f(x - 1.8) + '" cy="' + f(y - 1.8) + '" r="1.6" fill="#D0503F"/><circle cx="' + f(x + 2) + '" cy="' + f(y + 1.6) + '" r="1.1" fill="#8E1F13"/>';
    }, 0.35);
    s += '<circle cx="60" cy="60" r="6.6" fill="#AE2A1B"/><circle cx="58.2" cy="58.2" r="1.6" fill="#D0503F"/>';
    s += ring(3, 14, function (x, y, a) { return leaf(x, y, f(a + 70)); }, 1.4);
    s += ring(5, 35, function (x, y) {
      return '<circle cx="' + x + '" cy="' + y + '" r="2.5" fill="none" stroke="#2A2233" stroke-width="2"/>';
    }, 0.95);
    return s;
  };

  D.burger = function () {
    var r = rng(7), s = plate(), i;
    for (i = 0; i < 9; i++) {
      s += '<rect x="-2.2" y="-13" width="4.4" height="26" rx="1.6" fill="' + (i % 3 ? '#F2C23B' : '#E5A92A') +
        '" transform="translate(' + f(84 + r() * 12) + ' ' + f(38 + r() * 24) + ') rotate(' + f(-70 + r() * 140) + ')"/>';
    }
    s += '<circle cx="46" cy="60" r="29" fill="#69B341"/><circle cx="46" cy="60" r="30" fill="none" stroke="#69B341" stroke-width="7" stroke-dasharray="0.1 7.75" stroke-linecap="round"/>';
    s += '<rect x="20" y="34" width="52" height="52" rx="4" fill="#F7C22F" transform="rotate(18 46 60)"/>';
    s += '<circle cx="46" cy="60" r="27.5" fill="#D08427"/><circle cx="44.5" cy="57.5" r="23.5" fill="#E09A3A"/><ellipse cx="40" cy="51" rx="12" ry="8" fill="#EDB35A" opacity=".8"/>';
    for (i = 0; i < 16; i++) {
      var an = r() * 6.283, d = Math.sqrt(r()) * 21;
      s += '<ellipse rx="2" ry="1.1" fill="#FFF2CF" transform="translate(' + f(46 + d * Math.cos(an)) + ' ' + f(60 + d * Math.sin(an)) + ') rotate(' + f(r() * 180) + ')"/>';
    }
    s += cup(90, 86, 9.5, '#D6352A', '<circle cx="88" cy="84" r="1.8" fill="#EC6A5F"/>');
    return s;
  };

  D.kebab = function () {
    var s = plate();
    s += '<g transform="rotate(-28 60 60)">';
    s += '<ellipse cx="97" cy="60" rx="8.5" ry="14.5" fill="#6FB446"/>';
    s += '<ellipse cx="99" cy="55" rx="5" ry="6" fill="#7B4124"/><ellipse cx="98.5" cy="66" rx="5" ry="5" fill="#8C4C2B"/>';
    s += '<circle cx="102.5" cy="61" r="3.2" fill="#DE4638"/><path d="M95 49c3 1 5 3 5 6" stroke="#9A58A6" stroke-width="2" fill="none" stroke-linecap="round"/>';
    s += '<rect x="22" y="44" width="76" height="32" rx="15" fill="#EACB92"/>';
    s += '<g fill="#C99755" opacity=".7"><ellipse cx="70" cy="52" rx="5" ry="2.2"/><ellipse cx="82" cy="64" rx="4" ry="2"/><ellipse cx="74" cy="69" rx="3" ry="1.6"/><ellipse cx="88" cy="55" rx="3" ry="1.5"/></g>';
    s += '<path d="M22 60c0-9 6-16 15-16h23l-4 6 4 5-5 5 5 6-4 5 3 5H37c-9 0-15-7-15-16z" fill="#CBD2DA"/>';
    s += '<path d="M34 46l-3 7 4 6-4 7 3 8M46 45l-2 8 3 6-3 8 2 8" stroke="#AEB7C2" stroke-width="1" fill="none"/>';
    s += '</g>';
    s += cup(34, 34, 9, '#F4EAD2', '<circle cx="33" cy="33" r="1" fill="#7CA05A"/><circle cx="36" cy="36" r=".9" fill="#7CA05A"/>');
    s += cup(88, 88, 9, '#D6402E');
    return s;
  };

  D.sushi = function () {
    var s = '<circle cx="60" cy="60" r="57" fill="#2A2C3A"/><circle cx="60" cy="60" r="46" fill="none" stroke="#3B3E50" stroke-width="1.5"/>';
    var fill = ['#F2835A', '#7DBB55', '#D94F5E', '#F2835A', '#F4C542', '#7DBB55'];
    [[36, 40], [54, 36], [72, 40], [38, 58], [56, 55], [74, 58]].forEach(function (p, i) {
      s += '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="8.6" fill="#14231C"/><circle cx="' + p[0] + '" cy="' + p[1] + '" r="6.6" fill="#FBFAF3"/><circle cx="' + p[0] + '" cy="' + p[1] + '" r="2.9" fill="' + fill[i] + '"/>';
    });
    [[40, 82, -18, '#F2835A', '#F9C3AC'], [65, 85, -12, '#D94F5E', '#EFA0A8']].forEach(function (n) {
      s += '<g transform="translate(' + n[0] + ' ' + n[1] + ') rotate(' + n[2] + ')"><rect x="-11" y="-4" width="22" height="10" rx="5" fill="#FBFAF3"/><rect x="-12.5" y="-7" width="25" height="9.5" rx="4.7" fill="' + n[3] + '"/><path d="M-6-6.5l-3 8M0-7l-3 9M6-6.5l-3 8" stroke="' + n[4] + '" stroke-width="1.4" stroke-linecap="round"/></g>';
    });
    s += '<circle cx="91" cy="50" r="5.5" fill="#8BC34A"/><circle cx="89.5" cy="48.5" r="1.6" fill="#A9D86E"/>';
    s += '<g fill="#F5B3BF"><ellipse cx="88" cy="70" rx="7" ry="4" transform="rotate(-20 88 70)"/><ellipse cx="92" cy="75" rx="6" ry="3.4" transform="rotate(15 92 75)"/><ellipse cx="85" cy="77" rx="5" ry="3" transform="rotate(-35 85 77)"/></g>';
    return s;
  };

  D.pierogi = function () {
    var r = rng(5), s = plate(), i;
    s += '<circle cx="60" cy="60" r="51" fill="none" stroke="#4673B8" stroke-width="2.6" stroke-dasharray="0.1 6.16" stroke-linecap="round"/>';
    for (i = 0; i < 14; i++) {
      var an = r() * 6.283, d = 12 + r() * 30;
      s += '<rect x="-1.4" y="-.8" width="2.8" height="1.6" rx=".6" fill="#B56C2F" transform="translate(' + f(60 + d * Math.cos(an)) + ' ' + f(60 + d * Math.sin(an)) + ') rotate(' + f(r() * 180) + ')"/>';
    }
    s += ring(6, 28, function (x, y, a) {
      return '<g transform="translate(' + x + ' ' + y + ') rotate(' + f(a + 90) + ')"><path d="M-11.5 5a11.5 12 0 0 1 23 0z" fill="#C9A45C" transform="translate(.8 1.4)" opacity=".5"/><path d="M-11.5 5a11.5 12 0 0 1 23 0z" fill="#EFD592"/><ellipse cx="1" cy="-1" rx="6" ry="3" fill="#DDB262" opacity=".85"/><path d="M-11.5 5a11.5 12 0 0 1 23 0" fill="none" stroke="#C39A4D" stroke-width="2.2" stroke-dasharray="1.8 1.9"/></g>';
    }, 0.2);
    s += '<circle cx="60" cy="60" r="10" fill="#fff" stroke="#E3DCD3" stroke-width="1.2"/><circle cx="60" cy="60" r="7.4" fill="#FBF9F2"/><path d="M56.5 60c1-3 6-3 6 0s-4 3-3 0" stroke="#E4DCC9" stroke-width="1.2" fill="none"/>';
    s += '<g stroke="#3E9A46" stroke-width="1.1" stroke-linecap="round"><path d="M58 57l2-1.5M61.5 62.5l1.5 1.5M57.5 62.5l-.5 1.8"/></g>';
    return s;
  };

  D.ramen = function () {
    var r = rng(13), i;
    var s = '<circle cx="60" cy="60" r="57" fill="#26324A"/><circle cx="60" cy="60" r="51" fill="#1B2436"/><circle cx="60" cy="60" r="47.5" fill="#E0A247"/>';
    s += '<g fill="#EDBE6C" opacity=".8"><circle cx="34" cy="60" r="3"/><circle cx="82" cy="82" r="4"/><circle cx="52" cy="98" r="2.4"/><circle cx="62" cy="24" r="2"/></g>';
    s += '<g fill="none" stroke="#F7E3A6" stroke-width="2.6" stroke-linecap="round">';
    [-10, -4, 2, 8].forEach(function (dy, k) {
      s += '<path d="M29 ' + (66 + dy) + 'c7-9 13 7 20-1s13 7 20-1 12 6 18 0" opacity="' + (k % 2 ? 0.82 : 1) + '"/>';
    });
    s += '</g>';
    s += '<circle cx="42" cy="40" r="10" fill="#C48A69"/><circle cx="42" cy="40" r="6.5" fill="none" stroke="#E3B79D" stroke-width="1.6"/><circle cx="42" cy="40" r="2.2" fill="#E3B79D"/>';
    s += '<g transform="rotate(-20 76 38)"><ellipse cx="76" cy="38" rx="8" ry="10" fill="#fff"/><circle cx="76" cy="39" r="4.6" fill="#F5A623"/><circle cx="74.8" cy="37.8" r="1.3" fill="#FBC661"/></g>';
    s += '<rect x="84" y="54" width="15" height="24" rx="1.2" fill="#1E3A2B" transform="rotate(14 91 66)"/>';
    s += '<circle cx="40" cy="84" r="7.5" fill="#fff" stroke="#F3A4B5" stroke-width="1.2" stroke-dasharray="1.6 1.6"/><path d="M40 84c0-2.5 3.5-2.5 3.5 0s-5 4-5.5 0 3-6 6-4" fill="none" stroke="#EE7F97" stroke-width="1.4" stroke-linecap="round"/>';
    for (i = 0; i < 9; i++) {
      s += '<circle cx="' + f(54 + r() * 24) + '" cy="' + f(78 + r() * 16) + '" r="1.9" fill="none" stroke="#4E9D37" stroke-width="1.4"/>';
    }
    return s;
  };

  D.curry = function () {
    var r = rng(3), i;
    var s = '<circle cx="60" cy="60" r="57" fill="#FAF7F2"/><circle cx="60" cy="60" r="50" fill="#EFE9E0"/><circle cx="60" cy="60" r="46.5" fill="#D7802B"/>';
    s += '<g fill="#E79B3F" opacity=".8"><circle cx="78" cy="44" r="8"/><circle cx="84" cy="70" r="9"/><circle cx="68" cy="88" r="6"/></g>';
    s += '<path d="M56 13.67A46.5 46.5 0 0 0 56 106.33c4-8-5-13-1-22s-6-14-2-24-5-13-1-23 5-14 4-23.66z" fill="#FDFBF4"/>';
    for (i = 0; i < 22; i++) {
      var x = 20 + r() * 30, y = 30 + r() * 60;
      if ((x - 60) * (x - 60) + (y - 60) * (y - 60) > 41 * 41) continue;
      s += '<ellipse rx="2.1" ry=".9" fill="#E9E1CF" transform="translate(' + f(x) + ' ' + f(y) + ') rotate(' + f(r() * 180) + ')"/>';
    }
    [[72, 48, 12], [86, 60, -25], [70, 68, 40], [82, 80, -10], [66, 30, 20]].forEach(function (c) {
      s += '<g transform="translate(' + c[0] + ' ' + c[1] + ') rotate(' + c[2] + ')"><rect x="-6" y="-4.5" width="12" height="9" rx="3.4" fill="#F0B766"/><rect x="-4" y="-3.2" width="6" height="3" rx="1.5" fill="#F7D197"/></g>';
    });
    s += '<path d="M64 40c9 2 15 9 17 18" stroke="#F8DDB0" stroke-width="2" fill="none" stroke-linecap="round" opacity=".9"/>';
    s += leaf(74, 58, 20, '#3E9A46', 0.62) + leaf(88, 72, -40, '#3E9A46', 0.62) + leaf(64, 94, -70, '#3E9A46', 0.62) + leaf(34, 46, 10, '#3E9A46', 0.62);
    s += '<path d="M28 76c5 3 11 2 15-2" stroke="#D2362B" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M43 74l2.5-2" stroke="#3E9A46" stroke-width="1.6" stroke-linecap="round"/>';
    return s;
  };

  D.salatka = function () {
    var r = rng(9), i;
    var s = '<circle cx="60" cy="60" r="57" fill="#C48D58"/><circle cx="60" cy="60" r="51" fill="#AF7740"/><circle cx="60" cy="60" r="47.5" fill="#4B9A47"/>';
    var greens = ['#6CBA59', '#3D873D', '#86C96B'];
    for (i = 0; i < 15; i++) {
      var an = r() * 6.283, d = Math.sqrt(r()) * 35;
      s += '<ellipse rx="' + f(9 + r() * 6) + '" ry="' + f(5 + r() * 3) + '" fill="' + greens[i % 3] + '" opacity=".9" transform="translate(' + f(60 + d * Math.cos(an)) + ' ' + f(60 + d * Math.sin(an)) + ') rotate(' + f(r() * 180) + ')"/>';
    }
    for (i = 0; i < 4; i++) {
      s += '<path d="M-3-12c6 4 6 20 0 24-5-4-5-20 0-24z" fill="#D3E28A" stroke="#7FA43B" stroke-width="1.4" transform="translate(' + f(33 + i * 6.5) + ' ' + f(45 + i * 1.5) + ') rotate(' + (-25 + i * 7) + ')"/>';
    }
    [[78, 38], [89, 57], [72, 54]].forEach(function (p) {
      s += '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="7" fill="#DE4436"/><circle cx="' + p[0] + '" cy="' + p[1] + '" r="4.6" fill="#EE6C5E"/><circle cx="' + (p[0] - 1.6) + '" cy="' + (p[1] - 1) + '" r="1" fill="#F7D38A"/><circle cx="' + (p[0] + 1.6) + '" cy="' + (p[1] + 1.2) + '" r="1" fill="#F7D38A"/>';
    });
    [[44, 82], [57, 90], [36, 69]].forEach(function (p) {
      s += '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="6.6" fill="#B5DE96" stroke="#3D873D" stroke-width="1.6"/><circle cx="' + p[0] + '" cy="' + p[1] + '" r="2.6" fill="#DDF1CB"/>';
    });
    [[70, 76, 12], [82, 80, -20], [76, 89, 30], [63, 67, -8]].forEach(function (c) {
      s += '<rect x="-3.4" y="-3.4" width="6.8" height="6.8" rx="1" fill="#FFFDF6" transform="translate(' + c[0] + ' ' + c[1] + ') rotate(' + c[2] + ')"/>';
    });
    s += '<circle cx="58" cy="40" r="6" fill="none" stroke="#A65BAA" stroke-width="1.6"/><circle cx="92" cy="72" r="4.5" fill="none" stroke="#A65BAA" stroke-width="1.5"/>';
    for (i = 0; i < 12; i++) {
      s += '<circle cx="' + f(30 + r() * 60) + '" cy="' + f(30 + r() * 60) + '" r=".9" fill="#F3E6B8"/>';
    }
    return s;
  };

  D.nalesniki = function () {
    var r = rng(17), s = plate(), i;
    s += '<circle cx="60" cy="63" r="34" fill="#BF8236"/><circle cx="60" cy="60" r="33" fill="#DFA552"/><circle cx="59" cy="59" r="27.5" fill="#EBBA6C"/>';
    s += '<path d="M44 52c4-9 20-12 30-5 8 6 9 16 3 23-3 4-1 9-5 10s-4-4-9-3-9 5-14 1-2-7-5-11-3-9 0-15z" fill="#8B4A1C" opacity=".92"/>';
    s += '<path d="M50 54c4-5 12-7 19-4" stroke="#B8763C" stroke-width="2" fill="none" stroke-linecap="round"/>';
    s += '<rect x="53" y="52" width="14" height="13" rx="2.2" fill="#FFE98F" transform="rotate(14 60 58)"/><rect x="55" y="54" width="6" height="4" rx="1.4" fill="#FFF5C4" transform="rotate(14 60 58)"/>';
    [[24, 44, -20], [95, 80, 30], [32, 89, 10]].forEach(function (b) {
      s += '<g transform="translate(' + b[0] + ' ' + b[1] + ') rotate(' + b[2] + ')"><path d="M0 9C-7 4-8-3-4-6c2-1.6 6-1.6 8 0C8-3 7 4 0 9z" fill="#D9362F"/><path d="M-4-6l4 2.2 4-2.2-4-2z" fill="#3E9A46"/><g fill="#F6B2A6"><circle cx="-2" cy="-1" r=".6"/><circle cx="2" cy="0" r=".6"/><circle cx="0" cy="4" r=".6"/></g></g>';
    });
    [[90, 40], [97, 51], [25, 67], [84, 95], [41, 22], [50, 100]].forEach(function (b) {
      s += '<circle cx="' + b[0] + '" cy="' + b[1] + '" r="3.7" fill="#3B4A8C"/><circle cx="' + (b[0] - .6) + '" cy="' + (b[1] - .8) + '" r="1.2" fill="#22306B"/>';
    });
    s += leaf(80, 28, 20, '#3E9A46', 0.7);
    for (i = 0; i < 18; i++) {
      var an = r() * 6.283, d = 20 + r() * 12;
      s += '<circle cx="' + f(60 + d * Math.cos(an)) + '" cy="' + f(60 + d * Math.sin(an)) + '" r=".8" fill="#fff" opacity=".9"/>';
    }
    return s;
  };

  D.makaron = function () {
    var r = rng(29), s = plate(), i;
    s += '<circle cx="60" cy="60" r="36" fill="#EFCB78"/>';
    s += '<g fill="none" stroke="#D9AE52" stroke-width="2.4" stroke-linecap="round">';
    [[32, '30 7', 0], [27, '22 6', 40], [22, '26 5', 100], [17, '16 5', 10], [12, '14 4', 70]].forEach(function (c) {
      s += '<circle cx="60" cy="60" r="' + c[0] + '" stroke-dasharray="' + c[1] + '" transform="rotate(' + c[2] + ' 60 60)"/>';
    });
    s += '</g><g fill="none" stroke="#F9E4A8" stroke-width="1.3" stroke-linecap="round"><circle cx="60" cy="60" r="29.5" stroke-dasharray="18 12" transform="rotate(20 60 60)"/><circle cx="60" cy="60" r="19.5" stroke-dasharray="12 9" transform="rotate(75 60 60)"/></g>';
    s += '<path d="M47 56c2-8 14-11 22-6s8 14 2 19-17 5-22 0-3-9-2-13z" fill="#C43A27"/>';
    for (i = 0; i < 7; i++) {
      s += '<circle cx="' + f(52 + r() * 16) + '" cy="' + f(54 + r() * 12) + '" r="' + f(1.4 + r()) + '" fill="#8A2A1B"/>';
    }
    s += leaf(56, 60, -30, '#2E8B3D', 0.7) + leaf(62, 62, 40, '#2E8B3D', 0.62);
    for (i = 0; i < 9; i++) {
      var an = r() * 6.283, d = 14 + r() * 20;
      s += '<path d="M0 0l3.4 1.2-2 2.4z" fill="#FFF6CF" transform="translate(' + f(60 + d * Math.cos(an)) + ' ' + f(60 + d * Math.sin(an)) + ') rotate(' + f(r() * 360) + ')"/>';
    }
    return s;
  };

  D.tacos = function () {
    var s = plate();
    [[36, 52, -12], [60, 45, 0], [84, 53, 12]].forEach(function (t) {
      s += '<g transform="translate(' + t[0] + ' ' + t[1] + ') rotate(' + t[2] + ')">' +
        '<path d="M-15 8c3-6 4 2 7-3s4 3 7-2 4 3 7-2 4 2 6 0" fill="none" stroke="#63B24B" stroke-width="5" stroke-linecap="round"/>' +
        '<path d="M-17 6a17 18 0 0 1 34 0z" fill="#EDBB45"/><path d="M-17 6a17 18 0 0 1 34 0" fill="none" stroke="#D49C2C" stroke-width="1.4"/>' +
        '<g fill="#D8A53A" opacity=".8"><circle cx="-6" cy="-4" r="1.2"/><circle cx="5" cy="-7" r="1"/><circle cx="8" cy="0" r="1.2"/><circle cx="-2" cy="1" r="1"/></g>' +
        '<circle cx="-9" cy="9.5" r="2.6" fill="#DE4436"/><circle cx="3" cy="10.5" r="2.4" fill="#DE4436"/><circle cx="11" cy="9.5" r="2.2" fill="#DE4436"/>' +
        '<path d="M-4 8l3 4M7 8l2 4M-12.5 7l2 3" stroke="#F7D046" stroke-width="1.6" stroke-linecap="round"/></g>';
    });
    s += '<g transform="translate(42 86) rotate(-20)"><path d="M-10 0a10 10 0 0 0 20 0z" fill="#7CB342"/><path d="M-7.5 0a7.5 7.5 0 0 0 15 0z" fill="#D4EDA0"/><path d="M0 0v7.5M0 0l-5 5.5M0 0l5 5.5" stroke="#9CCC65" stroke-width="1"/></g>';
    s += cup(76, 86, 10, '#C8372A', '<g fill="#6DB33F"><circle cx="74" cy="84" r="1"/><circle cx="78" cy="88" r="1"/><circle cx="78.5" cy="83.5" r=".8"/></g><circle cx="73.5" cy="88.5" r="1" fill="#F4E3B0"/>');
    return s;
  };

  D.obiad = function () {
    var r = rng(21), s = plate(), i;
    s += '<path d="M22 58c-2-12 8-24 22-26 12-2 24 3 28 13 3 9-1 17-9 23-9 7-24 9-33 3-5-3-7-8-8-13z" fill="#BF7B2A"/>';
    s += '<path d="M27 57c-1-9 7-19 18-21 10-1 19 3 22 11 2 7-2 13-8 18-8 5-19 7-26 2-4-3-5-6-6-10z" fill="#D69A45"/>';
    for (i = 0; i < 16; i++) {
      var an = r() * 6.283, d = Math.sqrt(r());
      s += '<circle cx="' + f(47 + d * 17 * Math.cos(an)) + '" cy="' + f(55 + d * 13 * Math.sin(an)) + '" r="' + f(.7 + r() * .7) + '" fill="#B06E22"/>';
    }
    s += '<g transform="translate(40 47) rotate(-25)"><path d="M-8 0a8 8 0 0 1 16 0z" fill="#F6D84A"/><path d="M-6 0a6 6 0 0 1 12 0z" fill="#FBEF9E"/><path d="M0 0v-6M0 0l-4-4.4M0 0l4-4.4" stroke="#F6D84A" stroke-width=".9"/></g>';
    [[82, 38, 8, 10], [93, 52, 7.5, -30], [79, 55, 7, 40]].forEach(function (p) {
      s += '<g transform="translate(' + p[0] + ' ' + p[1] + ') rotate(' + p[3] + ')"><ellipse rx="' + p[2] + '" ry="' + f(p[2] * .82) + '" fill="#F2DC8C"/><ellipse cx="-1.5" cy="-1.5" rx="' + f(p[2] * .5) + '" ry="' + f(p[2] * .34) + '" fill="#F9ECB8"/><path d="M-2 2l2-1M2 3l1.6-1.4M3-1l1.6.4" stroke="#3E9A46" stroke-width="1" stroke-linecap="round"/></g>';
    });
    s += '<ellipse cx="64" cy="88" rx="23" ry="12" fill="#FBF9F1"/>';
    for (i = 0; i < 6; i++) {
      var cx = 47 + i * 6.6, cy = 89 - Math.sin(i / 5 * Math.PI) * 3;
      s += '<circle cx="' + f(cx) + '" cy="' + f(cy) + '" r="6" fill="#CDE9B3" stroke="#7DB85B" stroke-width="1.3"/><circle cx="' + f(cx) + '" cy="' + f(cy) + '" r="2.4" fill="#E6F4D7"/>';
    }
    s += '<g stroke="#3E9A46" stroke-width="1" stroke-linecap="round"><path d="M56 82l1.6-1.6M70 81l1.8 1M78 92l1.8-1"/></g>';
    return s;
  };

  var DISHES = ['pizza', 'burger', 'kebab', 'sushi', 'pierogi', 'ramen', 'curry', 'salatka', 'nalesniki', 'makaron', 'tacos', 'obiad'];
  var DISH_NAMES = {
    pizza: 'Pizza', burger: 'Burger z frytkami', kebab: 'Kebab w tortilli', sushi: 'Sushi', pierogi: 'Pierogi', ramen: 'Ramen',
    curry: 'Curry z ryżem', salatka: 'Sałatka', nalesniki: 'Pancakes z owocami', makaron: 'Makaron', tacos: 'Tacos', obiad: 'Schabowy z ziemniakami'
  };
  var COMPANION = {
    pizza: ['makaron', 'salatka'], burger: ['salatka', 'nalesniki'], kebab: ['salatka', 'tacos'], sushi: ['ramen', 'salatka'],
    pierogi: ['obiad', 'nalesniki'], ramen: ['sushi', 'curry'], curry: ['salatka', 'ramen'], salatka: ['makaron', 'nalesniki'],
    nalesniki: ['salatka', 'pierogi'], makaron: ['pizza', 'salatka'], tacos: ['salatka', 'curry'], obiad: ['pierogi', 'salatka']
  };

  /* ---------- wspólne symbole i wzory ---------- */
  function sprite() {
    var s = '<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>';
    s += '<pattern id="p-krata-j" width="44" height="44" patternUnits="userSpaceOnUse"><rect width="22" height="44" fill="#fff" opacity=".07"/><rect width="44" height="22" fill="#fff" opacity=".07"/></pattern>';
    s += '<pattern id="p-krata-c" width="44" height="44" patternUnits="userSpaceOnUse"><rect width="22" height="44" fill="#24152B" opacity=".045"/><rect width="44" height="22" fill="#24152B" opacity=".045"/></pattern>';
    s += '<mask id="m-ugryz"><rect width="32" height="32" fill="#fff"/><circle cx="26.5" cy="5.5" r="5.4"/><circle cx="31" cy="13.5" r="4.2"/><circle cx="19" cy="1" r="3.8"/></mask>';
    s += '</defs>';
    DISHES.forEach(function (k) { s += '<symbol id="d-' + k + '" viewBox="0 0 120 120">' + D[k]() + '</symbol>'; });
    s += '<symbol id="d-napoj" viewBox="0 0 60 60"><circle cx="30" cy="30" r="27" fill="#F6F9FB" stroke="#DCE4EA" stroke-width="1.5"/><circle cx="30" cy="30" r="22.5" fill="currentColor"/>' +
      '<rect x="17" y="20" width="11" height="11" rx="2.5" fill="#fff" opacity=".45" transform="rotate(-15 22 25)"/><rect x="30" y="31" width="11" height="11" rx="2.5" fill="#fff" opacity=".4" transform="rotate(25 35 36)"/>' +
      '<circle cx="37" cy="21" r="7.5" fill="#F6D84A"/><circle cx="37" cy="21" r="5.6" fill="#FBEF9E"/><path d="M37 15.4v11.2M31.4 21h11.2M33 17l8 8M41 17l-8 8" stroke="#F6D84A" stroke-width=".9"/>' +
      '<path d="M26 34L48 8" stroke="#fff" stroke-width="4" stroke-linecap="round"/><path d="M26 34L48 8" stroke="#E0312B" stroke-width="4" stroke-linecap="round" stroke-dasharray="4 5"/></symbol>';
    s += '<symbol id="d-sztucce" viewBox="0 0 44 130"><g fill="#F3F0EC"><path d="M4 6v24c0 6 4 7 4 11l-1.5 76a4.5 4.5 0 0 0 9 0L14 41c0-4 4-5 4-11V6h-2.6v22h-3.1V6H9.7v22H6.6V6z"/>' +
      '<path d="M29 6c5 2 9 14 9 30 0 8-2.5 10-4 12l1 69a4.5 4.5 0 0 1-9 0L27 48V8c0-1 1-2 2-2z"/></g></symbol>';
    s += '</svg>';
    return s;
  }

  function lum(hex) {
    var m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex || '');
    if (!m) return 0.5;
    return (0.2126 * parseInt(m[1], 16) + 0.7152 * parseInt(m[2], 16) + 0.0722 * parseInt(m[3], 16)) / 255;
  }
  function dishKey(k) { return DISHES.indexOf(k) >= 0 ? k : 'pizza'; }
  function safeColor(c, fallback) { return /^#[0-9a-f]{6}$/i.test(c || '') ? c : (fallback || '#2E6B4F'); }

  function use(kind, cx, cy, size, rot, shadow) {
    var x = f(cx - size / 2), y = f(cy - size / 2);
    return (shadow === false ? '' : '<circle cx="' + f(cx + size * 0.02) + '" cy="' + f(cy + size * 0.04) + '" r="' + f(size * 0.475) + '" fill="#000" opacity=".16"/>') +
      '<use href="#d-' + kind + '" x="' + x + '" y="' + y + '" width="' + size + '" height="' + size + '" transform="rotate(' + f(rot || 0) + ' ' + f(cx) + ' ' + f(cy) + ')"/>';
  }
  function drink(cx, cy, size, color, rot) {
    return '<circle cx="' + f(cx + 1.5) + '" cy="' + f(cy + 3) + '" r="' + f(size * 0.45) + '" fill="#000" opacity=".14"/>' +
      '<use href="#d-napoj" x="' + f(cx - size / 2) + '" y="' + f(cy - size / 2) + '" width="' + size + '" height="' + size + '" style="color:' + color + '" transform="rotate(' + f(rot || 0) + ' ' + f(cx) + ' ' + f(cy) + ')"/>';
  }
  var DRINKS = ['#F29F3D', '#B5391F', '#7FB9E6', '#F2C94C', '#8E4B2B', '#E9728A'];

  /* Okładka lokalu: stół w kolorze lokalu, główne danie i dodatki. */
  function cover(art, color, seed) {
    art = dishKey(art); color = safeColor(color);
    var r = rng(hash(seed || art)), dark = lum(color) < 0.62;
    var comp = COMPANION[art][Math.floor(r() * 2)];
    var mx = 318 + r() * 56, my = 92 + r() * 22;
    var sx = 46 + r() * 44, sy = 168 + r() * 30;
    var dx = 196 + r() * 36, dy = 34 + r() * 20;
    var s = '<svg class="art" viewBox="0 0 480 200" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">';
    s += '<rect width="480" height="200" fill="' + color + '"/><rect width="480" height="200" fill="url(#p-krata-' + (dark ? 'j' : 'c') + ')"/>';
    s += '<use href="#d-sztucce" x="' + f(mx - 190) + '" y="' + f(my - 76) + '" width="44" height="130" opacity="' + (dark ? '.9' : '1') + '" transform="rotate(' + f(-8 + r() * 16) + ' ' + f(mx - 168) + ' ' + f(my) + ')"/>';
    s += use(comp, sx, sy, 150, r() * 360);
    s += drink(dx, dy, 58, DRINKS[Math.floor(r() * DRINKS.length)], r() * 90);
    s += use(art, mx, my, 216, -20 + r() * 40);
    if (r() > 0.4) s += drink(452 + r() * 20, 176 + r() * 16, 52, DRINKS[Math.floor(r() * DRINKS.length)], r() * 90);
    return s + '</svg>';
  }

  /* Szeroki baner na stronie lokalu. Najważniejsze dania są pośrodku, bo telefon pokazuje tylko środek. */
  function banner(art, color, seed) {
    art = dishKey(art); color = safeColor(color);
    var r = rng(hash((seed || art) + '-baner')), dark = lum(color) < 0.62;
    var c1 = COMPANION[art][0], c2 = COMPANION[art][1];
    function d() { return DRINKS[Math.floor(r() * DRINKS.length)]; }
    var s = '<svg class="art" viewBox="0 0 1440 240" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">';
    s += '<rect width="1440" height="240" fill="' + color + '"/><rect width="1440" height="240" fill="url(#p-krata-' + (dark ? 'j' : 'c') + ')"/>';
    s += use(c2, 20, 40, 200, r() * 360);
    s += use(art, 190, 200, 230, -20 + r() * 40);
    s += drink(345, 62, 60, d(), r() * 90);
    s += use(c1, 470, 52, 200, r() * 360);
    s += drink(555, 196, 62, d(), r() * 90);
    s += '<use href="#d-sztucce" x="868" y="46" width="48" height="142" transform="rotate(' + f(-6 + r() * 12) + ' 892 117)"/>';
    s += use(art, 720, 132, 290, -15 + r() * 30);
    s += use(c2, 1030, 196, 210, r() * 360);
    s += drink(1010, 44, 58, d(), r() * 90);
    s += use(c1, 1250, 66, 210, r() * 360);
    s += drink(1190, 204, 60, d(), r() * 90);
    s += use(art, 1430, 210, 220, -20 + r() * 40);
    return s + '</svg>';
  }

  /* Pojedynczy talerz, np. w kafelku kuchni albo w koszyku. */
  function dish(art, cls) {
    return '<svg class="' + (cls || 'dish') + '" viewBox="0 0 120 120" aria-hidden="true" focusable="false"><use href="#d-' + dishKey(art) + '"/></svg>';
  }

  /* Stół na stronie głównej: szeroki kadr, dania zebrane po prawej, żeby było je widać także na telefonie. */
  function hero() {
    var s = '<svg class="art" viewBox="0 0 1440 520" preserveAspectRatio="xMaxYMid slice" aria-hidden="true" focusable="false">';
    s += '<rect width="1440" height="520" fill="#E0312B"/><rect width="1440" height="520" fill="url(#p-krata-j)"/>';
    s += use('ramen', 70, 440, 230, 20);
    s += use('tacos', 40, 50, 190, -15);
    s += use('nalesniki', 870, 28, 200, 40);
    s += use('sushi', 835, 492, 230, -12);
    s += drink(905, 262, 86, '#F29F3D', 20);
    s += use('pizza', 1130, 262, 430, 12);
    s += use('salatka', 1392, 70, 210, 30);
    s += use('burger', 1400, 452, 240, 8);
    return s + '</svg>';
  }

  /* Mapa dostawy: uproszczone miasto, trasa od lokalu do domu. */
  var ROUTE = 'M150 160H330V70H560V250H650';
  function map() {
    var xs = [-20, 90, 210, 330, 430, 560, 680, 820], ys = [-20, 70, 160, 250, 330, 400];
    var r = rng(77), s = '', i, j;
    s += '<svg class="art map" viewBox="0 0 800 380" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">';
    s += '<rect width="800" height="380" fill="#FBFAF8"/>';
    for (i = 0; i < xs.length - 1; i++) {
      for (j = 0; j < ys.length - 1; j++) {
        var x = xs[i] + 8, y = ys[j] + 8, w = xs[i + 1] - xs[i] - 16, h = ys[j + 1] - ys[j] - 16;
        var park = (i === 4 && j === 1) || (i === 1 && j === 2);
        s += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="8" fill="' + (park ? '#D5E9C9' : '#EAE5E0') + '"/>';
        if (park) {
          for (var t = 0; t < 7; t++) s += '<circle cx="' + f(x + 12 + r() * (w - 24)) + '" cy="' + f(y + 12 + r() * (h - 24)) + '" r="' + f(5 + r() * 4) + '" fill="#B4D6A4"/>';
        } else {
          var n = 1 + Math.floor(r() * 3);
          for (var b = 0; b < n; b++) {
            var bw = 22 + r() * (w / n - 34), bh = 18 + r() * (h - 44);
            s += '<rect x="' + f(x + 8 + b * (w / n)) + '" y="' + f(y + 8 + r() * (h - bh - 16)) + '" width="' + f(Math.max(14, bw)) + '" height="' + f(Math.max(12, bh)) + '" rx="3" fill="#DDD6CF"/>';
          }
        }
      }
    }
    s += '<path d="M-20 322C140 284 260 352 420 308S660 300 820 338" fill="none" stroke="#C3DCF0" stroke-width="36" stroke-linecap="round"/>';
    s += '<path d="M-20 322C140 284 260 352 420 308S660 300 820 338" fill="none" stroke="#D5E8F6" stroke-width="12" stroke-linecap="round" stroke-dasharray="40 30"/>';
    s += '<g stroke="#FBFAF8" stroke-width="16">';
    for (i = 1; i < xs.length - 1; i++) s += '<path d="M' + xs[i] + ' 262V380"/>';
    s += '</g>';
    s += '<path d="' + ROUTE + '" fill="none" stroke="#24152B" stroke-opacity=".22" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1 10"/>';
    s += '<path class="map__done" d="' + ROUTE + '" fill="none" stroke="#E0312B" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="770" stroke-dashoffset="770"/>';
    s += '<g transform="translate(150 160)"><circle r="19" fill="#24152B"/><path d="M-8.5-2.5l1.5-5h14l1.5 5M-7.5-2.5v9.5h15v-9.5M-8.5-2.5a2.83 2.83 0 0 0 5.66 0 2.83 2.83 0 0 0 5.67 0 2.83 2.83 0 0 0 5.67 0" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></g>';
    s += '<g transform="translate(650 250)"><circle class="map__home-pulse" r="19" fill="#E0312B" opacity=".25"/><circle r="19" fill="#E0312B"/><path d="M-8.5-.5L0-8l8.5 7.5M-6-2v9.5H6V-2" fill="none" stroke="#fff" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></g>';
    s += '<g class="map__courier" transform="translate(150 160)"><circle r="17" fill="#fff" stroke="#E0312B" stroke-width="3.5"/><g fill="none" stroke="#24152B" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="-5.6" cy="3.6" r="3.4"/><circle cx="5.6" cy="3.6" r="3.4"/><path d="M-5.6 3.6l3.6-6.6h4.6l3 6.6M-2-3L-3.4-6h-2M2.6-3L-.6 3.6"/></g></g>';
    return s + '</svg>';
  }

  /* Znak marki: talerz z ugryzionym brzegiem. */
  function logo(size) {
    size = size || 28;
    return '<svg class="logo__mark" viewBox="0 0 32 32" width="' + size + '" height="' + size + '" aria-hidden="true" focusable="false"><g mask="url(#m-ugryz)"><circle cx="16" cy="16" r="15" fill="currentColor"/><circle cx="16" cy="16" r="8.6" fill="none" stroke="#fff" stroke-width="2.2"/></g></svg>';
  }

  SZ.art = {
    DISHES: DISHES, DISH_NAMES: DISH_NAMES, sprite: sprite, cover: cover, banner: banner, dish: dish, hero: hero, map: map, logo: logo,
    hash: hash, rng: rng, lum: lum, safeColor: safeColor, dishKey: dishKey
  };
})();
