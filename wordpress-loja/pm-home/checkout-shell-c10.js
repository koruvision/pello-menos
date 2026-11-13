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
    if (host.shadowRoot) return;
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

  function paintCheckoutTotals(values, notify) {
    if (!values) return;
    setField("cupom", values.cupom, notify);
    setField("cupomamount", values.cupomamount, notify);
    setField("fullvalue", values.fullvalue, notify);
    setField("totalamount", values.totalamount, notify);
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
    } else if (opts && opts.allowEmpty) {
      lastTotals = {
        cupom: "",
        cupomamount: "0.00",
        fullvalue: "0.00",
        totalamount: "0.00",
      };
      window.__pmLastTotals = lastTotals;
      paintCheckoutTotals(lastTotals, false);
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

  function syncCheckoutTotalsFromWoo() {
    return wooGetCart()
      .then(function (data) {
        return applyCartSnapshot(data, { allowEmpty: false });
      })
      .catch(function () {
        return null;
      });
  }

  function ensureCheckoutLayout() {
    if (document.getElementById("pm-checkout-layout")) return document.getElementById("pm-checkout-cart");
    var formRoot =
      document.querySelector(".wpcf7") ||
      document.querySelector("div.wpcf7") ||
      document.querySelector("form.wpcf7-form");
    if (!formRoot) return null;
    document.body.classList.add("pm-checkout-brand");
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
    return cart;
  }

  function renderCheckoutCart() {
    var cart = ensureCheckoutLayout();
    if (!cart) return;
    var data = lastCart || { items: [], coupons: [], totals: {} };
    var items = data.items || [];
    var totals = data.totals || {};
    var minor = totals.currency_minor_unit != null ? Number(totals.currency_minor_unit) : 2;
    var coupons = (data.coupons || [])
      .map(function (c) {
        return String((c && (c.code || c)) || "").trim();
      })
      .filter(Boolean);

    cart.classList.toggle("is-busy", cartBusy);

    if (!items.length) {
      cart.innerHTML =
        '<h2 class="pm-checkout-cart__title">Seu pedido</h2>' +
        '<p class="pm-checkout-cart__sub">Resumo atualizado pela sessão WooCommerce</p>' +
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

    var lines = items
      .map(function (line) {
        var img =
          (line.images && line.images[0] && (line.images[0].thumbnail || line.images[0].src)) ||
          "";
        var name = decodeEntities(line.name || "Item");
        var qty = line.quantity || 1;
        var lineTotal = line.totals && line.totals.line_total != null ? line.totals.line_total : 0;
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
          moneyDisplay(lineTotal, minor) +
          "</span></div>" +
          '<button type="button" class="pm-checkout-line__remove" data-pm-remove="' +
          escapeHtml(line.key) +
          '"' +
          (cartBusy ? " disabled" : "") +
          ">Remover</button></div></li>"
        );
      })
      .join("");

    var couponList = coupons
      .map(function (code) {
        return (
          "<li><span>" +
          escapeHtml(code) +
          '</span><button type="button" data-pm-coupon-remove="' +
          escapeHtml(code) +
          '"' +
          (cartBusy ? " disabled" : "") +
          ">Remover</button></li>"
        );
      })
      .join("");

    cart.innerHTML =
      '<h2 class="pm-checkout-cart__title">Seu pedido</h2>' +
      '<p class="pm-checkout-cart__sub">' +
      items.length +
      (items.length === 1 ? " item" : " itens") +
      "</p>" +
      '<ul class="pm-checkout-cart__list">' +
      lines +
      "</ul>" +
      '<div class="pm-checkout-cart__totals">' +
      "<div><span>Subtotal</span><span>" +
      moneyDisplay(totals.total_items || 0, minor) +
      "</span></div>" +
      (Number(totals.total_discount || 0) > 0
        ? "<div><span>Desconto</span><span>−" +
          moneyDisplay(totals.total_discount || 0, minor) +
          "</span></div>"
        : "") +
      '<div class="is-total"><span>Total</span><span>' +
      moneyDisplay(totals.total_price || 0, minor) +
      "</span></div></div>" +
      '<div class="pm-checkout-coupon" data-pm-coupon>' +
      '<p style="margin:0;font-size:0.85rem;font-weight:700">Cupom</p>' +
      '<form data-pm-coupon-form>' +
      '<input data-pm-coupon-input type="text" autocomplete="off" placeholder="Código do cupom"' +
      (cartBusy ? " disabled" : "") +
      ">" +
      '<button type="submit"' +
      (cartBusy ? " disabled" : "") +
      ">" +
      (cartBusy ? "…" : "Aplicar") +
      "</button></form>" +
      (cartError && cartError.indexOf("upom") >= 0
        ? '<p class="pm-checkout-coupon__err">' + escapeHtml(cartError) + "</p>"
        : "") +
      (couponList ? '<ul class="pm-checkout-coupon__list">' + couponList + "</ul>" : "") +
      "</div>" +
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
    var form = cart.querySelector("[data-pm-coupon-form]");
    if (form) {
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        var input = cart.querySelector("[data-pm-coupon-input]");
        var code = input ? String(input.value || "").trim() : "";
        if (!code) {
          cartError = "Digite o código do cupom.";
          renderCheckoutCart();
          return;
        }
        runCartMutation(wooPost("apply-coupon", { code: code }), "Cupom aplicado").then(function () {
          if (input) input.value = "";
        });
      });
    }
    cart.querySelectorAll("[data-pm-coupon-remove]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var code = btn.getAttribute("data-pm-coupon-remove");
        if (!code) return;
        runCartMutation(wooPost("remove-coupon", { code: code }), "Cupom removido");
      });
    });
  }

  function scheduleCheckoutSync() {
    if (window.__pmShellSyncStarted) return;
    window.__pmShellSyncStarted = true;
    window.__pmShellSync = syncCheckoutTotalsFromWoo;
    ensureCheckoutLayout();
    syncCheckoutTotalsFromWoo();
    window.setInterval(function () {
      if (cartBusy) return;
      if (lastTotals) paintCheckoutTotals(lastTotals, false);
      syncCheckoutTotalsFromWoo();
    }, 400);
    document.addEventListener(
      "focusin",
      function () {
        if (lastTotals) paintCheckoutTotals(lastTotals, false);
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

  fetch(base + "checkout-header.html?v=shell2")
    .then(function (response) { return response.text(); })
    .then(function (html) { place("pm-shell-header", html); });
  fetch(base + "checkout-footer.html?v=shell2")
    .then(function (response) { return response.text(); })
    .then(function (html) { place("pm-shell-footer", html); });

  scheduleCheckoutSync();
  scheduleRemoveSameOrigin();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleCheckoutSync);
    document.addEventListener("DOMContentLoaded", scheduleRemoveSameOrigin);
  }
  window.addEventListener("load", scheduleCheckoutSync);
  window.addEventListener("load", scheduleRemoveSameOrigin);
})();
