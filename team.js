/* Sakura Studio — Ekipa: portfolio zespołu, kody jednorazowe, panel admina. */
(function () {
  "use strict";

  var API_ORIGIN = "https://vps-e6c53239.vps.ovh.net";
  var API = API_ORIGIN + "/api";
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---------- tokeny w tej przeglądarce ---------- */
  var store = {
    admin: function () { try { return localStorage.getItem("sakura_admin"); } catch (e) { return null; } },
    setAdmin: function (t) { try { localStorage.setItem("sakura_admin", t); } catch (e) {} },
    editToken: function (id) { try { return JSON.parse(localStorage.getItem("sakura_edits") || "{}")[id] || null; } catch (e) { return null; } },
    setEditToken: function (id, t) {
      try {
        var m = JSON.parse(localStorage.getItem("sakura_edits") || "{}");
        m[id] = t;
        localStorage.setItem("sakura_edits", JSON.stringify(m));
      } catch (e) {}
    },
  };

  function authHeader(portfolioId) {
    var admin = store.admin();
    if (admin) return "Bearer " + admin;
    var t = portfolioId && store.editToken(portfolioId);
    return t ? "Bearer " + t : null;
  }

  function api(path, opts) {
    opts = opts || {};
    var headers = opts.headers || {};
    if (opts.auth) {
      var h = authHeader(opts.authId);
      if (h) headers["Authorization"] = h;
    }
    if (opts.json) { headers["Content-Type"] = "application/json; charset=utf-8"; opts.body = JSON.stringify(opts.json); }
    return fetch(API + path, { method: opts.method || "GET", headers: headers, body: opts.body })
      .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, status: r.status, data: data }; }); });
  }

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }

  /* ---------- okna modalne ---------- */
  function openModal(el) {
    el.hidden = false;
    requestAnimationFrame(function () { requestAnimationFrame(function () { el.classList.add("open"); }); });
    document.documentElement.style.overflow = "hidden";
  }
  function closeModal(el) {
    el.classList.remove("open");
    document.documentElement.style.overflow = "";
    setTimeout(function () { el.hidden = true; }, 450);
  }
  $$(".modal").forEach(function (m) {
    $$("[data-close]", m).forEach(function (b) { b.addEventListener("click", function () { closeModal(m); }); });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    $$(".modal.open").forEach(closeModal);
  });

  var logoBtn = $("#logo-btn");
  var codeModal = $("#code-modal");
  var personModal = $("#person-modal");
  if (logoBtn) logoBtn.addEventListener("click", function () { renderCodeForm(); openModal(codeModal); });

  /* ---------- render siatki ekipy ---------- */
  var grid = $("#team-grid");
  var cache = {};

  function renderMiniDiscord(d) {
    if (!d) return "";
    return (
      '<span class="tc-media-count">' +
      (d.clanBadge ? '<img src="' + d.clanBadge + '" alt="" style="width:14px;height:14px;border-radius:3px">' : "") +
      "Discord: " + esc(d.globalName || d.username) + "</span>"
    );
  }

  function cardHtml(p) {
    if (p.status !== "claimed" || !p.hasName) {
      return (
        '<article class="team-card wolne" data-id="' + p.id + '" tabindex="0" role="button" aria-label="Wolne miejsce w ekipie">' +
        '<span class="tc-wolne-label">Wolne</span>' +
        '<span class="tc-wolne-sub">To miejsce czeka na kolejną osobę z ekipy.</span>' +
        "</article>"
      );
    }
    var d = p.discord;
    var avatar = (d && d.avatar) || "assets/logo-s.png";
    return (
      '<article class="team-card" data-id="' + p.id + '" tabindex="0" role="button" aria-label="' + esc(p.name) + '">' +
      '<div class="tc-banner">' + (d && d.banner ? '<img src="' + d.banner + '" alt="" loading="lazy">' : "") + "</div>" +
      '<div class="tc-av"><img src="' + avatar + '" alt="" loading="lazy">' +
      (d && d.decoration ? '<img class="tc-deco" src="' + d.decoration + '" alt="">' : "") +
      "</div>" +
      '<div class="tc-body">' +
      '<p class="tc-name">' + esc(p.name) + "</p>" +
      (p.role ? '<p class="tc-role">' + esc(p.role) + "</p>" : "") +
      (p.bioPreview ? '<p class="tc-bio">' + esc(p.bioPreview) + "</p>" : "") +
      (p.mediaCount ? '<span class="tc-media-count">' + p.mediaCount + (p.mediaCount === 1 ? " plik w portfolio" : " pliki w portfolio") + "</span>" : "") +
      "</div></article>"
    );
  }

  function loadGrid() {
    api("/portfolios").then(function (res) {
      if (!res.ok) { grid.innerHTML = '<p class="tc-wolne-sub">Nie udało się wczytać ekipy. Odśwież stronę.</p>'; return; }
      cache = {}; res.data.forEach(function (p) { cache[p.id] = p; });
      if (!res.data.length) {
        grid.innerHTML = '<p class="tc-wolne-sub">Ekipa jeszcze się buduje — pierwsze miejsca pojawią się tu wkrótce.</p>';
        return;
      }
      grid.innerHTML = res.data.map(cardHtml).join("");
      $$(".team-card", grid).forEach(function (card, i) {
        card.style.opacity = "0";
        card.style.translate = "0 18px";
        card.style.transition = "opacity .6s cubic-bezier(.22,1,.36,1) " + i * 0.05 + "s, translate .6s cubic-bezier(.22,1,.36,1) " + i * 0.05 + "s";
        requestAnimationFrame(function () { requestAnimationFrame(function () { card.style.opacity = "1"; card.style.translate = "0 0"; }); });
        card.addEventListener("click", function () { openPerson(card.dataset.id); });
        card.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openPerson(card.dataset.id); } });
      });
    });
  }

  /* ---------- panel osoby: widok / edycja ---------- */
  function mediaUrl(u) { return u && u.indexOf("http") === 0 ? u : API_ORIGIN + u; }

  function mediaItemHtml(m, owner) {
    var url = mediaUrl(m.url);
    var body = m.kind === "video"
      ? '<video src="' + url + '" muted loop playsinline preload="metadata"></video>'
      : '<img src="' + url + '" alt="" loading="lazy">';
    return (
      '<div class="pp-media-item' + (owner ? " owner" : "") + '" data-media-id="' + m.id + '">' + body +
      (m.caption ? '<span class="cap">' + esc(m.caption) + "</span>" : "") +
      (owner ? '<button type="button" class="pp-media-del" data-del-media="' + m.id + '" aria-label="Usuń">×</button>' : "") +
      "</div>"
    );
  }

  function discordCardHtml(d) {
    if (!d) return "";
    var grad = d.nameGradient ? "linear-gradient(100deg," + d.nameGradient[0] + "," + d.nameGradient[1] + ")" : "linear-gradient(100deg,#d0996a,#97613a)";
    return (
      '<div class="pp-clan">' + (d.clanBadge ? '<img src="' + d.clanBadge + '" alt="">' : "") + esc(d.clanTag || "Discord") + "</div>"
    );
  }

  function viewHtml(p, opts) {
    var owner = opts && opts.owner;
    var d = p.discord;
    var name = p.hasName ? esc(p.name) : "Wolne";
    var html = "";
    html += '<div class="pp-banner">' + (d && d.banner ? '<img src="' + d.banner + '" alt="">' : "") + "</div>";
    html += '<div class="pp-body">';
    html += '<div class="pp-av-wrap"><img class="pp-av" src="' + ((d && d.avatar) || "assets/logo-s.png") + '" alt="">' + (d && d.decoration ? '<img class="pp-deco" src="' + d.decoration + '" alt="">' : "") + "</div>";
    if (d) html += discordCardHtml(d);
    if (owner) html += '<span class="pp-edit-badge">✏️ Edytujesz swoje portfolio</span>';
    if (owner) {
      html += '<div id="pp-form">';
      html += '<div class="pp-field"><label for="f-name">Imię / pseudonim</label><input id="f-name" maxlength="40" value="' + esc(p.hasName ? p.name : "") + '" placeholder="Jak Cię pokazać w ekipie"></div>';
      html += '<div class="pp-field"><label for="f-role">Rola</label><input id="f-role" maxlength="60" value="' + esc(p.role || "") + '" placeholder="np. Grafik, Montażysta, Voice Actor"></div>';
      html += '<div class="pp-field"><label for="f-discord">ID Discorda</label><input id="f-discord" maxlength="20" value="' + esc(p.discordId || "") + '" placeholder="np. 527827004578594816"><small>Kliknij prawym na siebie na Discordzie → Kopiuj ID użytkownika (tryb dewelopera musi być włączony).</small></div>';
      html += '<div class="pp-field"><label for="f-bio">O mnie</label><textarea id="f-bio" rows="4" maxlength="1200" placeholder="Kilka słów o Tobie i tym, co robisz w Sakura Studio.">' + esc(p.bio || "") + "</textarea></div>";
      html += '<div class="pp-save-row"><button type="button" class="btn btn-primary" id="pp-save">Zapisz</button><span class="pp-save-msg" id="pp-save-msg" hidden></span></div>';
      html += "</div>";
    } else {
      html += '<p class="pp-name">' + name + "</p>";
      if (p.role) html += '<p class="pp-role">' + esc(p.role) + "</p>";
      html += p.bio ? '<p class="pp-bio">' + esc(p.bio) + "</p>" : '<p class="pp-bio pp-empty">To miejsce czeka jeszcze na opis.</p>';
    }
    var media = p.media || [];
    if (media.length || owner) {
      html += '<div class="pp-media">' + media.map(function (m) { return mediaItemHtml(m, owner); }).join("") + "</div>";
    }
    if (owner) {
      html += '<div class="pp-upload"><label for="pp-file">📎 Dodaj zdjęcie albo film<input type="file" id="pp-file" accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm,video/quicktime"></label><span class="hint">Do 50&nbsp;MB, maks. 12 plików w portfolio.</span></div>';
    }
    html += "</div>";
    return html;
  }

  function wireOwnerForm(id) {
    var save = $("#pp-save");
    if (save) save.addEventListener("click", function () {
      save.disabled = true;
      api("/portfolios/" + id, {
        method: "PATCH", auth: true, authId: id, json: {
          name: $("#f-name").value, role: $("#f-role").value, bio: $("#f-bio").value, discordId: $("#f-discord").value,
        },
      }).then(function (res) {
        save.disabled = false;
        var msg = $("#pp-save-msg");
        if (!res.ok) { msg.hidden = false; msg.textContent = res.data.error || "Nie udało się zapisać."; msg.style.color = "#ff8e8e"; return; }
        msg.hidden = false; msg.textContent = "Zapisano ✓"; msg.style.color = "";
        cache[id] = Object.assign({}, cache[id], res.data);
        setTimeout(function () { openPerson(id, true); }, 450);
        loadGrid();
      });
    });

    var fileInput = $("#pp-file");
    if (fileInput) fileInput.addEventListener("change", function () {
      var file = fileInput.files[0];
      if (!file) return;
      var fd = new FormData();
      fd.append("file", file);
      var headers = {}; var h = authHeader(id); if (h) headers["Authorization"] = h;
      fetch(API + "/portfolios/" + id + "/media", { method: "POST", headers: headers, body: fd })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
        .then(function (res) {
          if (!res.ok) { alert(res.data.error || "Nie udało się wgrać pliku."); return; }
          openPerson(id, true);
          loadGrid();
        });
    });

    $$("[data-del-media]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var mediaId = btn.getAttribute("data-del-media");
        api("/portfolios/" + id + "/media/" + mediaId, { method: "DELETE", auth: true, authId: id }).then(function () {
          openPerson(id, true);
          loadGrid();
        });
      });
    });
  }

  function openPerson(id, skipCache) {
    var content = $("#person-content");
    content.innerHTML = '<div class="pp-body"><p class="pp-bio pp-empty">Wczytuję…</p></div>';
    openModal(personModal);
    var known = !skipCache && cache[id];
    var owner = !!authHeader(id) && (store.admin() || store.editToken(id));
    Promise.resolve(known && known.media ? known : null)
      .then(function (pre) { return pre || api("/portfolios/" + id).then(function (r) { return r.data; }); })
      .then(function (p) {
        content.innerHTML = viewHtml(p, { owner: owner });
        if (owner) wireOwnerForm(id);
      });
  }

  /* ---------- kod dostępu / panel admina ---------- */
  function renderCodeForm() {
    var content = $("#code-content");
    content.innerHTML =
      '<p class="eyebrow">Panel administracyjny</p>' +
      "<h3>Podaj tymczasowy kod</h3>" +
      '<p class="code-sub">Kod od Sakura Studio odblokowuje edycję Twojego miejsca w&nbsp;ekipie.</p>' +
      '<form id="code-form" autocomplete="off">' +
      '<input type="text" id="code-input" placeholder="XXXX-XXXX-XXXX-XXXX" autocapitalize="characters" spellcheck="false" required>' +
      '<button type="submit" class="btn btn-primary">Zaloguj się</button>' +
      "</form>" +
      '<p class="code-msg" id="code-msg" hidden></p>';
    $("#code-form").addEventListener("submit", function (e) {
      e.preventDefault();
      var input = $("#code-input");
      var msg = $("#code-msg");
      var code = input.value.trim();
      if (!code) return;
      api("/redeem", { method: "POST", json: { code: code } }).then(function (res) {
        if (!res.ok) {
          msg.hidden = false; msg.className = "code-msg err"; msg.textContent = res.data.error || "Coś poszło nie tak.";
          return;
        }
        if (res.data.kind === "admin") {
          store.setAdmin(res.data.token);
          renderAdminPanel();
          return;
        }
        store.setEditToken(res.data.portfolio.id, res.data.token);
        msg.hidden = false; msg.className = "code-msg ok"; msg.textContent = "Kod przyjęty — otwieram Twoje portfolio…";
        loadGrid();
        setTimeout(function () { closeModal(codeModal); openPerson(res.data.portfolio.id, true); }, 500);
      });
    });
  }

  function renderAdminPanel() {
    var content = $("#code-content");
    content.innerHTML =
      '<p class="eyebrow">Panel administracyjny</p>' +
      "<h3>Zalogowano</h3>" +
      '<div class="admin-block">' +
      "<h4>Nowa osoba w ekipie</h4>" +
      '<div class="admin-gen"><button type="button" class="btn btn-ghost" id="admin-gen-btn">Wygeneruj kod</button></div>' +
      '<div class="admin-code-out" id="admin-code-out"><span id="admin-code-val"></span><button type="button" class="btn-link" id="admin-code-copy">Kopiuj</button></div>' +
      "</div>" +
      '<div class="admin-block"><h4>Wszystkie miejsca</h4><div class="admin-list" id="admin-list"></div></div>';

    $("#admin-gen-btn").addEventListener("click", function () {
      api("/admin/codes", { method: "POST", auth: true }).then(function (res) {
        if (!res.ok) { alert(res.data.error || "Nie udało się wygenerować kodu."); return; }
        var out = $("#admin-code-out"); out.classList.add("show");
        $("#admin-code-val").textContent = res.data.code;
        loadAdminList();
        loadGrid();
      });
    });
    $("#admin-code-copy").addEventListener("click", function () {
      var v = $("#admin-code-val").textContent;
      navigator.clipboard && navigator.clipboard.writeText(v).catch(function () {});
      var btn = $("#admin-code-copy"); var old = btn.textContent; btn.textContent = "Skopiowano ✓";
      setTimeout(function () { btn.textContent = old; }, 1500);
    });

    loadAdminList();
  }

  function loadAdminList() {
    api("/admin/portfolios", { auth: true }).then(function (res) {
      var list = $("#admin-list");
      if (!list) return;
      if (!res.ok) { list.innerHTML = '<p class="tc-wolne-sub">Brak dostępu.</p>'; return; }
      list.innerHTML = res.data.map(function (p) {
        var label = p.hasName ? p.name : "Wolne";
        var tag = p.status === "claimed" ? (p.codeUsed ? "zajęte" : "zajęte, kod nieużyty") : (p.codeUsed === false ? "czeka na kod" : "wolne");
        return (
          '<div class="admin-row"><b>' + esc(label) + '</b><span class="tag">' + tag + '</span>' +
          '<button type="button" data-reset="' + p.id + '">Reset</button>' +
          '<button type="button" data-del="' + p.id + '">Usuń</button></div>'
        );
      }).join("");
      $$("[data-reset]", list).forEach(function (b) {
        b.addEventListener("click", function () {
          if (!confirm("Zresetować to miejsce do stanu „Wolne”? Usunie to opis i pliki tej osoby.")) return;
          api("/admin/portfolios/" + b.getAttribute("data-reset") + "/reset", { method: "POST", auth: true }).then(function () { loadAdminList(); loadGrid(); });
        });
      });
      $$("[data-del]", list).forEach(function (b) {
        b.addEventListener("click", function () {
          if (!confirm("Usunąć to miejsce z listy na stałe?")) return;
          api("/admin/portfolios/" + b.getAttribute("data-del"), { method: "DELETE", auth: true }).then(function () { loadAdminList(); loadGrid(); });
        });
      });
    });
  }

  loadGrid();
})();
