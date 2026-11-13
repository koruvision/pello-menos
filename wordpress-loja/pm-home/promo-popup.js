(function () {
  // Pop-up dividido (reunião 29/10): lado A cupom de primeira compra + copiar; lado B preços de Black.
  // Decisão 30/10: só na home (feminina e masculina), uma única vez por visita — abre aos 5 s e não volta
  // enquanto a aba estiver aberta (sessionStorage); fechou o site e voltou, aparece de novo na home.
  // Cliente logada com pedido vê só o lado Black.
  // Espelho de src/components/CouponPopup.tsx — manter textos e classes iguais.
  var COUPON = "PRIMEIRACOMPRA5";
  var PERCENT = 5;
  var FIRST_DELAY_MS = 5000;
  var SESSION_KEY = "pello-menos-popup-v3";

  function isHome() {
    var path = (location.pathname || "/").replace(/\/+$/, "") || "/";
    return path === "/" || path === "/masculino";
  }
  if (!isHome()) return;
  try {
    if (sessionStorage.getItem(SESSION_KEY) === "done") return;
  } catch (e) {}

  var audienceNode = document.querySelector("[data-audience]");
  var isMale =
    location.pathname.indexOf("/masculino") === 0 ||
    Boolean(audienceNode && audienceNode.getAttribute("data-audience") === "masculino");
  var blackHref = isMale ? "/masculino/servicos/" : "/servicos/";

  var hasPurchased = false;
  function accountCall(op) {
    var body = new URLSearchParams();
    body.set("action", "pm_account");
    body.set("op", op);
    return fetch("/wp-admin/admin-ajax.php", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    })
      .then(function (r) {
        return r.ok ? r.json() : null;
      })
      .catch(function () {
        return null;
      });
  }
  accountCall("me").then(function (me) {
    if (!me || !me.loggedIn) return;
    return accountCall("orders").then(function (data) {
      hasPurchased = Boolean(data && data.ok && data.orders && data.orders.length);
      window.pmHasPurchased = hasPurchased;
    });
  });

  var host = null;

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function markDone() {
    try {
      sessionStorage.setItem(SESSION_KEY, "done");
    } catch (e) {}
  }

  function close() {
    if (!host) return;
    var card = host.querySelector("[data-pm-promo-card]");
    var overlay = host.querySelector("[data-pm-promo-overlay]");
    if (window.gsap && card && overlay) {
      var node = host;
      window.gsap.to(card, { opacity: 0, y: 40, scale: 0.92, duration: 0.3, ease: "power3.in" });
      window.gsap.to(overlay, {
        opacity: 0,
        duration: 0.3,
        onComplete: function () {
          if (node.parentNode) node.parentNode.removeChild(node);
        },
      });
    } else if (host.parentNode) {
      host.parentNode.removeChild(host);
    }
    host = null;
  }

  // Ícones lucide (mesmos de src/components/Icon.tsx) em SVG inline.
  var ICON_PATHS = {
    gift: '<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M12 8v13"/><path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/><path d="M7.5 8a2.5 2.5 0 0 1 0-5A4.8 8 0 0 1 12 8a4.8 8 0 0 1 4.5-5 2.5 2.5 0 0 1 0 5"/>',
    badgePercent:
      '<path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"/><path d="m15 9-6 6"/><path d="M9 9h.01"/><path d="M15 15h.01"/>',
    ticket:
      '<path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/><path d="M13 5v2"/><path d="M13 17v2"/><path d="M13 11v2"/>',
    copy: '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    flame:
      '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    tag: '<path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r=".5" fill="currentColor"/>',
    sparkles:
      '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/><path d="M4 17v2"/><path d="M5 18H3"/>',
    arrowRight: '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
  };

  function icon(name, size, cls) {
    return (
      '<svg width="' +
      size +
      '" height="' +
      size +
      '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"' +
      (cls ? ' class="' + cls + '"' : "") +
      ">" +
      (ICON_PATHS[name] || "") +
      "</svg>"
    );
  }

  function sideA() {
    return (
      '<section class="pm-promo-side pm-promo-side--light flex flex-col justify-center px-7 py-10 text-center md:px-8 text-[#3a0a3c] md:min-h-[460px] md:py-14">' +
      '<span class="pm-promo-seal pm-promo-seal--light" aria-hidden="true">' +
      icon("gift", 26) +
      "</span>" +
      '<p class="font-label-md text-label-md tracking-[0.22em] text-primary uppercase">Primeira compra</p>' +
      '<h2 id="pm-promo-title" class="mt-2 inline-flex items-center justify-center gap-2 font-[family-name:var(--font-display)] text-3xl text-primary md:text-4xl">' +
      icon("badgePercent", 30, "shrink-0") +
      PERCENT +
      "% de desconto</h2>" +
      '<p class="mt-3 text-sm leading-relaxed text-[#3a0a3c]/80">No total do seu primeiro pedido no site. Um uso por cliente; não acumula com outros cupons.</p>' +
      '<button type="button" data-pm-copy-coupon class="mt-6 inline-flex w-full items-center justify-between gap-3 rounded-2xl border border-primary/30 bg-white/90 px-4 py-3 text-primary shadow-[0_8px_20px_rgba(179,25,111,0.10)]">' +
      '<span class="inline-flex items-center gap-2 font-mono text-base tracking-[0.22em]">' +
      icon("ticket", 18, "shrink-0 text-[#e8b86d]") +
      esc(COUPON) +
      "</span>" +
      '<span class="inline-flex items-center gap-1 text-[11px] tracking-wide text-[#3a0a3c]/60 uppercase">' +
      '<span data-pm-copy-icon>' +
      icon("copy", 14) +
      "</span>" +
      '<span data-pm-copy-label>Copiar</span></span></button>' +
      '<p class="mt-3 text-[11px] text-[#3a0a3c]/60">Cole o código no carrinho.</p>' +
      "</section>"
    );
  }

  function sideB(onlyBlack) {
    return (
      '<section class="pm-promo-side pm-promo-side--dark flex flex-col justify-center px-7 py-10 text-center md:px-8 text-white md:min-h-[460px] md:py-14">' +
      '<span class="pm-promo-seal pm-promo-seal--dark" aria-hidden="true">' +
      icon("flame", 26) +
      "</span>" +
      '<p class="font-label-md text-label-md tracking-[0.22em] text-[#e8b86d] uppercase">Black Friday</p>' +
      "<h2" +
      (onlyBlack ? ' id="pm-promo-title"' : "") +
      ' class="mt-2 inline-flex items-center justify-center gap-2 font-[family-name:var(--font-display)] text-3xl text-white md:text-4xl">' +
      icon("tag", 28, "shrink-0 text-[#e8b86d]") +
      "Preços de Black</h2>" +
      '<p class="mt-3 text-sm leading-relaxed text-white/75">Cera, laser e esfoliação com preço especial de Black Friday aqui no site. Escolha a unidade e garanta o seu.</p>' +
      '<a href="' +
      esc(blackHref) +
      '" data-pm-promo-cta class="btn-lux btn-lux-gold mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full py-3.5 text-sm font-semibold tracking-wide text-on-secondary-container uppercase">' +
      icon("sparkles", 16) +
      "Ver ofertas" +
      icon("arrowRight", 16) +
      "</a>" +
      "</section>"
    );
  }

  function show() {
    if (host) return;
    if (document.hidden) {
      // Aba em segundo plano: espera voltar para mostrar (ainda conta como a única exibição da visita).
      document.addEventListener("visibilitychange", function onVisible() {
        if (document.hidden) return;
        document.removeEventListener("visibilitychange", onVisible);
        window.setTimeout(show, 800);
      });
      return;
    }
    markDone();
    var onlyBlack = hasPurchased;
    host = document.createElement("div");
    host.setAttribute("data-pm-promo-popup", "");
    host.className = "fixed inset-0 z-[90] flex items-center justify-center p-4";
    host.innerHTML =
      '<button type="button" data-pm-promo-overlay aria-label="Fechar" class="absolute inset-0 bg-[#2a1a24]/70 backdrop-blur-[6px]"></button>' +
      '<div data-pm-promo-card role="dialog" aria-labelledby="pm-promo-title" class="relative z-10 grid w-full overflow-hidden rounded-[28px] border border-[#e8b86d]/40 shadow-[0_40px_90px_rgba(58,10,60,0.55)] ' +
      (onlyBlack ? "max-w-[440px]" : "max-w-[760px] md:grid-cols-2") +
      '">' +
      '<button type="button" data-pm-promo-close aria-label="Fechar" class="absolute top-3 right-3 z-20 flex h-9 w-9 items-center justify-center rounded-full bg-black/35 text-white hover:bg-black/55">' +
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button>' +
      (onlyBlack ? "" : sideA()) +
      sideB(onlyBlack) +
      "</div>";
    document.body.appendChild(host);

    host.querySelector("[data-pm-promo-overlay]").addEventListener("click", close);
    host.querySelector("[data-pm-promo-close]").addEventListener("click", close);
    var cta = host.querySelector("[data-pm-promo-cta]");
    if (cta) cta.addEventListener("click", markDone);
    var copy = host.querySelector("[data-pm-copy-coupon]");
    if (copy) {
      copy.addEventListener("click", function () {
        var label = copy.querySelector("[data-pm-copy-label]");
        var iconWrap = copy.querySelector("[data-pm-copy-icon]");
        function paint(ok) {
          if (label) label.textContent = ok ? "Copiado" : "Copiar";
          if (iconWrap) iconWrap.innerHTML = icon(ok ? "check" : "copy", 14);
        }
        function done(ok) {
          if (!label) return;
          paint(ok);
          if (ok) window.setTimeout(function () { paint(false); }, 1800);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(COUPON).then(function () { done(true); }, function () { done(false); });
        } else {
          done(false);
        }
      });
    }

    if (window.gsap) {
      var card = host.querySelector("[data-pm-promo-card]");
      var overlay = host.querySelector("[data-pm-promo-overlay]");
      window.gsap.fromTo(overlay, { opacity: 0 }, { opacity: 1, duration: 0.35 });
      window.gsap.fromTo(card, { opacity: 0, y: 48, scale: 0.9 }, { opacity: 1, y: 0, scale: 1, duration: 0.7, ease: "power3.out" });
    }
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") close();
  });

  window.setTimeout(show, FIRST_DELAY_MS);
})();
