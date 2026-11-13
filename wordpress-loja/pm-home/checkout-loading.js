/**
 * Overlay leve de processamento no /finalizar-pagamento/.
 * Não altera CF7/Accesstage; só UI. Estados reais via eventos wpcf7*.
 */
(function () {
  "use strict";

  var ROOT_ID = "pm-ck-loading";
  var HOLDING_MS = 5200;
  var GSAP_URL = "https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js";
  var state = "idle";
  var root = null;
  var holdingTimer = null;
  var reduced = false;
  var gsapOk = typeof window.gsap !== "undefined";
  var gsapPromise = null;

  function ensureGsap(done) {
    if (typeof window.gsap !== "undefined") {
      gsapOk = true;
      if (done) done();
      return;
    }
    if (!gsapPromise) {
      gsapPromise = new Promise(function (resolve) {
        var s = document.createElement("script");
        s.src = GSAP_URL;
        s.async = true;
        s.onload = function () {
          resolve(true);
        };
        s.onerror = function () {
          resolve(false);
        };
        (document.head || document.documentElement).appendChild(s);
      });
    }
    gsapPromise.then(function () {
      gsapOk = typeof window.gsap !== "undefined";
      if (done) done();
    });
  }

  var COPY = {
    received: "Recebemos os dados do seu pedido",
    preparing: "Preparando os itens",
    paying: "Processando o pagamento",
    holding: "Aguardando confirmação…",
    confirmed: "Pedido confirmado",
  };

  var STEPS = ["received", "preparing", "paying", "confirmed"];

  function prefersReduced() {
    try {
      return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    } catch (e) {
      return false;
    }
  }

  function decodeEntities(s) {
    var t = document.createElement("textarea");
    t.innerHTML = String(s || "");
    return t.value;
  }

  function lineName(line) {
    if (!line) return "Item";
    var n = decodeEntities(line.name || "")
      .replace(/<[^>]+>/g, "")
      .trim();
    return n || "Item";
  }

  function lineQty(line) {
    var q = line && line.quantity != null ? Number(line.quantity) : 1;
    return isFinite(q) && q > 0 ? q : 1;
  }

  function linePriceLabel(line) {
    var cents =
      line && line.totals && line.totals.line_total != null
        ? Number(line.totals.line_total)
        : NaN;
    if (!isFinite(cents)) return "";
    return (
      "R$\u00a0" +
      (cents / 100).toFixed(2).replace(".", ",")
    );
  }

  function buildCardsHtml(items) {
    var list = (items || []).slice(0, 3);
    if (!list.length) {
      return (
        '<div class="pm-ck-loading__card" data-pm-card="0">' +
        '<span class="pm-ck-loading__card-name">Seu pedido</span>' +
        '<span class="pm-ck-loading__card-qty">1 item</span></div>'
      );
    }
    return list
      .map(function (line, i) {
        var price = linePriceLabel(line);
        return (
          '<div class="pm-ck-loading__card" data-pm-card="' +
          i +
          '">' +
          '<span class="pm-ck-loading__card-dot" aria-hidden="true"></span>' +
          '<span class="pm-ck-loading__card-name">' +
          escapeHtml(lineName(line)) +
          (price ? " · " + escapeHtml(price) : "") +
          "</span>" +
          '<span class="pm-ck-loading__card-qty">×' +
          lineQty(line) +
          "</span></div>"
        );
      })
      .join("");
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function ensureDom(items) {
    if (root && document.body.contains(root)) {
      var wrap = root.querySelector(".pm-ck-loading__cards");
      if (wrap) wrap.innerHTML = buildCardsHtml(items);
      return root;
    }
    var el = document.createElement("div");
    el.id = ROOT_ID;
    el.className = "pm-ck-loading";
    el.setAttribute("role", "alertdialog");
    el.setAttribute("aria-modal", "true");
    el.setAttribute("aria-busy", "true");
    el.setAttribute("aria-live", "polite");
    el.innerHTML =
      '<div class="pm-ck-loading__veil" aria-hidden="true"></div>' +
      '<div class="pm-ck-loading__panel">' +
      '<div class="pm-ck-loading__cart-wrap" aria-hidden="true">' +
      '<span class="pm-ck-loading__spinner"></span>' +
      '<span class="pm-ck-loading__cart">' +
      '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
      '<rect x="2" y="5" width="20" height="14" rx="2.5"/>' +
      '<path d="M2 10h20"/><path d="M6 15h4"/>' +
      "</svg></span></div>" +
      '<p class="pm-ck-loading__status" id="pm-ck-loading-status"></p>' +
      '<ol class="pm-ck-loading__steps" aria-hidden="true">' +
      '<li data-step="received"><span></span></li>' +
      '<li data-step="preparing"><span></span></li>' +
      '<li data-step="paying"><span></span></li>' +
      '<li data-step="confirmed"><span></span></li>' +
      "</ol>" +
      '<div class="pm-ck-loading__progress" aria-hidden="true"><i></i></div>' +
      '<div class="pm-ck-loading__cards">' +
      buildCardsHtml(items) +
      "</div>" +
      '<div class="pm-ck-loading__check" aria-hidden="true">' +
      '<svg viewBox="0 0 52 52" width="52" height="52">' +
      '<circle cx="26" cy="26" r="24" fill="none" stroke="currentColor" stroke-width="2"/>' +
      '<path class="pm-ck-loading__check-path" fill="none" stroke="currentColor" stroke-width="3" ' +
      'stroke-linecap="round" stroke-linejoin="round" d="M16 27l7 7 13-15"/>' +
      "</svg></div>" +
      "</div>";
    document.body.appendChild(el);
    root = el;
    return root;
  }

  function clearHolding() {
    if (holdingTimer) {
      window.clearTimeout(holdingTimer);
      holdingTimer = null;
    }
  }

  function paintSteps(active) {
    if (!root) return;
    var idx = STEPS.indexOf(active === "holding" ? "paying" : active);
    root.querySelectorAll(".pm-ck-loading__steps li").forEach(function (li, i) {
      li.classList.toggle("is-done", idx >= 0 && i < idx);
      li.classList.toggle("is-active", idx >= 0 && i === idx);
    });
    var bar = root.querySelector(".pm-ck-loading__progress > i");
    if (bar) {
      var pct = active === "confirmed" ? 100 : active === "holding" ? 78 : idx < 0 ? 8 : Math.min(92, (idx + 1) * 22);
      bar.style.width = pct + "%";
    }
  }

  function setCopy(key) {
    if (!root) return;
    var status = root.querySelector("#pm-ck-loading-status");
    if (status) status.textContent = COPY[key] || COPY.paying;
  }

  function animateIn() {
    if (!root) return;
    root.classList.add("is-open");
    document.documentElement.classList.add("pm-ck-loading-lock");
    if (!gsapOk || reduced) {
      root.style.opacity = "1";
      return;
    }
    var g = window.gsap;
    g.set(root, { opacity: 0 });
    g.set(root.querySelector(".pm-ck-loading__panel"), { y: 18, opacity: 0 });
    g.set(root.querySelectorAll(".pm-ck-loading__card"), { y: 16, opacity: 0 });
    g.to(root, { opacity: 1, duration: 0.22, ease: "power2.out" });
    g.to(root.querySelector(".pm-ck-loading__panel"), {
      y: 0,
      opacity: 1,
      duration: 0.35,
      ease: "power3.out",
    });
    g.to(root.querySelectorAll(".pm-ck-loading__card"), {
      y: 0,
      opacity: 1,
      duration: 0.32,
      stagger: 0.07,
      ease: "power2.out",
      delay: 0.08,
    });
  }

  function animateOut(done) {
    clearHolding();
    if (!root) {
      if (done) done();
      return;
    }
    if (gsapOk) {
      try {
        window.gsap.killTweensOf(root);
        window.gsap.killTweensOf(root.querySelectorAll(".pm-ck-loading__card"));
        window.gsap.killTweensOf(root.querySelector(".pm-ck-loading__panel"));
        window.gsap.killTweensOf(root.querySelector(".pm-ck-loading__check"));
        window.gsap.killTweensOf(root.querySelector(".pm-ck-loading__check-path"));
        window.gsap.killTweensOf(root.querySelector(".pm-ck-loading__cart-wrap"));
      } catch (e) {}
    }
    function finish() {
      if (root && root.parentNode) root.parentNode.removeChild(root);
      root = null;
      document.documentElement.classList.remove("pm-ck-loading-lock");
      state = "idle";
      if (done) done();
    }
    if (!gsapOk || reduced) {
      finish();
      return;
    }
    window.gsap.to(root, {
      opacity: 0,
      duration: 0.2,
      ease: "power1.in",
      onComplete: finish,
    });
  }

  function showCheck() {
    if (!root) return;
    root.classList.add("is-confirmed");
    if (!gsapOk || reduced) return;
    var path = root.querySelector(".pm-ck-loading__check-path");
    var g = window.gsap;
    g.fromTo(
      root.querySelector(".pm-ck-loading__check"),
      { scale: 0.7, opacity: 0 },
      { scale: 1, opacity: 1, duration: 0.28, ease: "back.out(1.6)" }
    );
    if (path) {
      var len = 40;
      try {
        len = path.getTotalLength();
      } catch (e) {}
      g.set(path, { strokeDasharray: len, strokeDashoffset: len });
      g.to(path, { strokeDashoffset: 0, duration: 0.35, ease: "power2.out" });
    }
  }

  function open(opts) {
    opts = opts || {};
    reduced = prefersReduced();
    clearHolding();
    ensureDom(opts.items || []);
    state = "received";
    root.classList.remove("is-confirmed");
    setCopy("received");
    paintSteps("received");
    // GSAP sob demanda: DOM já visível; animação quando o script chegar.
    ensureGsap(function () {
      if (state === "idle") return;
      animateIn();
    });
    holdingTimer = window.setTimeout(function () {
      if (state === "paying" || state === "preparing" || state === "received") {
        setState("holding");
      }
    }, HOLDING_MS);
    return true;
  }

  function setState(next) {
    if (!root && next !== "idle") return;
    if (state === "confirmed" && next !== "error" && next !== "idle") return;
    if (next === "error" || next === "idle") {
      animateOut();
      return;
    }
    if (next === "holding" && (state === "confirmed" || state === "error")) return;
    state = next;
    setCopy(next === "holding" ? "holding" : next);
    paintSteps(next);
    // Holding: só barra + copy (sem yoyo/pulse nos cards).
    if (next === "confirmed") {
      clearHolding();
      showCheck();
    }
  }

  function close() {
    animateOut();
  }

  function isActive() {
    return state !== "idle" && !!root;
  }

  function getState() {
    return state;
  }

  window.pmCheckoutLoading = {
    open: open,
    setState: setState,
    close: close,
    isActive: isActive,
    getState: getState,
  };
})();
