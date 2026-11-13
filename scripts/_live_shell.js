(function () {
  window.__pmShellBoot = Date.now();
  var base = "https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/";
  var shell = { css: base + "home.css?v=premium1" };

  function bind(root) {
    var menuButton = root.querySelector("[data-pm-menu-toggle]");
    var menu = root.querySelector("[data-pm-menu]");
    if (menuButton && menu) {
      menu.classList.add("pm-menu-panel");
      menu.classList.remove("hidden");
      menu.querySelectorAll("nav > div > a, nav > div > div").forEach(function (node) {
        node.setAttribute("data-pm-menu-item", "");
      });

      var overlay = root.querySelector("[data-pm-menu-overlay]");
      if (!overlay) {
        overlay = document.createElement("button");
        overlay.type = "button";
        overlay.setAttribute("data-pm-menu-overlay", "");
        overlay.setAttribute("aria-label", "Fechar menu");
        overlay.className = "pm-menu-overlay";
        root.appendChild(overlay);
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
    root.querySelectorAll("[data-pm-subtoggle]").forEach(function (button) {
      button.addEventListener("click", function () {
        var sub = button.nextElementSibling;
        if (!sub || !sub.hasAttribute("data-pm-sub")) return;
        var hidden = sub.classList.toggle("hidden");
        button.setAttribute("aria-expanded", hidden ? "false" : "true");
        var icon = button.querySelector("svg");
        if (icon) icon.classList.toggle("rotate-180", !hidden);
      });
    });
    var searchButton = root.querySelector("[data-pm-search]");
    if (searchButton) {
      searchButton.addEventListener("click", function () {
        var form = root.querySelector("[data-pm-search-form]");
        if (!form) {
          form = document.createElement("form");
          form.setAttribute("data-pm-search-form", "");
          form.action = "/";
          form.method = "get";
          form.className =
            "fixed inset-x-0 top-[154px] z-[90] border-b border-outline/40 bg-white px-container-margin py-4 md:top-[164px]";
          form.innerHTML =
            '<input name="s" type="search" placeholder="Buscar serviços" class="w-full rounded-full border border-primary/25 px-4 py-3 text-sm text-on-surface outline-none" />';
          root.appendChild(form);
          var input = form.querySelector("input");
          if (input) input.focus();
          return;
        }
        form.classList.toggle("hidden");
      });
    }
    root.querySelectorAll("[data-pm-account]").forEach(function (node) {
      node.addEventListener("click", function (event) {
        event.preventDefault();
        window.location.href = "/minha-conta/";
      });
    });
    try {
      var items = JSON.parse(localStorage.getItem("pm-cart-v1") || "[]");
      var total = items.reduce(function (sum, item) {
        return sum + (item.qty || 0);
      }, 0);
      if (total) {
        root.querySelectorAll('a[href="/carrinho/"], a[href="/carrinho"]').forEach(function (link) {
          var badge = document.createElement("span");
          badge.textContent = String(total);
          badge.setAttribute("data-pm-badge", "");
          badge.className =
            "absolute flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-white";
          badge.style.top = "-10px";
          badge.style.right = "-10px";
          badge.style.zIndex = "3";
          link.appendChild(badge);
        });
      }
    } catch (error) {}
  }

  // As variáveis da marca vivem em :root no home.css; dentro de uma shadow root :root não
  // existe, então elas entram aqui pelo :host. As fontes são declaradas no documento, porque
  // @font-face dentro da shadow root não carrega arquivo.
  var hostVars =
    "<style>:host{--brand-primary:#700053;--brand-primary-container:#4a1848;--brand-on-primary-container:#f3c6ee;" +
    "--brand-secondary:#8a5a12;--brand-secondary-container:#e8b86d;--brand-on-secondary-container:#5c3d00;" +
    "--brand-surface-tint:#8e3f8b;--brand-shadow-card:0 18px 40px rgba(58,10,60,.08);" +
    '--font-manrope:"Manrope","Manrope Fallback";--font-display:"Cormorant Garamond","Cormorant Garamond Fallback"}</style>';

  var fontsReady = null;
  function ensureFonts() {
    if (fontsReady) return fontsReady;
    fontsReady = fetch(shell.css)
      .then(function (response) { return response.text(); })
      .then(function (text) {
        var faces = text.match(/@font-face\s*\{[^}]*\}/g) || [];
        if (!faces.length || document.getElementById("pm-shell-fonts")) return;
        var style = document.createElement("style");
        style.id = "pm-shell-fonts";
        style.textContent = faces.join("\n");
        document.head.appendChild(style);
      })
      .catch(function () {});
    return fontsReady;
  }

  function mount(id, html) {
    var host = document.getElementById(id);
    if (!host || !html) return;
    var root = host.attachShadow({ mode: "open" });
    var css = shell.css || "";
    root.innerHTML = hostVars + '<link rel="stylesheet" href="' + css + '">' + html;
    ensureFonts();
    bind(root);
  }

  function place(id, html) {
    var host = document.getElementById(id);
    if (!host) {
      host = document.createElement("div");
      host.id = id;
      if (id === "pm-shell-header") {
        document.body.insertBefore(host, document.body.firstChild);
      } else {
        document.body.appendChild(host);
      }
    }
    mount(id, html);
  }

  function setField(name, value, notify) {
    document.querySelectorAll('input[name="' + name + '"], textarea[name="' + name + '"]').forEach(function (node) {
      var next = value == null ? "" : String(value);
      // Theme/CF7 inline keeps rewriting these hidden fields. Lock .value so Store API wins.
      if (!node.__pmTotalsLock) {
        var held = next;
        try {
          Object.defineProperty(node, "value", {
            configurable: true,
            enumerable: true,
            get: function () {
              return held;
            },
            set: function () {
              /* ignore theme writes — paintCheckoutTotals updates held via __pmSet */
            },
          });
          node.__pmSet = function (v) {
            held = v == null ? "" : String(v);
          };
          node.__pmTotalsLock = true;
        } catch (error) {
          node.__pmTotalsLock = false;
        }
      }
      if (node.__pmSet) node.__pmSet(next);
      else node.value = next;
      try {
        node.setAttribute("value", next);
      } catch (error) {}
      // Avoid noisy change events on the tight repaint loop — they retrigger theme fillers
      if (notify) {
        try {
          node.dispatchEvent(new Event("input", { bubbles: true }));
          node.dispatchEvent(new Event("change", { bubbles: true }));
        } catch (error) {}
      }
    });
  }

  function moneyMajorFromMinor(minor, minorUnit, decimalSep) {
    var unit = minorUnit == null ? 2 : Number(minorUnit);
    var n = Number(minor || 0);
    if (!isFinite(n)) n = 0;
    var major = n / Math.pow(10, unit);
    var sep = decimalSep || ",";
    return major.toFixed(2).replace(".", sep);
  }

  var lastTotals = null;

  function paintCheckoutTotals(values, notify) {
    if (!values) return;
    setField("cupom", values.cupom, notify);
    setField("cupomamount", values.cupomamount, notify);
    setField("fullvalue", values.fullvalue, notify);
    setField("totalamount", values.totalamount, notify);
  }

  /** Fill CF7 cupom/totals from Store API without touching card/gateway fields. */
  function syncCheckoutTotalsFromWoo() {
    return fetch("/wp-json/wc/store/v1/cart", { credentials: "same-origin" })
      .then(function (response) {
        return response.json().then(function (data) {
          if (!response.ok) throw new Error("woo");
          return data;
        });
      })
      .then(function (data) {
        var items = (data && data.items) || [];
        var totals = (data && data.totals) || {};
        var minorUnit = totals.currency_minor_unit != null ? Number(totals.currency_minor_unit) : 2;
        // CF7/payment scripts on this site parse majors with "." (not locale comma)
        var sep = ".";
        var coupons = (data.coupons || [])
          .map(function (c) {
            return String((c && (c.code || c)) || "").trim();
          })
          .filter(Boolean);
        var discount = Number(totals.total_discount || 0);
        var itemsTotal = Number(totals.total_items || 0);
        var priceTotal = Number(totals.total_price || 0);
        // Ignore empty-cart snapshots so we don't lock zeros before session hydrates
        if (!items.length && itemsTotal <= 0 && !coupons.length) {
          return lastTotals;
        }
        lastTotals = {
          cupom: coupons.length ? coupons[coupons.length - 1] : "",
          cupomamount: moneyMajorFromMinor(discount, minorUnit, sep),
          fullvalue: moneyMajorFromMinor(itemsTotal, minorUnit, sep),
          totalamount: moneyMajorFromMinor(priceTotal, minorUnit, sep),
        };
        window.__pmLastTotals = lastTotals;
        // Never dispatch change here — theme listeners overwrite totals
        paintCheckoutTotals(lastTotals, false);
        return lastTotals;
      })
      .catch(function () {
        return null;
      });
  }

  function scheduleCheckoutSync() {
    if (window.__pmShellSyncStarted) return;
    window.__pmShellSyncStarted = true;
    window.__pmShellSync = syncCheckoutTotalsFromWoo;
    syncCheckoutTotalsFromWoo();
    // Theme/CF7 inline rewrites hidden fields — keep re-applying Store API values
    window.setInterval(function () {
      if (lastTotals) paintCheckoutTotals(lastTotals, false);
      syncCheckoutTotalsFromWoo();
    }, 300);
    document.addEventListener(
      "focusin",
      function () {
        if (lastTotals) paintCheckoutTotals(lastTotals, false);
        syncCheckoutTotalsFromWoo();
      },
      true,
    );
  }

  fetch(base + "checkout-header.html?v=shell2")
    .then(function (response) { return response.text(); })
    .then(function (html) { place("pm-shell-header", html); });
  fetch(base + "checkout-footer.html?v=shell2")
    .then(function (response) { return response.text(); })
    .then(function (html) { place("pm-shell-footer", html); });

  scheduleCheckoutSync();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleCheckoutSync);
  }
  window.addEventListener("load", scheduleCheckoutSync);
})();
