(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var heroIndex = 0;
  var heroTimer = 0;

  function padLeft(node) {
    return parseFloat(getComputedStyle(node).paddingLeft) || 0;
  }

  function nearestIndex(node) {
    var cards = node.querySelectorAll("[data-carousel-card]");
    if (!cards.length) return 0;
    var origin = node.scrollLeft + padLeft(node);
    var best = 0;
    var dist = Infinity;
    cards.forEach(function (card, index) {
      var delta = Math.abs(card.offsetLeft - origin);
      if (delta < dist) {
        dist = delta;
        best = index;
      }
    });
    return best;
  }

  function bindCarousel(track) {
    var wrap = track.parentElement;
    if (!wrap) return;
    var buttons = wrap.querySelectorAll("button");
    if (buttons.length < 2) return;
    var index = 0;
    var animating = false;
    var token = 0;

    function goTo(next) {
      var cards = track.querySelectorAll("[data-carousel-card]");
      if (!cards.length) return;
      next = Math.max(0, Math.min(cards.length - 1, next));
      index = next;
      animating = true;
      var current = ++token;
      track.style.scrollSnapType = "none";
      track.scrollTo({
        left: cards[next].offsetLeft - padLeft(track),
        behavior: "smooth",
      });
      var finish = function () {
        if (current !== token) return;
        track.style.scrollSnapType = "";
        animating = false;
      };
      track.addEventListener("scrollend", finish, { once: true });
      window.setTimeout(finish, 520);
    }

    buttons[0].addEventListener("click", function () {
      if (!animating) index = nearestIndex(track);
      goTo(index - 1);
    });
    buttons[1].addEventListener("click", function () {
      if (!animating) index = nearestIndex(track);
      goTo(index + 1);
    });
    track.addEventListener("scroll", function () {
      if (animating) return;
      window.clearTimeout(track._pmSync);
      track._pmSync = window.setTimeout(function () {
        index = nearestIndex(track);
      }, 80);
    });
  }

  document.querySelectorAll(".carousel-track").forEach(bindCarousel);

  var activeFilter =
    "rounded-full bg-primary px-4 py-2 text-sm font-semibold text-on-primary";
  var idleFilter =
    "rounded-full border border-primary/25 px-4 py-2 text-sm text-primary";

  var methodFilter = "todos";
  var audienceFilter = "todos";
  document.querySelectorAll("[data-audience-filter]").forEach(function (button) {
    if (button.getAttribute("aria-pressed") === "true") {
      audienceFilter = button.getAttribute("data-audience-filter") || "todos";
    }
  });

  function paintFilters() {
    document.querySelectorAll("[data-home-panel]").forEach(function (section) {
      var panel = section.getAttribute("data-home-panel");
      var audience = section.getAttribute("data-audience");
      var methodOk = methodFilter === "todos" || panel === methodFilter;
      var audienceOk =
        audienceFilter === "todos" ||
        !audience ||
        audience === "ambos" ||
        audience === audienceFilter;
      section.classList.toggle("hidden", !(methodOk && audienceOk));
    });
    document.querySelectorAll("[data-home-filter]").forEach(function (button) {
      var on = button.getAttribute("data-home-filter") === methodFilter;
      button.className = on ? activeFilter : idleFilter;
    });
    document.querySelectorAll("[data-audience-filter]").forEach(function (button) {
      var on = button.getAttribute("data-audience-filter") === audienceFilter;
      button.className = on ? activeFilter : idleFilter;
      button.setAttribute("aria-pressed", on ? "true" : "false");
    });
    var grid = document.querySelector("[data-catalog-grid]");
    var empty = document.querySelector("[data-catalog-empty]");
    if (grid && empty) {
      var visible = grid.querySelectorAll("[data-home-panel]:not(.hidden)").length;
      empty.classList.toggle("hidden", visible > 0);
    }
    if (window.ScrollTrigger) window.ScrollTrigger.refresh();
  }

  function applyFilter(id) {
    methodFilter = id || "todos";
    paintFilters();
  }

  document.querySelectorAll("[data-home-filter]").forEach(function (button) {
    button.addEventListener("click", function () {
      applyFilter(button.getAttribute("data-home-filter"));
    });
  });
  document.querySelectorAll("[data-audience-filter]").forEach(function (button) {
    button.addEventListener("click", function () {
      audienceFilter = button.getAttribute("data-audience-filter") || "todos";
      paintFilters();
    });
  });
  if (document.querySelector("[data-catalog-grid]")) paintFilters();

  function showHero(index, animate) {
    var slides = document.querySelectorAll("[data-hero-slide]");
    var count = slides.length;
    if (!count) return;
    heroIndex = (index + count) % count;
    slides.forEach(function (slide, i) {
      var on = i === heroIndex;
      slide.classList.toggle("opacity-100", on);
      slide.classList.toggle("opacity-0", !on);
      slide.classList.toggle("pointer-events-none", !on);
    });
    document.querySelectorAll("[data-hero-dot]").forEach(function (dot, i) {
      var on = i === heroIndex;
      dot.classList.toggle("w-8", on);
      dot.classList.toggle("bg-secondary-container", on);
      dot.classList.toggle("w-4", !on);
      dot.classList.toggle("bg-white/35", !on);
    });
    if (animate && window.gsap && !reduce) {
      var copy = slides[heroIndex].querySelector(".js-hero-copy");
      if (copy) {
        gsap.fromTo(
          copy,
          { opacity: 0, y: 18 },
          { opacity: 1, y: 0, duration: 0.6, ease: "power2.out" },
        );
      }
    }
  }

  var prev = document.querySelector("[data-hero-prev]");
  var next = document.querySelector("[data-hero-next]");
  if (prev) {
    prev.addEventListener("click", function () {
      showHero(heroIndex - 1, true);
    });
  }
  if (next) {
    next.addEventListener("click", function () {
      showHero(heroIndex + 1, true);
    });
  }
  document.querySelectorAll("[data-hero-dot]").forEach(function (dot) {
    dot.addEventListener("click", function () {
      showHero(Number(dot.getAttribute("data-hero-dot")), true);
    });
  });
  if (document.querySelector("[data-hero-slide]") && !reduce) {
    heroTimer = window.setInterval(function () {
      showHero(heroIndex + 1, true);
    }, 6400);
  }

  if (!document.getElementById("pm-menu-anim-style")) {
    var menuStyle = document.createElement("style");
    menuStyle.id = "pm-menu-anim-style";
    menuStyle.textContent =
      ".pm-menu-panel{max-height:0;opacity:0;visibility:hidden;pointer-events:none;overflow:hidden;" +
      "transition:max-height .34s ease,opacity .28s ease,visibility .28s ease}" +
      ".pm-menu-panel.is-open{max-height:min(78vh,720px);opacity:1;visibility:visible;pointer-events:auto;overflow-y:auto}" +
      ".pm-menu-panel [data-pm-menu-item]{opacity:0;transform:translateY(-8px);transition:opacity .28s ease,transform .28s ease}" +
      ".pm-menu-panel.is-open [data-pm-menu-item]{opacity:1;transform:translateY(0)}" +
      ".pm-menu-panel.is-open [data-pm-menu-item]:nth-child(1){transition-delay:40ms}" +
      ".pm-menu-panel.is-open [data-pm-menu-item]:nth-child(2){transition-delay:80ms}" +
      ".pm-menu-panel.is-open [data-pm-menu-item]:nth-child(3){transition-delay:120ms}" +
      ".pm-menu-panel.is-open [data-pm-menu-item]:nth-child(4){transition-delay:160ms}" +
      ".pm-menu-panel.is-open [data-pm-menu-item]:nth-child(5){transition-delay:200ms}" +
      ".pm-menu-panel.is-open [data-pm-menu-item]:nth-child(6){transition-delay:240ms}" +
      ".pm-menu-panel.is-open [data-pm-menu-item]:nth-child(7){transition-delay:280ms}" +
      ".pm-menu-panel.is-open [data-pm-menu-item]:nth-child(8){transition-delay:320ms}" +
      ".pm-menu-overlay{position:fixed;inset:0;z-index:70;background:rgba(20,4,18,.42);opacity:0;visibility:hidden;pointer-events:none;border:0;padding:0;transition:opacity .22s ease,visibility .22s ease}" +
      ".pm-menu-overlay.is-open{opacity:1;visibility:visible;pointer-events:auto}" +
      "@media (prefers-reduced-motion:reduce){.pm-menu-panel,.pm-menu-panel [data-pm-menu-item],.pm-menu-overlay{transition:none}" +
      ".pm-menu-panel [data-pm-menu-item]{opacity:1;transform:none}}";
    document.head.appendChild(menuStyle);
  }

  var menuButton = document.querySelector("[data-pm-menu-toggle]");
  var menu = document.querySelector("[data-pm-menu]");
  if (menuButton && menu) {
    menu.classList.add("pm-menu-panel");
    menu.classList.remove("hidden");
    menu.querySelectorAll("nav > div > a, nav > div > div").forEach(function (node) {
      node.setAttribute("data-pm-menu-item", "");
    });

    var overlay = document.querySelector("[data-pm-menu-overlay]");
    if (!overlay) {
      overlay = document.createElement("button");
      overlay.type = "button";
      overlay.setAttribute("data-pm-menu-overlay", "");
      overlay.setAttribute("aria-label", "Fechar menu");
      overlay.className = "pm-menu-overlay";
      document.body.appendChild(overlay);
    }

    function setMenuOpen(open) {
      menu.classList.toggle("is-open", open);
      overlay.classList.toggle("is-open", open);
      menu.setAttribute("aria-hidden", open ? "false" : "true");
      overlay.setAttribute("aria-hidden", open ? "false" : "true");
      menuButton.setAttribute("aria-expanded", open ? "true" : "false");
      menuButton.setAttribute("aria-label", open ? "Fechar menu" : "Abrir menu");
      var menuIcon = menuButton.querySelector('[data-pm-icon="menu"]');
      var closeIcon = menuButton.querySelector('[data-pm-icon="close"]');
      if (menuIcon) menuIcon.classList.toggle("hidden", open);
      if (closeIcon) closeIcon.classList.toggle("hidden", !open);
    }

    menuButton.addEventListener("click", function () {
      setMenuOpen(!menu.classList.contains("is-open"));
    });
    overlay.addEventListener("click", function () {
      setMenuOpen(false);
    });
  }

  document.querySelectorAll("[data-pm-subtoggle]").forEach(function (button) {
    button.addEventListener("click", function () {
      var sub = button.nextElementSibling;
      if (!sub || !sub.hasAttribute("data-pm-sub")) return;
      var hidden = sub.classList.toggle("hidden");
      button.setAttribute("aria-expanded", hidden ? "false" : "true");
      var icon = button.querySelector("svg");
      if (icon) icon.classList.toggle("rotate-180", !hidden);
    });
  });

  var searchButton = document.querySelector("[data-pm-search]");
  if (searchButton) {
    searchButton.addEventListener("click", function () {
      var form = document.querySelector("[data-pm-search-form]");
      if (!form) {
        form = document.createElement("form");
        form.setAttribute("data-pm-search-form", "");
        form.action = "/busca";
        form.method = "get";
        form.className =
          "fixed inset-x-0 top-[154px] z-[90] border-b border-outline/40 bg-white px-container-margin py-4 shadow-[0_18px_40px_rgba(58,10,60,0.12)] md:top-[164px]";
        var audienceNode = document.querySelector("[data-audience]");
        var audience = audienceNode
          ? audienceNode.getAttribute("data-audience") || ""
          : "";
        var hiddenAudience =
          audience === "masculino"
            ? '<input type="hidden" name="audience" value="masculino" />'
            : "";
        form.innerHTML =
          '<div class="flex items-center gap-2">' +
          '<input name="q" type="search" placeholder="Buscar serviços" class="w-full rounded-full border border-primary/25 px-4 py-3 text-sm text-on-surface outline-none" required />' +
          '<button type="submit" class="shrink-0 rounded-full bg-primary px-4 py-3 text-sm font-semibold text-on-primary">Buscar</button>' +
          "</div>" +
          hiddenAudience;
        document.body.appendChild(form);
        var input = form.querySelector('input[name="q"]');
        if (input) input.focus();
        return;
      }
      form.classList.toggle("hidden");
      if (!form.classList.contains("hidden")) {
        var field = form.querySelector('input[name="q"]');
        if (field) field.focus();
      }
    });
  }

  document.querySelectorAll("[data-pm-account]").forEach(function (node) {
    node.addEventListener("click", function (event) {
      event.preventDefault();
      window.location.href = "/minha-conta/";
    });
  });

  function motionCore() {
    if (!window.gsap || reduce) return;
    var firstCopy = document.querySelector(".opacity-100 .js-hero-copy");
    if (firstCopy) {
      gsap.fromTo(
        firstCopy,
        { opacity: 0, y: 18 },
        { opacity: 1, y: 0, duration: 0.6, ease: "power2.out" },
      );
    }
  }

  function motionScroll() {
    if (!window.gsap || !window.ScrollTrigger || reduce) return;
    gsap.registerPlugin(window.ScrollTrigger);
    gsap.utils.toArray(".js-reveal").forEach(function (section) {
      gsap.from(section, {
        y: 28,
        duration: 0.7,
        ease: "power3.out",
        scrollTrigger: {
          trigger: section,
          start: "top 92%",
          toggleActions: "play none none none",
        },
      });
    });
    gsap.from(".js-cat", {
      y: 14,
      stagger: 0.07,
      duration: 0.5,
      ease: "power2.out",
      scrollTrigger: {
        trigger: ".js-cats",
        start: "top 94%",
        toggleActions: "play none none none",
      },
    });
  }

  function loadScrollTrigger(done) {
    if (window.ScrollTrigger) {
      done();
      return;
    }
    var s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/ScrollTrigger.min.js";
    s.async = true;
    s.onload = done;
    s.onerror = done;
    document.head.appendChild(s);
  }

  function bootMotion() {
    motionCore();
    function startScroll() {
      loadScrollTrigger(motionScroll);
    }
    if ("requestIdleCallback" in window) {
      window.requestIdleCallback(startScroll, { timeout: 2500 });
    } else {
      window.setTimeout(startScroll, 1200);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootMotion);
  } else {
    bootMotion();
  }

  window.addEventListener("beforeunload", function () {
    window.clearInterval(heroTimer);
  });

  function ensureCartWrap(link) {
    var parent = link.parentElement;
    if (parent && parent.getAttribute("data-pm-cart-wrap") != null) return parent;
    var wrap = document.createElement("span");
    wrap.setAttribute("data-pm-cart-wrap", "");
    if (link.parentNode) {
      link.parentNode.insertBefore(wrap, link);
      wrap.appendChild(link);
    }
    return wrap;
  }

  function paintCartBadge(items) {
    var list = items || [];
    var total = list.reduce(function (sum, item) {
      return sum + (Number(item && item.qty) || 0);
    }, 0);
    document.querySelectorAll('a[href="/carrinho/"], a[href="/carrinho"]').forEach(function (link) {
      if (!link.classList.contains("relative")) link.classList.add("relative");
      var bottomNav = link.closest("nav");
      var inBar = bottomNav && bottomNav.className.indexOf("bottom-0") !== -1;
      link.setAttribute(
        "aria-label",
        total ? "Carrinho com " + total + (total === 1 ? " item" : " itens") : "Carrinho",
      );
      if (inBar) {
        var barBadge = link.querySelector("[data-pm-badge]");
        if (!total) {
          if (barBadge) barBadge.remove();
          return;
        }
        if (!barBadge) {
          barBadge = document.createElement("span");
          barBadge.setAttribute("data-pm-badge", "");
          link.appendChild(barBadge);
        }
        barBadge.className =
          "absolute top-1 right-3 flex h-4 min-w-4 items-center justify-center rounded-full bg-secondary-container px-1 text-[10px] font-bold text-on-secondary-container";
        barBadge.style.top = "";
        barBadge.style.right = "";
        barBadge.textContent = String(total);
        return;
      }
      var wrap = ensureCartWrap(link);
      var oldInside = link.querySelector("[data-pm-badge]");
      if (oldInside) oldInside.remove();
      var badge = wrap.querySelector("[data-pm-badge]");
      if (!total) {
        if (badge) badge.remove();
        return;
      }
      if (!badge) {
        badge = document.createElement("span");
        badge.setAttribute("data-pm-badge", "");
        wrap.appendChild(badge);
      }
      badge.className =
        "flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-white";
      badge.textContent = String(total);
    });
  }

  function setupHeaderShine() {
    if (reduce) return;
    var search = document.querySelector("[data-pm-search]");
    var account = document.querySelector("[data-pm-account]");
    var cart = document.querySelector(
      'header a[href="/carrinho"], header a[href="/carrinho/"]',
    );
    var nodes = [search, account, cart].filter(Boolean);
    if (!nodes.length) return;
    nodes.forEach(function (node) {
      node.classList.add("btn-lux-icon");
      node.setAttribute("data-pm-shine", "");
    });
    var delays = [0, 3.2, 6.4];
    var i;
    var j;
    var tmp;
    for (i = delays.length - 1; i > 0; i -= 1) {
      j = Math.floor(Math.random() * (i + 1));
      tmp = delays[i];
      delays[i] = delays[j];
      delays[j] = tmp;
    }
    nodes.forEach(function (node, index) {
      node.style.setProperty("--shine-delay", delays[index % delays.length] + "s");
    });
  }

  function readStoredCart() {
    try {
      return JSON.parse(localStorage.getItem("pm-cart-v1") || "[]");
    } catch (error) {
      return [];
    }
  }

  function setupPurchasePopup() {
    if (!document.getElementById("pm-purchase-desktop-style")) {
      var purchaseStyle = document.createElement("style");
      purchaseStyle.id = "pm-purchase-desktop-style";
      purchaseStyle.textContent =
        "[data-pm-purchase]{display:none!important}" +
        "@media (min-width:768px){[data-pm-purchase]{display:block!important}}";
      document.head.appendChild(purchaseStyle);
    }

    var host = null;
    document.querySelectorAll(".fixed.bottom-24, .fixed.bottom-8").forEach(function (node) {
      if (host) return;
      if (
        node.getAttribute("data-pm-whatsapp") != null ||
        node.querySelector('[aria-label="WhatsApp SAC Pello Menos"]')
      ) {
        return;
      }
      if (
        node.querySelector('a[href*="/produto/"]') &&
        (node.textContent || "").indexOf("comprou") !== -1
      ) {
        host = node;
      }
    });
    if (!host) return;

    host.setAttribute("data-pm-purchase", "");
    // Notificações de compra só no desktop (md+).
    if (window.matchMedia("(max-width: 767px)").matches) {
      host.setAttribute("aria-hidden", "true");
      return;
    }

    host.className =
      "fixed bottom-24 left-4 z-[60] w-max max-w-[min(calc(100vw-2rem),22rem)] md:bottom-8";

    var mediaBase =
      (window.location && window.location.origin
        ? window.location.origin
        : "") + "/wp-content/uploads/pm-home/media";
    var root = document.querySelector("[data-audience]");
    var male = root && root.getAttribute("data-audience") === "masculino";
    var female = [
      {
        name: "Camila R.",
        city: "Copacabana, RJ",
        product: "Axilas Laser",
        href: "/produto/axilas-laser/",
        image: mediaBase + "/images/products/axilas-laser.png",
        when: "há 2 minutos",
      },
      {
        name: "Juliana M.",
        city: "Tijuca, RJ",
        product: "Virilha Total Laser",
        href: "/produto/virilha-laser/",
        image: mediaBase + "/images/products/virilha-laser.png",
        when: "há 6 minutos",
      },
      {
        name: "Fernanda L.",
        city: "Barra da Tijuca, RJ",
        product: "Perna Inteira – Cera",
        href: "/produto/perna-cera/",
        image: mediaBase + "/images/products/perna-cera.png",
        when: "há 11 minutos",
      },
      {
        name: "Bianca T.",
        city: "Avenida Paulista, SP",
        product: "Design de Sobrancelha",
        href: "/produto/design-sobrancelha/",
        image: mediaBase + "/images/products/design-sobrancelha.png",
        when: "há 18 minutos",
      },
      {
        name: "Larissa P.",
        city: "Campo Grande, RJ",
        product: "Braços Inteiros Laser",
        href: "/produto/bracos-laser/",
        image: mediaBase + "/images/products/bracos-laser.png",
        when: "há 24 minutos",
      },
    ];
    var males = [
      {
        name: "Rafael C.",
        city: "Copacabana, RJ",
        product: "Tórax Laser",
        href: "/produto/peito-laser-masc/",
        image: mediaBase + "/images/products/male/peito-laser-masc.png",
        when: "há 2 minutos",
      },
      {
        name: "Bruno M.",
        city: "Tijuca, RJ",
        product: "Costas Laser",
        href: "/produto/costas-laser-masc/",
        image: mediaBase + "/images/products/male/costas-laser-masc.png",
        when: "há 6 minutos",
      },
      {
        name: "Pedro S.",
        city: "Barra da Tijuca, RJ",
        product: "Axila Laser",
        href: "/produto/axilas-laser-masc/",
        image: mediaBase + "/images/products/male/axilas-laser-masc.png",
        when: "há 11 minutos",
      },
      {
        name: "Lucas T.",
        city: "Avenida Paulista, SP",
        product: "Barba Laser",
        href: "/produto/barba-laser-masc/",
        image: mediaBase + "/images/products/male/barba-laser-masc.jpg",
        when: "há 18 minutos",
      },
      {
        name: "Thiago P.",
        city: "Copacabana, RJ",
        product: "Queixo Laser",
        href: "/produto/queixo-laser-masc/",
        image: mediaBase + "/images/products/male/queixo-laser-masc.jpg",
        when: "há 24 minutos",
      },
    ];
    var items = male ? males : female;
    var index = 0;
    var VISIBLE_MS = 6000;
    var OUT_MS = reduce ? 0 : 400;
    var card = host.querySelector("a");
    if (!card) return;

    function gap() {
      return 4000 + Math.floor(Math.random() * 3001);
    }

    function render(item) {
      card.href = item.href;
      card.className =
        "inline-flex items-center gap-3 rounded-2xl border border-primary/15 bg-white p-2.5 shadow-[0_18px_40px_rgba(58,10,60,0.18)]";
      card.innerHTML =
        '<span class="relative h-14 w-14 shrink-0 overflow-hidden rounded-xl bg-surface-container-high">' +
        '<img alt="" class="object-cover" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover" src="' +
        item.image +
        '"/></span><span class="min-w-0">' +
        '<span class="block text-sm font-semibold text-on-surface">' +
        item.name +
        '</span><span class="block text-xs whitespace-normal text-on-surface-variant">comprou ' +
        item.product +
        '</span><span class="mt-0.5 block text-[11px] whitespace-normal text-primary">' +
        item.city +
        " · " +
        item.when +
        "</span></span>";
    }

    function showIn() {
      host.classList.remove("pointer-events-none");
      host.setAttribute("aria-hidden", "false");
      card.tabIndex = 0;
      if (window.gsap && !reduce) {
        window.gsap.fromTo(
          card,
          { x: -28, y: 12, opacity: 0, scale: 0.96 },
          { x: 0, y: 0, opacity: 1, scale: 1, duration: 0.5, ease: "power3.out" },
        );
      } else {
        card.style.opacity = "1";
      }
    }

    function showOut(done) {
      host.classList.add("pointer-events-none");
      host.setAttribute("aria-hidden", "true");
      card.tabIndex = -1;
      if (window.gsap && !reduce) {
        window.gsap.to(card, {
          x: -20,
          y: 10,
          opacity: 0,
          scale: 0.96,
          duration: 0.4,
          ease: "power3.in",
          onComplete: done,
        });
      } else {
        card.style.opacity = "0";
        done();
      }
    }

    function cycle() {
      window.setTimeout(function () {
        showOut(function () {
          window.setTimeout(function () {
            index = (index + 1) % items.length;
            render(items[index]);
            showIn();
            cycle();
          }, gap());
        });
      }, VISIBLE_MS);
    }

    render(items[0]);
    showIn();
    cycle();
  }

  window.pmPaintCart = function (items) {
    paintCartBadge(items || readStoredCart());
  };
  window.pmPaintCart();
  setupHeaderShine();
  setupPurchasePopup();
  window.addEventListener("storage", function (event) {
    if (event.key === "pm-cart-v1") window.pmPaintCart();
  });
  window.addEventListener("pageshow", function () {
    window.pmPaintCart();
  });
})();
