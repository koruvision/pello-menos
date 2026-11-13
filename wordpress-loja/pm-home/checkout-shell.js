(function () {
  window.__pmShellBoot = Date.now();
  var base = "https://loja.pellomenos.com.br/wp-content/uploads/pm-home/";
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
          form.action = "/busca";
          form.method = "get";
          form.className =
            "fixed inset-x-0 top-[154px] z-[90] border-b border-outline/40 bg-white px-container-margin py-4 md:top-[164px]";
          form.innerHTML =
            '<input name="q" type="search" placeholder="Buscar serviços" class="w-full rounded-full border border-primary/25 px-4 py-3 text-sm text-on-surface outline-none" required />';
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
          var parent = link.parentElement;
          var wrap =
            parent && parent.getAttribute("data-pm-cart-wrap") != null
              ? parent
              : (function () {
                  var w = document.createElement("span");
                  w.setAttribute("data-pm-cart-wrap", "");
                  if (link.parentNode) {
                    link.parentNode.insertBefore(w, link);
                    w.appendChild(link);
                  }
                  return w;
                })();
          var oldInside = link.querySelector("[data-pm-badge]");
          if (oldInside) oldInside.remove();
          var badge = wrap.querySelector("[data-pm-badge]");
          if (!badge) {
            badge = document.createElement("span");
            badge.setAttribute("data-pm-badge", "");
            wrap.appendChild(badge);
          }
          badge.textContent = String(total);
          badge.className =
            "flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-white";
        });
      }
    } catch (error) {}
  }

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

  function stripAudienceSwitch(html) {
    // Carrinho/checkout: chrome feminino sem faixa Feminino|Masculino.
    if (!html || html.indexOf('aria-label="Público"') === -1) return html;
    return html.replace(
      /<div[^>]*border-b[^>]*>\s*<div[^>]*aria-label="Público"[^>]*>[\s\S]*?<\/div>\s*<\/div>/i,
      "",
    );
  }

  function mount(id, html) {
    var host = document.getElementById(id);
    if (!host || !html) return;
    if (host.shadowRoot) return;
    var markup = id === "pm-shell-header" ? stripAudienceSwitch(html) : html;
    var root = host.attachShadow({ mode: "open" });
    var css = shell.css || "";
    root.innerHTML = hostVars + '<link rel="stylesheet" href="' + css + '">' + markup;
    ensureFonts();
    bind(root);
    if (id === "pm-shell-header" && root) {
      var nav = root.querySelector('[aria-label="Público"]');
      if (nav) {
        var wrap = nav.parentElement;
        if (wrap && wrap !== root) wrap.remove();
        else nav.remove();
      }
    }
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
      if (!node.__pmTotalsLock) {
        var held = next;
        try {
          Object.defineProperty(node, "value", {
            configurable: true,
            enumerable: true,
            get: function () {
              return held;
            },
            set: function () {},
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

  function moneyDisplay(minor, minorUnit) {
    return "R$ " + moneyMajorFromMinor(minor, minorUnit, ",");
  }

  function decodeEntities(value) {
    var raw = String(value == null ? "" : value);
    if (!raw || raw.indexOf("&") === -1) return raw;
    var ta = document.createElement("textarea");
    ta.innerHTML = raw;
    return ta.value;
  }

  var IMAGE_FALLBACKS = {
    "": base + "media/images/products/body-splash.png",
    "body-splash": base + "media/images/products/body-splash.png",
    "body-splash-livre": base + "media/images/products/body-splash.png",
    "body-splash-marcante": base + "media/images/products/body-splash.png",
    "body-splash-autentica": base + "media/images/products/body-splash.png",
  };

  /** Mesma regra do cart.js: /images/... → media do pm-home. */
  function productImageUrl(path) {
    if (!path) return "";
    if (/^https?:\/\//i.test(path)) return path;
    if (path.indexOf("/images/") === 0) return base + "media" + path;
    if (path.indexOf("media/") === 0) return base + path;
    return path;
  }

  function catalogImageForLine(wooId, nameNorm, catalogId) {
    if (catalogId && catalogById[catalogId] && catalogById[catalogId].image) {
      return productImageUrl(catalogById[catalogId].image);
    }
    if (!catalogReady) return "";
    var keys = Object.keys(catalogById);
    for (var i = 0; i < keys.length; i++) {
      var row = catalogById[keys[i]];
      if (!row || !row.image) continue;
      if (
        wooId &&
        (String(row.wooId || "") === wooId ||
          String(row.productId || "") === wooId ||
          String(row.id || "") === wooId)
      ) {
        return productImageUrl(row.image);
      }
      var units = row.units || {};
      var uids = Object.keys(units);
      for (var u = 0; u < uids.length; u++) {
        var meta = units[uids[u]];
        if (meta && wooId && String(meta.variationId || "") === wooId) {
          return productImageUrl(row.image);
        }
      }
      if (nameNorm) {
        var rn = String(row.name || "")
          .toLowerCase()
          .replace(/\s+/g, " ")
          .trim();
        if (rn === nameNorm) return productImageUrl(row.image);
      }
    }
    return "";
  }

  /** pm_catalog_id da linha Store API (desambigua esfoliação vs cera). */
  function lineCatalogId(line) {
    if (!line) return "";
    var raw =
      line.pm_catalog_id ||
      (line.extensions &&
        (line.extensions.pm_catalog_id ||
          (line.extensions.pellomenos && line.extensions.pellomenos.pm_catalog_id))) ||
      "";
    if (raw) return String(raw);
    var data = line.item_data || [];
    for (var i = 0; i < data.length; i++) {
      var row = data[i] || {};
      var key = String(row.key || row.name || "").toLowerCase();
      if (key === "pm_catalog_id" || key === "_pm_catalog_id") {
        return String(row.value || row.display || "").trim();
      }
    }
    return "";
  }

  function matchLocalCartItem(line, localItems) {
    if (!line || !Array.isArray(localItems)) return null;
    var cat = lineCatalogId(line);
    var wooId = line.id != null ? String(line.id) : "";
    var used = {};
    if (cat) {
      for (var i = 0; i < localItems.length; i++) {
        var a = localItems[i];
        if (a && String(a.id || "") === cat) return a;
      }
    }
    if (line.key) {
      for (var j = 0; j < localItems.length; j++) {
        var b = localItems[j];
        if (b && b.wooKey && String(b.wooKey) === String(line.key)) return b;
      }
    }
    // Fallback wooId só se houver exatamente um local com esse id ainda não "preferido"
    var hits = [];
    for (var k = 0; k < localItems.length; k++) {
      var c = localItems[k];
      if (c && wooId && String(c.wooId || "") === wooId) hits.push(c);
    }
    return hits.length === 1 ? hits[0] : null;
  }

  function displayLineName(line, localMatch) {
    if (localMatch && localMatch.name) return String(localMatch.name);
    var cat = lineCatalogId(line);
    if (cat && catalogById[cat] && catalogById[cat].name) {
      return String(catalogById[cat].name);
    }
    return decodeEntities(line && line.name ? line.name : "Item");
  }

  /**
   * Fonte de verdade = frontend (pm-cart / cart-related).
   * Woo featured image fica por ultimo: varios SKUs linha reusam foto de cera.
   */
  function resolveLineImage(line) {
    var wooId = line && (line.id != null ? String(line.id) : "");
    var name = decodeEntities(String((line && line.name) || ""))
      .toLowerCase()
      .replace(/\s+/g, " ")
      .trim();
    var localMatch = null;
    try {
      var local = JSON.parse(localStorage.getItem("pm-cart-v1") || "[]");
      localMatch = matchLocalCartItem(line, local);
      if (localMatch && localMatch.image) return productImageUrl(String(localMatch.image));
    } catch (error) {}
    var fromCatalog = catalogImageForLine(
      wooId,
      name,
      (localMatch && localMatch.id) || lineCatalogId(line) || ""
    );
    if (fromCatalog) return fromCatalog;
    if (wooId && IMAGE_FALLBACKS[wooId]) return IMAGE_FALLBACKS[wooId];
    if (name.indexOf("body splash") >= 0) return IMAGE_FALLBACKS[""];
    var fromWoo =
      (line && line.images && line.images[0] && (line.images[0].thumbnail || line.images[0].src)) ||
      "";
    return fromWoo || "";
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  var lastTotals = null;
  var lastCart = null;
  var cartBusy = false;
  var cartError = "";
  var cartStatus = "";
  var wooNonce = "";
  var loadingFailsafeTimer = null;
  var catalogByWooId = {};
  var catalogByName = {};
  var catalogById = {};
  var catalogReady = false;
  var SPLASH_CENTS = 8161; // Body Splash R$ 81,61 (de R$ 85,90, 5% OFF)
  var SPLASH_LIST_CENTS = 8590;

  function ingestCatalog(data) {
    catalogByWooId = {};
    catalogByName = {};
    catalogById = {};
    if (!data || !data.products) return;
    Object.keys(data.products).forEach(function (pid) {
      var row = data.products[pid];
      if (!row) return;
      var cents = Number(row.priceCents) || 0;
      if (String(row.id || pid).indexOf("body-splash") === 0) cents = SPLASH_CENTS;
      if (cents <= 0) return;
      var catalogId = String(row.id || pid);
      catalogById[catalogId] = row;
      function remember(id) {
        if (!id) return;
        catalogByWooId[String(id)] = cents;
      }
      remember(row.wooId);
      remember(row.productId);
      remember(row.id || pid);
      var units = row.units || {};
      Object.keys(units).forEach(function (uid) {
        var meta = units[uid];
        if (meta) remember(meta.variationId);
      });
      var name = String(row.name || "")
        .toLowerCase()
        .replace(/\s+/g, " ")
        .trim();
      if (name) catalogByName[name] = cents;
    });
    catalogReady = true;
  }

  function loadCatalogPrices() {
    var boot =
      window.pmBlackNov && typeof window.pmBlackNov.load === "function"
        ? window.pmBlackNov.load()
        : Promise.resolve();
    var url =
      (window.location && window.location.origin ? window.location.origin : "") +
      "/wp-content/uploads/pm-home/cart-related.json";
    return boot
      .catch(function () {})
      .then(function () {
        return fetch(url, { credentials: "same-origin", cache: "no-cache" });
      })
      .then(function (resp) {
        return resp.ok ? resp.json() : null;
      })
      .then(function (data) {
        if (data) ingestCatalog(data);
        return data;
      })
      .catch(function () {
        return null;
      });
  }

  function isIntentionalOneReal(idOrName) {
    var s = String(idOrName || "").toLowerCase();
    return s.indexOf("produto-1-real") !== -1 || s.indexOf("1 real") !== -1 || s.indexOf("produto r$") !== -1;
  }

  function isTestChargeCents(cents, idOrName) {
    return Number(cents) === 100 && !isIntentionalOneReal(idOrName);
  }

  function paintCheckoutTotals(values, notify) {
    if (!values) return;
    setField("cupom", values.cupom, notify);
    setField("cupomamount", values.cupomamount, notify);
    setField("fullvalue", values.fullvalue, notify);
    setField("totalamount", values.totalamount, notify);
  }

  /** Sync CF7 line fields from Store API so payment matches panel edits.
   * Theme inline fills cart/cartqtd once on load (comma-separated ids/qtys). */
  function paintCheckoutLines(data, notify) {
    var items = (data && data.items) || [];
    var ids = [];
    var qtys = [];
    items.forEach(function (line) {
      if (!line || line.id == null) return;
      ids.push(String(line.id));
      qtys.push(String(line.quantity != null ? line.quantity : 1));
    });
    setField("cart", ids.join(","), notify);
    setField("cartqtd", qtys.join(","), notify);
  }

  /** Regra do cupom (espelha pmWoo.couponRuleFromCart em product.js; o shell não depende dele). */
  function couponRuleFromTotals(data) {
    var coupons = (data && data.coupons) || [];
    if (!coupons.length) return null;
    var t = (data && data.totals) || {};
    var discount = Math.round(Number(t.total_discount || 0)) || 0;
    var itemsTotal = Math.round(Number(t.total_items || 0)) || 0;
    var first = coupons[0] || {};
    var code = String(first.code || first || "").trim();
    var type = String(first.discount_type || "").toLowerCase();
    if (/^PM1L/i.test(code)) {
      return {
        code: code,
        type: "target_total",
        percent: 0,
        fixedCents: 0,
        targetCents: 100,
        catalogIds: ["buco-linha"],
      };
    }
    var rule = {
      code: code,
      type: type || "percent",
      percent: 0,
      fixedCents: discount,
    };
    if (type === "fixed_cart") return rule;
    if (itemsTotal > 0 && discount > 0) {
      var pct = (discount / itemsTotal) * 100;
      var rounded = Math.round(pct * 2) / 2;
      rule.percent = Math.abs(pct - rounded) < 0.4 ? rounded : Math.round(pct * 100) / 100;
      rule.type = "percent";
    }
    return rule;
  }

  function displayDiscountCents(rule, subtotalCents) {
    if (!rule) return 0;
    var subtotal = Math.max(0, Math.round(Number(subtotalCents) || 0));
    if (rule.type === "target_total") {
      var target = Math.max(0, Math.round(Number(rule.targetCents) || 100));
      return Math.max(0, subtotal - target);
    }
    if (rule.type === "fixed_cart") return Math.min(subtotal, Math.max(0, rule.fixedCents || 0));
    if (rule.percent > 0) return Math.min(subtotal, Math.round((subtotal * rule.percent) / 100));
    return Math.min(subtotal, Math.max(0, rule.fixedCents || 0));
  }

  function totalsFromCart(data) {
    var items = (data && data.items) || [];
    var totals = (data && data.totals) || {};
    var minorUnit = totals.currency_minor_unit != null ? Number(totals.currency_minor_unit) : 2;
    var sep = ".";
    var coupons = (data.coupons || [])
      .map(function (c) {
        return String((c && (c.code || c)) || "").trim();
      })
      .filter(Boolean);
    var discount = Number(totals.total_discount || 0);
    var itemsTotal = Number(totals.total_items || 0);
    var priceTotal = Number(totals.total_price || 0);
    // Se o Woo listou cupom+desconto mas total_price ainda veio cheio, força o líquido nos hiddens CF7.
    if (coupons.length && discount > 0 && priceTotal >= itemsTotal) {
      priceTotal = Math.max(0, itemsTotal - discount);
    }
    if (!items.length && itemsTotal <= 0 && !coupons.length) {
      return null;
    }
    return {
      cupom: coupons.length ? coupons[coupons.length - 1] : "",
      cupomamount: moneyMajorFromMinor(discount, minorUnit, sep),
      fullvalue: moneyMajorFromMinor(itemsTotal, minorUnit, sep),
      totalamount: moneyMajorFromMinor(priceTotal, minorUnit, sep),
      minorUnit: minorUnit,
      coupons: coupons,
      items: items,
      totals: totals,
    };
  }

  function applyCartSnapshot(data, opts) {
    lastCart = data || lastCart;
    try {
      document.dispatchEvent(new CustomEvent("pm:cart-updated"));
    } catch (e) {}
    var painted = totalsFromCart(data);
    if (painted) {
      lastTotals = {
        cupom: painted.cupom,
        cupomamount: painted.cupomamount,
        fullvalue: painted.fullvalue,
        totalamount: painted.totalamount,
      };
      window.__pmLastTotals = lastTotals;
      paintCheckoutTotals(lastTotals, false);
      paintCheckoutLines(data, false);
      '(function(){var _d=setTimeout(function(){applyInstallmentRules()},300)})();';
    } else if (opts && opts.allowEmpty) {
      lastTotals = {
        cupom: "",
        cupomamount: "0.00",
        fullvalue: "0.00",
        totalamount: "0.00",
      };
      window.__pmLastTotals = lastTotals;
      paintCheckoutTotals(lastTotals, false);
      paintCheckoutLines(data || { items: [] }, false);
      '(function(){var _d=setTimeout(function(){applyInstallmentRules()},300)})();';
    } else if (data && data.items) {
      paintCheckoutLines(data, false);
    }
    syncLocalStorageFromWoo(data);
    renderCheckoutCart();
    return lastTotals;
  }

  function syncLocalStorageFromWoo(data) {
    try {
      var wooItems = (data && data.items) || [];
      var local = JSON.parse(localStorage.getItem("pm-cart-v1") || "[]");
      if (!Array.isArray(local)) local = [];
      if (local.length) {
        var byKey = {};
        wooItems.forEach(function (line) {
          if (line && line.key) byKey[String(line.key)] = line;
        });
        var next = [];
        local.forEach(function (item) {
          if (!item) return;
          if (item.wooKey && byKey[String(item.wooKey)]) {
            item.qty = byKey[String(item.wooKey)].quantity || item.qty;
            // Corrige preço de vitrine se o local ficou com R$ 1,00 de teste
            if (String(item.id || "").indexOf("body-splash") === 0) {
              item.priceCents = SPLASH_CENTS;
            } else if (isTestChargeCents(item.priceCents, item.id || item.name)) {
              var fix =
                (item.id && catalogByWooId[String(item.id)]) ||
                (item.variationId && catalogByWooId[String(item.variationId)]) ||
                (item.wooId && catalogByWooId[String(item.wooId)]) ||
                (item.productId && catalogByWooId[String(item.productId)]) ||
                0;
              if (fix > 0) item.priceCents = fix;
            }
            next.push(item);
          }
        });
        localStorage.setItem("pm-cart-v1", JSON.stringify(next));
      }
      var codes = (data.coupons || [])
        .map(function (c) {
          return String((c && (c.code || c)) || "").trim();
        })
        .filter(Boolean);
      localStorage.setItem("pm-coupon-v1", JSON.stringify(codes));
    } catch (error) {}
  }

  function wooRefresh(response) {
    var next = response.headers.get("Nonce");
    if (next) wooNonce = next;
    return response.json().then(function (data) {
      if (!response.ok) {
        var err = new Error("woo");
        err.payload = data;
        throw err;
      }
      return data;
    });
  }

  function wooGetCart() {
    return fetch("/wp-json/wc/store/v1/cart", { credentials: "same-origin" }).then(wooRefresh);
  }

  function wooPost(path, payload) {
    var run = function () {
      return fetch("/wp-json/wc/store/v1/cart/" + path, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          Nonce: wooNonce,
        },
        body: JSON.stringify(payload || {}),
      }).then(wooRefresh);
    };
    if (wooNonce) return run();
    return wooGetCart().then(function () {
      return run();
    });
  }

  function wooErrorMessage(error) {
    var payload = error && error.payload;
    if (payload && payload.message) return String(payload.message);
    if (payload && payload.data && payload.data.message) return String(payload.data.message);
    return "Não foi possível atualizar o carrinho. Tente de novo.";
  }

  function readSavedCoupons() {
    try {
      var raw = JSON.parse(localStorage.getItem("pm-coupon-v1") || "[]");
      return Array.isArray(raw)
        ? raw
            .map(function (c) {
              return String(c || "").trim();
            })
            .filter(Boolean)
        : [];
    } catch (error) {
      return [];
    }
  }

  function couponCodesFromCart(data) {
    return ((data && data.coupons) || [])
      .map(function (c) {
        return String((c && (c.code || c)) || "").trim();
      })
      .filter(Boolean);
  }

  /** Reaplica cupons salvos no localStorage se a sessão Woo perdeu o código. */
  function ensureCouponsOnCart(data) {
    var onCart = couponCodesFromCart(data).map(function (c) {
      return c.toLowerCase();
    });
    var missing = readSavedCoupons().filter(function (code) {
      return onCart.indexOf(String(code).toLowerCase()) === -1;
    });
    if (!missing.length) return Promise.resolve(data);
    return missing
      .reduce(function (chain, code) {
        return chain.then(function () {
          return wooPost("apply-coupon", { code: code }).catch(function () {
            return null;
          });
        });
      }, Promise.resolve())
      .then(function () {
        return wooGetCart();
      });
  }

  function syncCheckoutTotalsFromWoo() {
    return wooGetCart()
      .then(ensureCouponsOnCart)
      .then(function (data) {
        return applyCartSnapshot(data, { allowEmpty: false });
      })
      .catch(function () {
        return null;
      });
  }

  function isPayStepActive() {
    var tab = document.getElementById("pills-pagamento-tab");
    var pane = document.getElementById("pills-pagamento");
    if (tab && tab.classList.contains("active")) return true;
    if (pane && pane.classList.contains("active")) return true;
    if (pane && pane.classList.contains("show") && !pane.classList.contains("fade")) return true;
    return false;
  }

  function syncCheckoutStepClass() {
    var layout = document.getElementById("pm-checkout-layout");
    if (!layout) return;
    var pay = isPayStepActive();
    layout.classList.toggle("is-pay-step", pay);
    document.body.classList.toggle("pm-checkout-pay-step", pay);
    if (pay) {
      ensureInstallmentsUi();
      relocateConsentNearSubmit();
      enhanceSubmitButton();
    }
  }

  function widenCheckoutParents(fromNode) {
    var node = fromNode;
    var hops = 0;
    while (node && node !== document.body && hops < 12) {
      if (node.classList) {
        var cls = node.className || "";
        if (
          /\bcol-lg-8\b/.test(cls) ||
          /\bcol-md-8\b/.test(cls) ||
          /\bcol-8\b/.test(cls) ||
          (node.classList.contains("white") && node.querySelector && node.querySelector("#pills-tab"))
        ) {
          node.classList.add("pm-checkout-span");
        }
        if (node.classList.contains("container") || node.classList.contains("container-fluid")) {
          node.classList.add("pm-checkout-span-wrap");
        }
      }
      node = node.parentNode;
      hops += 1;
    }
  }

  function bindCheckoutStepWatcher() {
    if (window.__pmCheckoutStepBound) return;
    window.__pmCheckoutStepBound = true;
    document.addEventListener(
      "click",
      function (event) {
        var t = event.target;
        if (!t || !t.closest) return;
        if (t.closest("#pills-tab, #pills-dados-tab, #pills-pagamento-tab, a[href='#pills-pagamento'], a[href='#pills-dados']")) {
          window.setTimeout(syncCheckoutStepClass, 0);
          window.setTimeout(syncCheckoutStepClass, 200);
        }
      },
      true,
    );
    var tabRoot = document.getElementById("pills-tab") || document.getElementById("pills-tabContent");
    if (tabRoot && window.MutationObserver) {
      var mo = new MutationObserver(function () {
        syncCheckoutStepClass();
      });
      mo.observe(tabRoot, { attributes: true, subtree: true, attributeFilter: ["class", "aria-selected"] });
      var pane = document.getElementById("pills-pagamento");
      if (pane) mo.observe(pane, { attributes: true, attributeFilter: ["class"] });
      var dados = document.getElementById("pills-dados");
      if (dados) mo.observe(dados, { attributes: true, attributeFilter: ["class"] });
    }
    window.setInterval(syncCheckoutStepClass, 800);
  }

  function ensureCheckoutLayout() {
    if (document.getElementById("pm-checkout-layout")) {
      syncCheckoutStepClass();
      return document.getElementById("pm-checkout-cart");
    }
    var formRoot =
      document.querySelector(".wpcf7") ||
      document.querySelector("div.wpcf7") ||
      document.querySelector("form.wpcf7-form");
    if (!formRoot) return null;
    document.body.classList.add("pm-checkout-brand");
    widenCheckoutParents(formRoot);
    var layout = document.createElement("div");
    layout.id = "pm-checkout-layout";
    layout.className = "pm-checkout-layout";
    var cart = document.createElement("aside");
    cart.id = "pm-checkout-cart";
    cart.className = "pm-checkout-cart";
    cart.setAttribute("aria-live", "polite");
    var formCol = document.createElement("div");
    formCol.className = "pm-checkout-form-col";
    var parent = formRoot.parentNode;
    parent.insertBefore(layout, formRoot);
    layout.appendChild(cart);
    layout.appendChild(formCol);
    formCol.appendChild(formRoot);
    var legacy = document.getElementById("total");
    if (legacy) legacy.classList.add("pm-checkout-legacy-hidden");
    bindCheckoutStepWatcher();
    syncCheckoutStepClass();
    return cart;
  }

  function cartHasBodySplash(items) {
    return (items || []).some(function (line) {
      if (!line) return false;
      if (String(line.id) === "") return true;
      var name = decodeEntities(line.name || "").toLowerCase();
      return name.indexOf("body splash") >= 0;
    });
  }

  function bodySplashPickupNoteHtml() {
    return (
      '<p class="pm-checkout-pickup-note">' +
      "Body Splash: <strong>retirada na loja</strong>. Compra online com retirada na unidade Pello Menos escolhida — não enviamos pelos Correios." +
      "</p>"
    );
  }

  function syncBodySplashPayNote(hasSplash) {
    var pay = document.getElementById("pills-pagamento");
    if (!pay) return;
    var note = pay.querySelector(".pm-checkout-pickup-note--pay");
    if (!hasSplash) {
      if (note) note.remove();
      return;
    }
    if (!note) {
      note = document.createElement("p");
      note.className = "pm-checkout-pickup-note pm-checkout-pickup-note--pay";
      note.innerHTML =
        "Body Splash: <strong>retirada na loja</strong>. Compra online com retirada na unidade Pello Menos escolhida — não enviamos pelos Correios.";
      var consent = pay.querySelector(".pm-checkout-consent");
      var submit =
        pay.querySelector(".pm-checkout-submit, button.wpcf7-submit, input.wpcf7-submit") ||
        pay.querySelector(".wpcf7-form-control-wrap");
      var host = (consent && consent.parentNode) || (submit && submit.parentNode) || pay;
      if (consent && consent.parentNode) {
        consent.parentNode.insertBefore(note, consent);
      } else if (submit && submit.parentNode) {
        submit.parentNode.insertBefore(note, submit);
      } else {
        host.appendChild(note);
      }
    }
  }

  function renderCheckoutCart() {
    var cart = ensureCheckoutLayout();
    if (!cart) return;
    var data = lastCart || { items: [], coupons: [], totals: {} };
    var items = data.items || [];
    var totals = data.totals || {};
    var minor = totals.currency_minor_unit != null ? Number(totals.currency_minor_unit) : 2;
    var hasSplash = cartHasBodySplash(items);
    cart.classList.toggle("is-busy", cartBusy);
    syncCheckoutStepClass();
    syncBodySplashPayNote(hasSplash);

    if (!items.length) {
      cart.innerHTML =
        '<h2 class="pm-checkout-cart__title">Seu pedido</h2>' +
        '<p class="pm-checkout-cart__sub">Resumo na etapa de pagamento</p>' +
        '<div class="pm-checkout-empty">' +
        "<p>Seu carrinho está vazio.</p>" +
        '<a href="/carrinho/">Voltar ao carrinho</a>' +
        '<a href="/">Continuar comprando</a>' +
        "</div>" +
        '<p class="pm-checkout-cart__status' +
        (cartError ? " is-error" : "") +
        '">' +
        escapeHtml(cartError || cartStatus) +
        "</p>";
      return;
    }

    // Preços de vitrine: catálogo (cart-related) + pm-cart-v1.
    // Woo no ensaio fica a R$ 1,00 (cobrança de teste) — NÃO usar na UI.
    var localByKey = {};
    var localByWooId = {};
    var localItems = [];
    var campaignLines = [];
    try {
      var localCart = JSON.parse(localStorage.getItem("pm-cart-v1") || "[]");
      if (Array.isArray(localCart)) {
        localItems = localCart.filter(Boolean);
        localItems.forEach(function (item) {
          if (!item) return;
          var unit = Number(item.priceCents) || 0;
          if (String(item.id || "").indexOf("body-splash") === 0) unit = SPLASH_CENTS;
          if (isTestChargeCents(unit, item.id || item.name)) {
            var fix =
              (item.id && catalogByWooId[String(item.id)]) ||
              (item.variationId && catalogByWooId[String(item.variationId)]) ||
              (item.wooId && catalogByWooId[String(item.wooId)]) ||
              (item.productId && catalogByWooId[String(item.productId)]) ||
              0;
            if (fix > 0) unit = fix;
          }
          if (item.wooKey && unit > 0) localByKey[String(item.wooKey)] = unit;
          if (item.wooId && unit > 0) localByWooId[String(item.wooId)] = unit;
          var row = catalogById[String(item.id || "")];
          campaignLines.push({
            id: String(item.id || ""),
            method: (row && row.method) || item.method || null,
          });
        });
      }
    } catch (e) {}

    function pricedForLocal(item) {
      if (!item) return { sale: 0, list: 0 };
      if (String(item.id || "").indexOf("body-splash") === 0) {
        return { sale: SPLASH_CENTS, list: SPLASH_LIST_CENTS };
      }
      var row = catalogById[String(item.id || "")];
      if (window.pmBlackNov && window.pmBlackNov.ready && window.pmBlackNov.ready() && row) {
        var priced = window.pmBlackNov.unitPrice(row, campaignLines);
        if (priced && Number(priced.priceCents) > 0) {
          return {
            sale: Number(priced.priceCents),
            list: Number(priced.oldPriceCents) || Number(priced.priceCents),
          };
        }
      }
      if (row) {
        var sale = Number(row.priceCents) || 0;
        var list = Number(row.originalCents) || sale;
        return { sale: sale, list: list > 0 ? list : sale };
      }
      var fallback = Number(item.priceCents) || 0;
      return { sale: fallback, list: fallback };
    }

    function displayUnitCents(line) {
      var qty = Math.max(1, Number(line.quantity) || 1);
      var name = String(line.name || "").toLowerCase();
      var decoded = decodeEntities(line.name || "").toLowerCase();
      if (name.indexOf("body splash") !== -1 || name.indexOf("splash") !== -1) {
        return SPLASH_CENTS;
      }
      var wooId = line.id != null ? String(line.id) : "";
      var nameKey = decoded.replace(/\s+/g, " ").trim();
      var catId = lineCatalogId(line);
      // 1) pm-cart-v1 / catalog id: desambigua esfoliação vs cera no mesmo SKU Woo.
      if (line.key && localByKey[String(line.key)] > 0) {
        var localKey = localByKey[String(line.key)];
        if (!isTestChargeCents(localKey, nameKey)) return localKey;
      }
      if (catId && catalogById[catId]) {
        var catCents = Number(catalogById[catId].priceCents) || 0;
        if (catCents > 0 && !isTestChargeCents(catCents, catId)) return catCents;
      }
      if (wooId && localByWooId[wooId] > 0) {
        var localWoo = localByWooId[wooId];
        if (!isTestChargeCents(localWoo, nameKey)) return localWoo;
      }
      if (nameKey && catalogByName[nameKey] > 0) return catalogByName[nameKey];
      if (wooId && catalogByWooId[wooId] > 0) return catalogByWooId[wooId];
      var wooTotal =
        line.totals && line.totals.line_total != null
          ? Math.round(Number(line.totals.line_total) / qty)
          : 0;
      if (isTestChargeCents(wooTotal, nameKey) && catalogReady) {
        return (
          (catId && catalogById[catId] && Number(catalogById[catId].priceCents)) ||
          catalogByWooId[wooId] ||
          catalogByName[nameKey] ||
          wooTotal
        );
      }
      return wooTotal;
    }

    var listSubtotal = 0;
    var saleSubtotal = 0;
    var lines = items
      .map(function (line) {
        var img = resolveLineImage(line);
        var localMatch = matchLocalCartItem(line, localItems);
        var name = displayLineName(line, localMatch);
        var qty = line.quantity || 1;
        var unitCents = displayUnitCents(line);
        var listCents = unitCents;
        if (localMatch) {
          var priced = pricedForLocal(localMatch);
          if (priced.sale > 0) unitCents = priced.sale;
          if (priced.list > 0) listCents = priced.list;
        }
        var lineTotal = unitCents * qty;
        listSubtotal += listCents * qty;
        saleSubtotal += lineTotal;
        var priceHtml =
          listCents > unitCents && unitCents > 0
            ? '<span class="pm-checkout-line__list">' +
              moneyDisplay(listCents * qty, minor) +
              "</span> " +
              moneyDisplay(lineTotal, minor)
            : moneyDisplay(lineTotal, minor);
        return (
          '<li class="pm-checkout-line" data-pm-key="' +
          escapeHtml(line.key) +
          '">' +
          (img
            ? '<img class="pm-checkout-line__img" src="' + escapeHtml(img) + '" alt="">'
            : '<span class="pm-checkout-line__img" aria-hidden="true"></span>') +
          '<div><p class="pm-checkout-line__name">' +
          escapeHtml(name) +
          "</p>" +
          '<div class="pm-checkout-line__row">' +
          '<div class="pm-checkout-qty">' +
          '<button type="button" data-pm-qty-dec="' +
          escapeHtml(line.key) +
          '" aria-label="Diminuir"' +
          (cartBusy || qty <= 1 ? " disabled" : "") +
          ">−</button>" +
          "<span>" +
          qty +
          "</span>" +
          '<button type="button" data-pm-qty-inc="' +
          escapeHtml(line.key) +
          '" aria-label="Aumentar"' +
          (cartBusy ? " disabled" : "") +
          ">+</button></div>" +
          '<span class="pm-checkout-line__price">' +
          priceHtml +
          "</span></div>" +
          '<button type="button" class="pm-checkout-line__remove" data-pm-remove="' +
          escapeHtml(line.key) +
          '"' +
          (cartBusy ? " disabled" : "") +
          ">Remover</button></div></li>"
        );
      })
      .join("");

    // Desconto de vitrine: mesma regra do carrinho (nomes Esquenta / Black Week + cupom).
    var campaignSavings = Math.max(0, listSubtotal - saleSubtotal);
    var campaignLabel =
      window.pmBlackNov && window.pmBlackNov.discountLabel
        ? window.pmBlackNov.discountLabel()
        : null;
    if (!campaignLabel && campaignSavings > 0) {
      campaignLabel = "Desconto e-commerce (5%)";
    }
    var couponRule = couponRuleFromTotals(data);
    var couponBase = saleSubtotal;
    if (couponRule && couponRule.type === "target_total" && couponRule.catalogIds) {
      var allowed = {};
      (couponRule.catalogIds || []).forEach(function (id) {
        allowed[String(id)] = true;
      });
      couponBase = 0;
      localItems.forEach(function (it) {
        if (!allowed[String(it.id)]) return;
        var priced = pricedForLocal(it);
        couponBase += (priced.sale > 0 ? priced.sale : Number(it.priceCents) || 0) * (it.qty || 0);
      });
    }
    var displayDiscount = displayDiscountCents(couponRule, couponBase);
    var couponCodeShort = (function (code, maxLen) {
      var s = String(code || "").toUpperCase();
      var lim = maxLen || 10;
      if (s.length <= lim) return s;
      return s.slice(0, lim) + "...";
    })(couponRule && couponRule.code, 10);
    var couponLabel = couponRule
      ? couponRule.percent > 0
        ? "Desconto (" +
          escapeHtml(couponCodeShort) +
          " · " +
          String(couponRule.percent).replace(".", ",") +
          "%)"
        : "Desconto (" + escapeHtml(couponCodeShort) + ")"
      : "Desconto";
    var displaySubtotal = listSubtotal > 0 ? listSubtotal : saleSubtotal;
    var displayTotal = Math.max(0, saleSubtotal - displayDiscount);

    cart.innerHTML =
      '<h2 class="pm-checkout-cart__title">Seu pedido</h2>' +
      '<p class="pm-checkout-cart__sub">' +
      items.length +
      (items.length === 1 ? " item" : " itens") +
      "</p>" +
      '<ul class="pm-checkout-cart__list">' +
      lines +
      "</ul>" +
      (hasSplash ? bodySplashPickupNoteHtml() : "") +
      '<div class="pm-checkout-cart__totals">' +
      "<div><span>Subtotal</span><span>" +
      moneyDisplay(displaySubtotal, minor) +
      "</span></div>" +
      (campaignSavings > 0 && campaignLabel
        ? "<div><span>" +
          escapeHtml(campaignLabel) +
          "</span><span>−" +
          moneyDisplay(campaignSavings, minor) +
          "</span></div>"
        : "") +
      (displayDiscount > 0
        ? "<div><span>" +
          couponLabel +
          "</span><span>−" +
          moneyDisplay(displayDiscount, minor) +
          "</span></div>"
        : "") +
      '<div class="is-total"><span>Total</span><span>' +
      moneyDisplay(displayTotal, minor) +
      "</span></div></div>" +
      '<p class="pm-checkout-cart__status' +
      (cartError ? " is-error" : "") +
      '">' +
      escapeHtml(cartError || cartStatus) +
      "</p>";

    bindCartPanelEvents(cart);
  }

  function runCartMutation(promise, okMsg) {
    if (cartBusy) return;
    cartBusy = true;
    cartError = "";
    cartStatus = "Atualizando…";
    renderCheckoutCart();
    return promise
      .then(function (data) {
        cartBusy = false;
        cartError = "";
        cartStatus = okMsg || "Atualizado";
        applyCartSnapshot(data, { allowEmpty: true });
        window.setTimeout(function () {
          if (cartStatus === okMsg) {
            cartStatus = "";
            renderCheckoutCart();
          }
        }, 1600);
        return data;
      })
      .catch(function (error) {
        cartBusy = false;
        cartError = wooErrorMessage(error);
        cartStatus = "";
        return wooGetCart()
          .then(function (data) {
            applyCartSnapshot(data, { allowEmpty: true });
          })
          .catch(function () {
            renderCheckoutCart();
          });
      });
  }

  function bindCartPanelEvents(cart) {
    cart.querySelectorAll("[data-pm-qty-dec]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var key = btn.getAttribute("data-pm-qty-dec");
        var line = (lastCart && lastCart.items || []).filter(function (i) {
          return i.key === key;
        })[0];
        if (!line || (line.quantity || 1) <= 1) return;
        runCartMutation(wooPost("update-item", { key: key, quantity: (line.quantity || 1) - 1 }), "Quantidade atualizada");
      });
    });
    cart.querySelectorAll("[data-pm-qty-inc]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var key = btn.getAttribute("data-pm-qty-inc");
        var line = (lastCart && lastCart.items || []).filter(function (i) {
          return i.key === key;
        })[0];
        if (!line) return;
        runCartMutation(wooPost("update-item", { key: key, quantity: (line.quantity || 1) + 1 }), "Quantidade atualizada");
      });
    });
    cart.querySelectorAll("[data-pm-remove]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var key = btn.getAttribute("data-pm-remove");
        if (!key) return;
        runCartMutation(wooPost("remove-item", { key: key }), "Item removido");
      });
    });
  }

  function scheduleCheckoutSync() {
    if (window.__pmShellSyncStarted) return;
    window.__pmShellSyncStarted = true;
    window.__pmShellSync = syncCheckoutTotalsFromWoo;
    ensureCheckoutLayout();
    bindSubmitCartSync();
    loadCatalogPrices().finally(function () {
      syncCheckoutTotalsFromWoo();
      if (lastCart) renderCheckoutCart();
    });
    window.setInterval(function () {
      if (cartBusy) return;
      if (lastTotals) paintCheckoutTotals(lastTotals, false);
      if (lastCart) paintCheckoutLines(lastCart, false);
      syncCheckoutTotalsFromWoo();
    }, 400);
    document.addEventListener(
      "focusin",
      function () {
        if (lastTotals) paintCheckoutTotals(lastTotals, false);
        if (lastCart) paintCheckoutLines(lastCart, false);
      },
      true,
    );
  }

  function waitWhileCartBusy(maxMs) {
    var limit = maxMs == null ? 8000 : maxMs;
    var started = Date.now();
    return new Promise(function (resolve) {
      function tick() {
        if (!cartBusy || Date.now() - started >= limit) {
          resolve(!cartBusy);
          return;
        }
        window.setTimeout(tick, 50);
      }
      tick();
    });
  }

  function syncCartFieldsBeforeSubmit() {
    var hadItems =
      (lastCart && lastCart.items && lastCart.items.length) ||
      (lastTotals && lastTotals.totalamount && lastTotals.totalamount !== "0.00");
    return waitWhileCartBusy(8000).then(function () {
      return wooGetCart()
        .then(ensureCouponsOnCart)
        .then(function (data) {
          var items = (data && data.items) || [];
          // Nunca zerar hiddens no submit se a sessão Woo veio vazia por race/rede.
          if (!items.length && hadItems) {
            if (lastCart) paintCheckoutLines(lastCart, false);
            if (lastTotals) paintCheckoutTotals(lastTotals, false);
            return data;
          }
          applyCartSnapshot(data, { allowEmpty: false });
          return data;
        });
    });
  }

  function loadingApi() {
    return window.pmCheckoutLoading || null;
  }

  function clearLoadingFailsafe() {
    if (loadingFailsafeTimer) {
      window.clearTimeout(loadingFailsafeTimer);
      loadingFailsafeTimer = null;
    }
  }

  function armLoadingFailsafe() {
    clearLoadingFailsafe();
    // Se CF7/Accesstage não responder, libera a UI (sem falso "aprovado").
    loadingFailsafeTimer = window.setTimeout(function () {
      loadingFailsafeTimer = null;
      if (loadingApi() && loadingApi().isActive && loadingApi().isActive()) {
        closeCheckoutLoading();
      }
    }, 90000);
  }

  function openCheckoutLoading() {
    var api = loadingApi();
    if (!api || typeof api.open !== "function") return;
    try {
      api.open({ items: (lastCart && lastCart.items) || [] });
      armLoadingFailsafe();
    } catch (e) {}
  }

  function setCheckoutLoadingState(next) {
    var api = loadingApi();
    if (!api || typeof api.setState !== "function") return;
    try {
      api.setState(next);
      if (next === "confirmed" || next === "error" || next === "idle") {
        clearLoadingFailsafe();
      }
    } catch (e) {}
  }

  function unlockCheckoutSubmit() {
    document.querySelectorAll("button.pm-checkout-submit, input.wpcf7-submit, button.wpcf7-submit").forEach(function (el) {
      el.disabled = false;
      el.removeAttribute("data-pm-cart-synced");
      el.__pmSyncingSubmit = false;
      try {
        el.style.pointerEvents = "";
        el.style.display = "";
      } catch (e) {}
    });
  }

  function closeCheckoutLoading() {
    clearLoadingFailsafe();
    var api = loadingApi();
    if (api) {
      try {
        if (typeof api.close === "function") api.close();
        else if (typeof api.setState === "function") api.setState("error");
      } catch (e) {}
    }
    unlockCheckoutSubmit();
  }

  function bindCheckoutLoadingEvents() {
    if (window.__pmCheckoutLoadingBound) return;
    window.__pmCheckoutLoadingBound = true;
    document.addEventListener("wpcf7submit", function () {
      if (!loadingApi() || !loadingApi().isActive || !loadingApi().isActive()) return;
      setCheckoutLoadingState("paying");
    });
    document.addEventListener("wpcf7mailsent", function () {
      setCheckoutLoadingState("confirmed");
      clearLoadingFailsafe();
      // Redirect fica no JS inline do tema (cookie redirectSuccess).
    });
    document.addEventListener("wpcf7invalid", function () {
      closeCheckoutLoading();
      // Mantém a cliente na etapa Pagamento (sensação de "voltou ao início").
      try {
        var payTab = document.getElementById("pills-pagamento-tab");
        if (payTab && typeof payTab.click === "function") payTab.click();
        syncCheckoutStepClass();
      } catch (e) {}
      window.setTimeout(function () {
        var bad = document.querySelector(
          "#pills-pagamento .wpcf7-not-valid, #pills-dados .wpcf7-not-valid, .wpcf7-not-valid",
        );
        if (bad && bad.scrollIntoView) {
          bad.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 80);
    });
    document.addEventListener("wpcf7spam", function () {
      closeCheckoutLoading();
    });
    document.addEventListener("wpcf7mailfailed", function () {
      closeCheckoutLoading();
    });
  }

  function redispatchCheckoutSubmit(btn) {
    btn.setAttribute("data-pm-cart-synced", "1");
    // Botão disabled NÃO dispara click()/submit — precisa estar habilitado no re-envio.
    btn.disabled = false;
    try {
      btn.style.pointerEvents = "";
      btn.style.display = "";
    } catch (e) {}
    try {
      btn.click();
    } catch (error) {
      btn.removeAttribute("data-pm-cart-synced");
      btn.disabled = false;
      closeCheckoutLoading();
      return;
    }
    // Anti double-submit: overlay (isActive) + disabled após o dispatch.
    window.setTimeout(function () {
      if (loadingApi() && loadingApi().isActive && loadingApi().isActive()) {
        btn.disabled = true;
      }
    }, 0);
  }

  function bindSubmitCartSync() {
    if (window.__pmSubmitCartSyncBound) return;
    window.__pmSubmitCartSyncBound = true;
    bindCheckoutLoadingEvents();
    document.addEventListener(
      "click",
      function (event) {
        var btn = event.target && event.target.closest
          ? event.target.closest("button.pm-checkout-submit, input.wpcf7-submit, button.wpcf7-submit")
          : null;
        if (!btn || !btn.closest || !btn.closest(".wpcf7-form, .wpcf7")) return;
        if (btn.getAttribute("data-pm-cart-synced") === "1") {
          btn.removeAttribute("data-pm-cart-synced");
          // Segundo clique (após sync): overlay já aberto; CF7 segue.
          return;
        }
        event.preventDefault();
        event.stopImmediatePropagation();
        if (btn.__pmSyncingSubmit) return;
        var api = loadingApi();
        if (api && api.isActive && api.isActive()) return;
        btn.__pmSyncingSubmit = true;
        btn.disabled = true;
        openCheckoutLoading();
        syncCartFieldsBeforeSubmit()
          .catch(function () {})
          .then(function () {
            setCheckoutLoadingState("preparing");
            btn.__pmSyncingSubmit = false;
            redispatchCheckoutSubmit(btn);
          });
      },
      true,
    );
  }

  function bindRemoveSameOrigin() {
    if (!window.jQuery) return;
    var $ = window.jQuery;
    $(".removeitem").off("click");
    $(document).off("click", ".removeitem");
    $(document).off("click.pmSameOrigin", ".removeitem");
    $(document).on("click.pmSameOrigin", ".removeitem", function (event) {
      event.preventDefault();
      event.stopImmediatePropagation();
      // Prefer Store API panel path when we know the cart
      var productId = $(this).data("id");
      var match = null;
      if (lastCart && lastCart.items) {
        match = lastCart.items.filter(function (line) {
          return String(line.id) === String(productId);
        })[0];
      }
      if (match && match.key) {
        runCartMutation(wooPost("remove-item", { key: match.key }), "Item removido");
        return;
      }
      $.ajax({
        type: "GET",
        url: "/wp-admin/admin-ajax.php",
        data: { action: "removeitemcartpl", productid: productId },
        beforeSend: function () {
          cartStatus = "Atualizando…";
          renderCheckoutCart();
        },
        success: function () {
          window.location.href = "/finalizar-pagamento/";
        },
      });
    });
  }

  function scheduleRemoveSameOrigin() {
    bindRemoveSameOrigin();
    window.setTimeout(bindRemoveSameOrigin, 400);
    window.setTimeout(bindRemoveSameOrigin, 1200);
  }

  function revealGroup(el) {
    if (!el) return;
    el.style.setProperty("display", "block", "important");
    el.classList.remove("wpcf7cf-hidden", "wpcf7cf_group_hidden");
    el.removeAttribute("hidden");
    el.hidden = false;
  }

  function groupVisible(el) {
    if (!el) return false;
    var cs = window.getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden") return false;
    return el.offsetHeight > 0 || el.getClientRects().length > 0;
  }

  var MIN_INSTALLMENT_ORDER = 180;
  var MIN_INSTALLMENT_PARCEL = 50;

  function checkoutTotalMajor() {
    var raw =
      (lastTotals && lastTotals.totalamount) ||
      (window.__pmLastTotals && window.__pmLastTotals.totalamount) ||
      "";
    if (!raw) {
      var el =
        document.querySelector('input[name="totalamount"]') ||
        document.querySelector('[name="totalamount"]');
      raw = el ? el.value : "";
    }
    var n = parseFloat(String(raw).replace(/\s/g, "").replace(",", "."));
    return isFinite(n) ? n : 0;
  }

  function parseInstallmentTimes(value) {
    var m = String(value || "").match(/(\d+)/);
    return m ? parseInt(m[1], 10) : 0;
  }

  function rememberInstallmentOptions(sel) {
    if (!sel || sel.getAttribute("data-pm-inst-opts") === "1") return;
    var snap = [];
    Array.prototype.forEach.call(sel.options || [], function (opt) {
      snap.push({
        value: opt.value,
        text: opt.text,
        disabled: !!opt.disabled,
      });
    });
    try {
      sel.setAttribute("data-pm-inst-snap", JSON.stringify(snap));
      sel.setAttribute("data-pm-inst-opts", "1");
    } catch (e) {}
  }

  function restoreInstallmentOptions(sel) {
    var raw = sel.getAttribute("data-pm-inst-snap");
    if (!raw) return;
    var snap;
    try {
      snap = JSON.parse(raw);
    } catch (e) {
      return;
    }
    if (!Array.isArray(snap) || !snap.length) return;
    var prev = String(sel.value || "");
    sel.innerHTML = "";
    snap.forEach(function (item) {
      var opt = document.createElement("option");
      opt.value = item.value;
      opt.textContent = item.text;
      if (item.disabled) opt.disabled = true;
      sel.appendChild(opt);
    });
    if (prev) sel.value = prev;
  }

  function installmentSnap(sel) {
    rememberInstallmentOptions(sel);
    var raw = sel.getAttribute("data-pm-inst-snap");
    if (!raw) return [];
    try {
      return JSON.parse(raw) || [];
    } catch (e) {
      return [];
    }
  }

  function maxInstallmentTimesForSelect(sel, totalMajor) {
    var snap = installmentSnap(sel);
    var selectCap = 1;
    snap.forEach(function (item) {
      var n = parseInstallmentTimes(item.value);
      if (n > selectCap) selectCap = n;
    });
    if (totalMajor + 1e-9 < MIN_INSTALLMENT_ORDER) return 1;
    var byFloor = Math.max(1, Math.floor(totalMajor / MIN_INSTALLMENT_PARCEL + 1e-9));
    return Math.min(selectCap, byFloor);
  }

  function setInstallmentUiVisible(sel, visible) {
    var wrap = sel.closest(".wpcf7-form-control-wrap") || sel.parentNode;
    var host = wrap && wrap.parentNode ? wrap.parentNode : null;
    var label = host ? host.querySelector(".pm-checkout-installments-label") : null;
    if (visible) {
      if (sel.getAttribute("data-pm-inst-ui-hidden") !== "1") return;
      sel.removeAttribute("data-pm-inst-ui-hidden");
      if (label) label.style.display = "";
      if (wrap) wrap.style.display = "";
      sel.style.display = "";
      return;
    }
    // Só esconde se o grupo do CF7 estiver visível (não briga com conditional fields).
    var group =
      sel.closest('[data-id="nosubscribe"]') ||
      sel.closest('[data-id="productcera"]') ||
      sel.closest('[data-id="subscribe"]') ||
      host;
    if (group && !groupVisible(group) && sel.getAttribute("data-pm-inst-ui-hidden") !== "1") {
      return;
    }
    sel.setAttribute("data-pm-inst-ui-hidden", "1");
    if (label) label.style.display = "none";
    if (wrap) wrap.style.display = "none";
    else sel.style.display = "none";
  }

  function filterInstallmentSelect(sel, totalMajor) {
    if (!sel) return;
    var snap = installmentSnap(sel);
    if (!snap.length) {
      rememberInstallmentOptions(sel);
      snap = installmentSnap(sel);
    }
    var maxTimes = maxInstallmentTimesForSelect(sel, totalMajor);
    var prev = String(sel.value || "");
    var prevN = parseInstallmentTimes(prev);
    var keep = snap.filter(function (item) {
      var n = parseInstallmentTimes(item.value);
      return n >= 1 && n <= maxTimes;
    });
    if (!keep.length) {
      keep = snap.filter(function (item) {
        return parseInstallmentTimes(item.value) === 1;
      });
      maxTimes = 1;
    }
    sel.innerHTML = "";
    keep.forEach(function (item) {
      var opt = document.createElement("option");
      opt.value = item.value;
      opt.textContent = item.text;
      if (item.disabled) opt.disabled = true;
      sel.appendChild(opt);
    });
    var allowed = keep.some(function (item) {
      return String(item.value) === prev;
    });
    if (allowed) {
      sel.value = prev;
    } else {
      var one = keep.filter(function (item) {
        return parseInstallmentTimes(item.value) === 1;
      })[0];
      sel.value = one ? one.value : keep[0] ? keep[0].value : "";
      if (prevN > 1) {
        sel.dispatchEvent(new Event("change", { bubbles: true }));
        sel.dispatchEvent(new Event("input", { bubbles: true }));
      }
    }
    // < R$ 180 (ou só 1x): some o select. >= 180 com 2+ opções: aparece com N options corretas.
    setInstallmentUiVisible(sel, maxTimes > 1);
  }

  // Debounce helper - only run function after user stops typing
  function debounce(func, wait) {
    let timeout;
    return function() {
      const context = this;
      const args = arguments;
      clearTimeout(timeout);
      timeout = setTimeout(function() {
        func.apply(context, args);
      }, wait);
    };
  }

  function applyInstallmentRules() {
    var total = checkoutTotalMajor();
    ["allinstallments", "cerainstallments", "installments"].forEach(function (name) {
      var sel = document.querySelector('select[name="' + name + '"]');
      if (!sel) return;
      ensureInstallmentsLabel(sel);
      filterInstallmentSelect(sel, total);
    });
  }

  function ensureInstallmentsUi() {
    // siteinstallment NÃO é o número de parcelas: é o marcador de "compra avulsa"
    // (1) vs "assinatura" (0) que controla os grupos condicionais nosubscribe/subscribe.
    // O payment_CF7 não lê este campo. Mantê-lo em "1" é o comportamento correto.
    var site = document.querySelector('input[name="siteinstallment"]');
    if (site && String(site.value || "") !== "1") {
      site.value = "1";
      site.dispatchEvent(new Event("change", { bubbles: true }));
      site.dispatchEvent(new Event("input", { bubbles: true }));
    }
    var nosub = document.querySelector('[data-id="nosubscribe"]');
    var sub = document.querySelector('[data-id="subscribe"]');
    var cera = document.querySelector('[data-id="productcera"]');
    if (!groupVisible(nosub) && !groupVisible(sub) && !groupVisible(cera)) {
      revealGroup(nosub || cera || sub);
    }
    ["allinstallments", "cerainstallments", "installments"].forEach(function (name) {
      var sel = document.querySelector('select[name="' + name + '"]');
      if (!sel) return;
      var hasOne = Array.prototype.some.call(sel.options || [], function (opt) {
        return String(opt.value) === "1x";
      });
      if (hasOne && (!sel.value || sel.value === "")) {
        sel.value = "1x";
        sel.dispatchEvent(new Event("change", { bubbles: true }));
        sel.dispatchEvent(new Event("input", { bubbles: true }));
      }
      ensureInstallmentsLabel(sel);
    });
    '(function(){var _d=setTimeout(function(){applyInstallmentRules()},300)})();';
  }

  function ensureInstallmentsLabel(sel) {
    if (!sel || sel.getAttribute("data-pm-labeled") === "1") return;
    var wrap = sel.closest(".wpcf7-form-control-wrap") || sel.parentNode;
    var host = wrap && wrap.parentNode ? wrap.parentNode : null;
    if (!host) return;
    if (host.querySelector(".pm-checkout-installments-label")) {
      sel.setAttribute("data-pm-labeled", "1");
      return;
    }
    var label = document.createElement("label");
    label.className = "pm-checkout-installments-label";
    label.setAttribute("for", sel.id || "");
    if (!sel.id) {
      sel.id = "pm-ck-" + (sel.getAttribute("name") || "installments");
      label.setAttribute("for", sel.id);
    }
    label.textContent = "Número de parcelas";
    host.insertBefore(label, wrap);
    sel.setAttribute("data-pm-labeled", "1");
  }

  function relocateConsentNearSubmit() {
    var wrap = document.querySelector('.wpcf7-form-control-wrap[data-name="declaracao"]');
    var submit =
      document.querySelector("button.wpcf7-submit, input.wpcf7-submit") ||
      document.querySelector(".wpcf7-submit");
    if (!wrap || !submit || wrap.getAttribute("data-pm-moved") === "1") return;
    var block = wrap.closest("p") || wrap.parentNode;
    var submitHost = submit.closest("p") || submit.parentNode;
    if (!block || !submitHost || !submitHost.parentNode) return;
    var pay = document.getElementById("pills-pagamento");
    if (pay && !pay.contains(submitHost)) return;
    submitHost.parentNode.insertBefore(block, submitHost);
    block.classList.add("pm-checkout-consent");
    wrap.setAttribute("data-pm-moved", "1");
  }

  function enhanceSubmitButton() {
    var input = document.querySelector("input.wpcf7-submit");
    if (!input || input.getAttribute("data-pm-enhanced") === "1") return;
    if (document.querySelector("button.pm-checkout-submit")) return;
    var btn = document.createElement("button");
    btn.type = "submit";
    btn.className = (input.className || "wpcf7-form-control wpcf7-submit") + " pm-checkout-submit";
    btn.setAttribute("data-pm-enhanced", "1");
    btn.innerHTML =
      '<span class="pm-checkout-submit__label">Finalizar Pagamento</span>' +
      '<span class="pm-checkout-submit__icon" aria-hidden="true">' +
      '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
      '<circle cx="9" cy="20" r="1.5"></circle><circle cx="18" cy="20" r="1.5"></circle>' +
      '<path d="M3 4h2l2.2 11h10.3l1.8-7H7.1"></path>' +
      "</svg></span>";
    input.setAttribute("data-pm-enhanced", "1");
    input.parentNode.replaceChild(btn, input);
  }

  function hidePageCheckoutHeading() {
    document.querySelectorAll("h1, h2").forEach(function (node) {
      var text = String(node.textContent || "").replace(/\s+/g, " ").trim();
      if (/^finalizar pagamento$/i.test(text)) {
        node.classList.add("pm-checkout-page-heading");
        node.setAttribute("hidden", "hidden");
        node.setAttribute("aria-hidden", "true");
      }
    });
  }

  function ensureStepCardTitles() {
    var dados = document.getElementById("pills-dados");
    if (dados && !dados.querySelector(".pm-checkout-step-title")) {
      var title = document.createElement("h3");
      title.className = "pm-checkout-step-title text-center";
      title.textContent = "Dados Pessoais";
      dados.insertBefore(title, dados.firstChild);
    }
    var payTitle = document.querySelector("#pills-pagamento > h3");
    if (payTitle) payTitle.classList.add("pm-checkout-step-title");

    var iconUser =
      '<svg class="pm-ck-tab-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>';
    var iconCard =
      '<svg class="pm-ck-tab-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/></svg>';
    var iconBuy =
      '<svg class="pm-ck-tab-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M3 4h2l2.2 11h10.3l1.8-7H7.1"/></svg>';

    var dadosTab = document.getElementById("pills-dados-tab");
    var payTab = document.getElementById("pills-pagamento-tab");
    if (dadosTab && !dadosTab.getAttribute("data-pm-label")) {
      dadosTab.setAttribute("data-pm-label", "1");
      dadosTab.innerHTML = iconUser + "<span>Dados</span>";
    }
    if (payTab && !payTab.getAttribute("data-pm-label")) {
      payTab.setAttribute("data-pm-label", "1");
      payTab.innerHTML = iconCard + "<span>Pagamento</span>";
    }

    document.querySelectorAll("a.btnNext, .btnNext, a.btn.btn-primary.btnNext").forEach(function (btn) {
      if (btn.getAttribute("data-pm-buy") === "1") return;
      btn.setAttribute("data-pm-buy", "1");
      btn.classList.add("pm-checkout-buy-now");
      btn.innerHTML = "<span>Comprar Agora</span>" + iconBuy;
    });
  }

  function isRequiredOnlyTip(text) {
    var t = String(text || "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
    if (!t) return true;
    if (/(e-?mail|@|inválid|invalid|formato|n[uú]mero|cep|cpf|telefone|curto|longo|digite um|please enter)/i.test(t)) {
      return false;
    }
    return (
      /campo (é|e) obrigat/.test(t) ||
      /obrigat[oó]rio/.test(t) ||
      t === "this field is required." ||
      t === "please fill out this field."
    );
  }

  function polishValidationTips() {
    document.querySelectorAll(".wpcf7-not-valid-tip").forEach(function (tip) {
      // Tips genéricos de obrigatório: esconde o texto repetido, mas marca o wrap
      // para a cliente ver qual campo falhou (caso Beatriz: "carrega e volta").
      var hide = isRequiredOnlyTip(tip.textContent);
      tip.classList.toggle("pm-ck-tip-show", !hide);
      if (hide) {
        tip.setAttribute("aria-hidden", "true");
      } else {
        tip.removeAttribute("aria-hidden");
      }
      var wrap = tip.closest(".wpcf7-form-control-wrap, .form-group, p, div");
      if (wrap) wrap.classList.add("pm-ck-field-invalid");
    });
    document.querySelectorAll(".wpcf7-not-valid").forEach(function (el) {
      var wrap = el.closest(".wpcf7-form-control-wrap, .form-group, p, div");
      if (wrap) wrap.classList.add("pm-ck-field-invalid");
    });
  }

  function bindValidationPolish() {
    if (window.__pmValidationPolishBound) return;
    window.__pmValidationPolishBound = true;
    document.addEventListener("wpcf7invalid", function () {
      window.setTimeout(polishValidationTips, 0);
      window.setTimeout(polishValidationTips, 200);
    });
    document.addEventListener("wpcf7submit", function () {
      window.setTimeout(polishValidationTips, 0);
    });
    if (window.MutationObserver) {
      var form = document.querySelector(".wpcf7-form");
      if (form) {
        var mo = new MutationObserver(function () {
          polishValidationTips();
        });
        mo.observe(form, { childList: true, subtree: true, characterData: true });
      }
    }
  }

  function polishCheckoutFormUi() {
    hidePageCheckoutHeading();
    ensureStepCardTitles();
    relocateConsentNearSubmit();
    enhanceSubmitButton();
    bindSubmitCartSync();
    bindValidationPolish();
    polishValidationTips();
    if (isPayStepActive()) ensureInstallmentsUi();
  }

  function scheduleFormPolish() {
    polishCheckoutFormUi();
    window.setTimeout(polishCheckoutFormUi, 400);
    window.setTimeout(polishCheckoutFormUi, 1200);
    window.setInterval(function () {
      if (isPayStepActive()) ensureInstallmentsUi();
    }, 1200);
  }

  // ---------------------------------------------------------------------------
  // Carrinho abandonado (plugin Cart Abandonment Recovery for WooCommerce).
  // O checkout é um formulário CF7, então o script do plugin não roda aqui;
  // o snippet "pm-wcar" injeta window.pmWcar (ajaxurl + nonces) e nós enviamos
  // os dados para o mesmo endpoint que o plugin usa no checkout nativo.
  //
  // v2 (30/10): captura "pre-submit" de e-mail, nome, telefone, CPF, unidade e
  // endereço assim que a cliente digita (debounce), identidade persistente em
  // localStorage (pm-identity-v1) para reconhecer quem volta, lead parcial sem
  // e-mail (tabela própria, para follow-up por WhatsApp) e pré-preenchimento do
  // formulário com a identidade salva / da conta logada / do link do e-mail.
  // ---------------------------------------------------------------------------
  var WCAR_IDENTITY_KEY = "pm-identity-v1";
  var wcarTimer = null;
  var wcarCartTimer = null;
  var wcarLastPayload = "";
  var wcarLastLeadPayload = "";
  var wcarLastCartSig = null;
  var wcarPrefilled = false;

  function wcarCartSignature() {
    if (!lastCart) return "";
    var sig = (lastCart.items || [])
      .map(function (line) { return line.key + ":" + line.quantity; })
      .join(",");
    if (lastCart.totals) sig += "|" + (lastCart.totals.total_price || "");
    return sig;
  }

  function wcarConfig() {
    var cfg = window.pmWcar;
    return cfg && cfg.nonce && cfg.ajaxurl ? cfg : null;
  }

  function wcarValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(value || "").trim());
  }

  function wcarDigits(value) {
    return String(value || "").replace(/\D+/g, "");
  }

  function wcarFieldEl(name) {
    return document.querySelector('.wpcf7-form [name="' + name + '"]');
  }

  function wcarField(name) {
    var el = wcarFieldEl(name);
    if (!el) return "";
    if (el.tagName === "SELECT") {
      var opt = el.options[el.selectedIndex];
      var text = opt ? String(opt.textContent || "").trim() : "";
      var val = String(el.value || "").trim();
      return val ? (text || val) : "";
    }
    return String(el.value || "").trim();
  }

  function wcarUnitFromCart() {
    try {
      var local = JSON.parse(localStorage.getItem("pm-cart-v1") || "[]");
      if (Array.isArray(local) && local.length && local[0].unitName) {
        var first = local[0];
        return [first.unitName, first.city, first.stateName].filter(Boolean).join(" · ");
      }
    } catch (e) {}
    return "";
  }

  function wcarRandomId() {
    var chars = "abcdefghijklmnopqrstuvwxyz0123456789";
    var out = "";
    for (var i = 0; i < 20; i++) out += chars.charAt(Math.floor(Math.random() * chars.length));
    return out;
  }

  function wcarReadIdentity() {
    try {
      var raw = JSON.parse(localStorage.getItem(WCAR_IDENTITY_KEY) || "null");
      return raw && typeof raw === "object" ? raw : null;
    } catch (e) {
      return null;
    }
  }

  function wcarWriteIdentity(patch) {
    var current = wcarReadIdentity() || {};
    var next = {};
    Object.keys(current).forEach(function (k) { next[k] = current[k]; });
    Object.keys(patch || {}).forEach(function (k) {
      var v = patch[k];
      if (v == null) return;
      v = String(v).trim();
      if (v) next[k] = v;
    });
    if (!next.leadId) next.leadId = wcarRandomId();
    next.updatedAt = new Date().toISOString();
    try {
      localStorage.setItem(WCAR_IDENTITY_KEY, JSON.stringify(next));
      // Cookie de 1 ano só com o id aleatório (sem dado pessoal), para o servidor
      // reconhecer o mesmo navegador entre sessões do Woo.
      document.cookie = "pm_lead_id=" + encodeURIComponent(next.leadId) + "; path=/; max-age=31536000; SameSite=Lax";
    } catch (e) {}
    return next;
  }

  // Lê o formulário e devolve o que a cliente já digitou (sem validar).
  function wcarCollectForm() {
    var fullName = wcarField("your-name");
    var street = wcarField("endereco");
    var number = wcarField("numero");
    var unit = wcarField("unit") || wcarField("easyunit") || wcarUnitFromCart();
    return {
      email: wcarField("your-email"),
      name: fullName,
      phone: wcarField("your-phone"),
      cpf: wcarDigits(wcarField("cpf")),
      unit: unit,
      city: wcarField("cidade"),
      state: wcarField("estado"),
      cep: wcarField("cep"),
      address1: street + (street && number ? ", " + number : number),
      address2: [wcarField("bairro"), wcarField("complemento")].filter(Boolean).join(" · "),
    };
  }

  function wcarPost(cfg, data) {
    var body = new URLSearchParams();
    Object.keys(data).forEach(function (k) {
      body.append(k, data[k] == null ? "" : String(data[k]));
    });
    return fetch(cfg.ajaxurl, { method: "POST", credentials: "same-origin", body: body }).catch(function () {});
  }

  // Envia para o plugin (exige e-mail válido) — cria/atualiza a linha do carrinho abandonado.
  function wcarCapturePlugin(cfg, form, identity) {
    var email = wcarValidEmail(form.email) ? form.email : (wcarValidEmail(identity.email) ? identity.email : "");
    if (!email) return false;
    var parts = String(form.name || identity.name || "").split(/\s+/).filter(Boolean);
    var first = parts.shift() || "";
    var last = parts.join(" ");
    var data = {
      action: "cartflows_save_cart_abandonment_data",
      security: cfg.nonce,
      wcf_post_id: cfg.postId || 0,
      wcf_email: email,
      wcf_phone: form.phone || identity.phone || "",
      wcf_name: first,
      wcf_surname: last,
      wcf_city: form.city || identity.city || "",
      wcf_billing_state: form.state || identity.state || "",
      wcf_billing_postcode: form.cep || identity.cep || "",
      wcf_billing_address_1: form.address1 || identity.address1 || "",
      wcf_billing_address_2: form.address2 || identity.address2 || "",
      wcf_country: "BR",
      // Campos extras lidos pelo snippet pm-wcar (filtro wcar_cart_default_other_fields).
      pm_cpf: form.cpf || identity.cpf || "",
      pm_unidade: form.unit || identity.unit || "",
      pm_lead_id: identity.leadId || "",
      pm_source: "checkout",
    };
    var cartSig = wcarCartSignature();
    var key = JSON.stringify(data) + "|" + cartSig;
    if (key === wcarLastPayload) return true;
    wcarLastPayload = key;
    wcarLastCartSig = cartSig;
    wcarPost(cfg, data);
    return true;
  }

  // Lead parcial (sem e-mail): nome / telefone / CPF / unidade digitados.
  function wcarCaptureLead(cfg, form, identity) {
    if (!cfg.leadNonce) return;
    var has = form.name || form.phone || form.cpf || identity.name || identity.phone || identity.cpf;
    if (!has) return;
    var data = {
      action: "pm_lead_save",
      security: cfg.leadNonce,
      lead_id: identity.leadId || "",
      name: form.name || identity.name || "",
      phone: form.phone || identity.phone || "",
      cpf: form.cpf || identity.cpf || "",
      unit: form.unit || identity.unit || "",
      email: wcarValidEmail(form.email) ? form.email : (wcarValidEmail(identity.email) ? identity.email : ""),
      city: form.city || identity.city || "",
      state: form.state || identity.state || "",
      page: window.location.pathname,
      cart: wcarCartSignature(),
    };
    var key = JSON.stringify(data);
    if (key === wcarLastLeadPayload) return;
    wcarLastLeadPayload = key;
    wcarPost(cfg, data);
  }

  function wcarCapture() {
    var cfg = wcarConfig();
    if (!cfg) return;
    var form = wcarCollectForm();
    var identity = wcarWriteIdentity({
      email: wcarValidEmail(form.email) ? form.email : null,
      name: form.name,
      phone: form.phone,
      cpf: form.cpf,
      unit: form.unit,
      city: form.city,
      state: form.state,
      cep: form.cep,
      address1: form.address1,
      address2: form.address2,
    });
    var sent = wcarCapturePlugin(cfg, form, identity);
    // Sempre registra o lead (com ou sem e-mail) — a equipe vê quem parou no meio.
    wcarCaptureLead(cfg, form, identity);
    return sent;
  }

  function wcarSchedule() {
    if (!wcarConfig()) return;
    window.clearTimeout(wcarTimer);
    wcarTimer = window.setTimeout(wcarCapture, 1200);
  }

  // O shell consulta o carrinho do Woo com frequência; só reenvia quando o conteúdo mudou
  // de fato desde a última captura (timer próprio, para não zerar o debounce dos campos).
  function wcarOnCartUpdated() {
    if (!wcarConfig() || wcarLastCartSig === null) return;
    if (wcarCartSignature() === wcarLastCartSig) return;
    window.clearTimeout(wcarCartTimer);
    wcarCartTimer = window.setTimeout(wcarCapture, 1500);
  }

  // Pré-preenche o formulário com a identidade conhecida: localStorage, conta logada
  // (cfg.user) ou linha restaurada pelo link do e-mail (cfg.restored). Nunca sobrescreve
  // o que a cliente já digitou.
  function wcarPrefill() {
    var cfg = wcarConfig();
    if (!cfg || wcarPrefilled) return;
    var email = wcarFieldEl("your-email");
    if (!email) return;
    wcarPrefilled = true;
    var saved = wcarReadIdentity() || {};
    var known = {};
    [cfg.user, cfg.restored, saved].forEach(function (src) {
      if (!src) return;
      Object.keys(src).forEach(function (k) {
        if (!known[k] && src[k]) known[k] = src[k];
      });
    });
    if (cfg.restored || cfg.user) wcarWriteIdentity(known);
    var map = {
      "your-email": known.email,
      "your-name": known.name,
      "your-phone": known.phone,
      cpf: known.cpf,
      cep: known.cep,
      cidade: known.city,
      estado: known.state,
    };
    var changed = false;
    Object.keys(map).forEach(function (name) {
      var el = wcarFieldEl(name);
      if (!el || !map[name] || el.value) return;
      el.value = map[name];
      changed = true;
      try { el.dispatchEvent(new Event("input", { bubbles: true })); } catch (e) {}
      try { el.dispatchEvent(new Event("change", { bubbles: true })); } catch (e) {}
    });
    if (changed || known.email) wcarSchedule();
  }

  function bindWcarCapture() {
    if (!wcarConfig() || window.__pmWcarBound) return;
    window.__pmWcarBound = true;
    var watched = {
      "your-email": 1, "your-phone": 1, "your-name": 1, cpf: 1, unit: 1, easyunit: 1,
      cidade: 1, estado: 1, cep: 1, endereco: 1, numero: 1, bairro: 1, complemento: 1,
    };
    function onFieldEvent(event) {
      var t = event.target;
      if (!t || !t.getAttribute || !watched[t.getAttribute("name")]) return;
      if (!t.closest || !t.closest(".wpcf7-form")) return;
      wcarSchedule();
    }
    // Captura enquanto digita (input) e ao sair do campo (blur/change) — "pre-submit tracking".
    document.addEventListener("input", onFieldEvent, true);
    document.addEventListener("change", onFieldEvent, true);
    document.addEventListener("blur", onFieldEvent, true);
    // Carrinho mudou (cupom, remover item): reenvia para o plugin guardar o conteúdo atual.
    document.addEventListener("pm:cart-updated", wcarOnCartUpdated);
    // Saída da página: última tentativa com o que estiver no formulário.
    window.addEventListener("pagehide", function () {
      try { wcarCapture(); } catch (e) {}
    });
    wcarPrefill();
    window.setTimeout(wcarPrefill, 800);
    window.setTimeout(wcarPrefill, 2000);
    window.setTimeout(wcarCapture, 1500);
  }

  fetch(base + "checkout-header.html?v=shell3")
    .then(function (response) { return response.text(); })
    .then(function (html) { place("pm-shell-header", html); });
  fetch(base + "checkout-footer.html?v=shell2")
    .then(function (response) { return response.text(); })
    .then(function (html) { place("pm-shell-footer", html); });

  scheduleCheckoutSync();
  scheduleRemoveSameOrigin();
  scheduleFormPolish();
  bindWcarCapture();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleCheckoutSync);
    document.addEventListener("DOMContentLoaded", scheduleRemoveSameOrigin);
    document.addEventListener("DOMContentLoaded", scheduleFormPolish);
    document.addEventListener("DOMContentLoaded", bindWcarCapture);
  }
  window.addEventListener("load", scheduleCheckoutSync);
  window.addEventListener("load", scheduleRemoveSameOrigin);
  window.addEventListener("load", scheduleFormPolish);
  window.addEventListener("load", bindWcarCapture);
})();
