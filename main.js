/* Sakura Studio — płynne przewijanie (Lenis) i animacje sterowane scrollem (GSAP + ScrollTrigger) */
(function () {
  "use strict";

  var root = document.documentElement;
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* Baner w pętli: druga kopia obrazków, żeby przesuw nie miał szwu. */
  if (!reduce) {
    $$(".marquee-row").forEach(function (row) {
      $$("img", row).forEach(function (img) { row.appendChild(img.cloneNode(true)); });
    });
  }

  /* Blask pod kursorem na kartach cennika. */
  $$(".plan").forEach(function (p) {
    p.addEventListener("pointermove", function (e) {
      var r = p.getBoundingClientRect();
      p.style.setProperty("--mx", (e.clientX - r.left) + "px");
      p.style.setProperty("--my", (e.clientY - r.top) + "px");
    });
  });

  /* Dzieli tekst na słowa (<span class="w">), zostawiając znaczniki takie jak <em>. */
  function splitWords(el) {
    (function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 3) {
          var frag = document.createDocumentFragment();
          n.textContent.split(/([ \t\n\r]+)/).forEach(function (part) {
            if (!part) return;
            if (/^[ \t\n\r]+$/.test(part)) { frag.appendChild(document.createTextNode(" ")); return; }
            var s = document.createElement("span");
            s.className = "w";
            s.textContent = part;
            frag.appendChild(s);
          });
          n.parentNode.replaceChild(frag, n);
        } else if (n.nodeType === 1 && !n.classList.contains("w")) {
          walk(n);
        }
      });
    })(el);
    return $$(".w", el);
  }

  /* Gradient ciągnie się przez całą linię, a nie zaczyna od nowa w każdym słowie. */
  function fitGradients() {
    $$(".gradw").forEach(function (line) {
      var width = line.getBoundingClientRect().width;
      $$(".w", line).forEach(function (w) {
        w.style.setProperty("--gw", width + "px");
        w.style.setProperty("--gx", (line.offsetLeft - w.offsetLeft) + "px");
      });
    });
  }

  function staticMode() {
    root.classList.remove("anim");
    window.__animReady = true;
  }

  function start() {
    var G = window.gsap, ST = window.ScrollTrigger;
    if (reduce || !G || !ST || !root.classList.contains("anim")) { staticMode(); return; }
    window.__animReady = true;
    G.registerPlugin(ST);

    /* ---------- płynne przewijanie ---------- */
    var lenis = null;
    if (window.Lenis) {
      lenis = new window.Lenis({ lerp: 0.085, smoothWheel: true, wheelMultiplier: 1 });
      lenis.on("scroll", ST.update);
      G.ticker.add(function (t) { lenis.raf(t * 1000); });
      G.ticker.lagSmoothing(0);
    }
    $$('a[href^="#"]').forEach(function (a) {
      a.addEventListener("click", function (e) {
        var id = a.getAttribute("href");
        var target = id.length > 1 && $(id);
        if (!target) return;
        e.preventDefault();
        if (lenis) lenis.scrollTo(target, { offset: id === "#start" ? 0 : -52, duration: 1.6, easing: function (t) { return 1 - Math.pow(1 - t, 4); } });
        else target.scrollIntoView({ behavior: "smooth" });
        history.replaceState(null, "", id);
      });
    });

    /* ---------- hero: wejście ---------- */
    $$(".hero-title .grad").forEach(function (l) { l.classList.remove("grad"); l.classList.add("gradw"); });
    var heroWords = splitWords($(".hero-title"));
    fitGradients();
    G.set(".hero-title", { opacity: 1 });

    var intro = G.timeline({ defaults: { ease: "expo.out" } });
    intro
      .fromTo(".hero-glow", { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 2.8, ease: "power2.out" }, 0)
      .fromTo(".hero-word", { opacity: 0, scale: 1.08 }, { opacity: 1, scale: 1, duration: 2.8, ease: "power2.out" }, 0)
      .fromTo(".nav", { opacity: 0, y: -14 }, { opacity: 1, y: 0, duration: 1.4 }, 0.25)
      .fromTo(".hero-logo", { opacity: 0, scale: 0.6, rotate: -14, filter: "blur(16px)" }, { opacity: 1, scale: 1, rotate: 0, filter: "blur(0px)", duration: 2.1 }, 0.15)
      .fromTo(".hero-eyebrow", { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 1.4 }, 0.5)
      .fromTo(heroWords, { opacity: 0, yPercent: 55, filter: "blur(12px)" }, { opacity: 1, yPercent: 0, filter: "blur(0px)", duration: 1.7, stagger: 0.075 }, 0.6)
      .fromTo(".hero-sub", { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: 1.6 }, 1.05)
      .fromTo(".hero-cta > *", { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 1.5, stagger: 0.1 }, 1.2)
      .add(function () { G.set(heroWords, { clearProps: "filter,willChange" }); });
    G.to(".hero-logo img", { y: -12, duration: 3.2, ease: "sine.inOut", yoyo: true, repeat: -1, delay: 2.2 });

    /* ---------- hero: odjazd przy przewijaniu ---------- */
    G.timeline({ scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: true } })
      .to(".hero-inner", { scale: 0.86, yPercent: -10, opacity: 0, ease: "none" }, 0)
      .to(".hero-word span", { xPercent: -14, ease: "none" }, 0)
      .to(".hero-glow", { yPercent: -30, opacity: 0.55, ease: "none" }, 0)
      .to(".scroll-hint", { opacity: 0, ease: "none", duration: 0.15 }, 0);

    /* ---------- zdanie, które zapala się słowo po słowie ---------- */
    var stWords = splitWords($(".statement-text"));
    G.to(stWords, {
      opacity: 1, ease: "none", stagger: 0.08,
      scrollTrigger: { trigger: ".statement", start: "top 78%", end: "bottom 62%", scrub: 0.8 }
    });

    /* ---------- elementy wjeżdżające od dołu ---------- */
    ST.batch("[data-reveal]", {
      start: "top 88%", once: true,
      onEnter: function (els) { G.to(els, { opacity: 1, y: 0, duration: 1.5, ease: "expo.out", stagger: 0.09, overwrite: true }); }
    });

    /* ---------- funkcje: przyklejony ekran i zmieniające się wiadomości ---------- */
    var stack = $(".device-stack");
    var steps = $$(".step");
    steps.forEach(function (s) {
      var card = s.querySelector("[data-card]").cloneNode(true);
      card.removeAttribute("data-card");
      $$("img", card).forEach(function (i) { i.removeAttribute("loading"); });
      stack.appendChild(card);
    });
    root.classList.add("has-device");
    var cards = $$(".dc", stack);
    var current = -1;
    function setActive(i) {
      if (i === current) return;
      cards.forEach(function (c, k) { c.classList.toggle("on", k === i); c.classList.toggle("out", k < i); });
      steps.forEach(function (s, k) { s.classList.toggle("active", k === i); });
      current = i;
    }
    setActive(0);
    steps.forEach(function (s, i) {
      ST.create({ trigger: s, start: "top 55%", end: "bottom 55%", onToggle: function (self) { if (self.isActive) setActive(i); } });
    });
    G.fromTo(".device", { scale: 0.9, opacity: 0, y: 80 }, {
      scale: 1, opacity: 1, y: 0, ease: "none",
      scrollTrigger: { trigger: ".features-grid", start: "top 92%", end: "top 38%", scrub: true }
    });

    /* ---------- liczby ---------- */
    $$("[data-count]").forEach(function (el) {
      var end = +el.getAttribute("data-count"), o = { v: 0 };
      el.textContent = "0";
      ST.create({
        trigger: el, start: "top 90%", once: true,
        onEnter: function () { G.to(o, { v: end, duration: 1.8, ease: "power3.out", onUpdate: function () { el.textContent = Math.round(o.v); } }); }
      });
    });

    /* ---------- realizacje: przewijanie w bok (od 901 px) ---------- */
    var mm = G.matchMedia();
    mm.add("(min-width: 901px)", function () {
      var track = $(".works-track");
      var bar = $(".works-progress span");
      var distance = function () { return Math.max(0, track.scrollWidth - window.innerWidth); };
      var slide = G.to(track, {
        x: function () { return -distance(); }, ease: "none",
        scrollTrigger: {
          trigger: ".works-pin", start: "top top", end: function () { return "+=" + distance(); },
          pin: true, scrub: 1, invalidateOnRefresh: true, anticipatePin: 1,
          onUpdate: function (self) { bar.style.setProperty("--p", self.progress.toFixed(4)); }
        }
      });
      $$(".work", track).forEach(function (w) {
        G.fromTo(w, { opacity: 0.35, scale: 0.92 }, {
          opacity: 1, scale: 1, ease: "none",
          scrollTrigger: { trigger: w, containerAnimation: slide, start: "left 100%", end: "left 62%", scrub: true }
        });
      });
    });
    mm.add("(max-width: 900px)", function () {
      root.classList.add("no-pin");
      return function () { root.classList.remove("no-pin"); };
    });

    /* ---------- jak to działa: linia postępu ---------- */
    var procItems = $$(".process-steps li");
    G.fromTo(".process-line span", { scaleX: 0 }, {
      scaleX: 1, ease: "none",
      scrollTrigger: {
        trigger: ".process", start: "top 72%", end: "bottom 72%", scrub: 0.6,
        onUpdate: function (self) {
          var lit = Math.floor(self.progress * procItems.length + 0.2);
          procItems.forEach(function (li, i) { li.classList.toggle("lit", i < lit); });
        }
      }
    });

    /* ---------- kontakt ---------- */
    G.fromTo(".cta-title", { scale: 0.82, opacity: 0.15 }, {
      scale: 1, opacity: 1, ease: "none",
      scrollTrigger: { trigger: ".cta", start: "top 88%", end: "center 62%", scrub: true }
    });
    G.fromTo(".cta-glow", { opacity: 0, scale: 0.6 }, {
      opacity: 1, scale: 1, ease: "none",
      scrollTrigger: { trigger: ".cta", start: "top 92%", end: "center 55%", scrub: true }
    });

    /* ---------- przeliczenie po czcionkach, obrazkach i zmianie rozmiaru ---------- */
    var refresh = function () { fitGradients(); ST.refresh(); };
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(refresh);
    window.addEventListener("load", refresh);
    var t;
    window.addEventListener("resize", function () { clearTimeout(t); t = setTimeout(fitGradients, 150); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
