(function () {
  var KEY = "pm-cart-v1";
  var SPLASH = {
    id: "body-splash-livre",
    name: "Body Splash - Livre",
    duration: "Uso diário",
    sku: "PM-BODY-SPLASH-LIVRE",
    // Mesma imagem da ficha do produto (catalogImage("body-splash")); resolvida via mediaBase.
    image: "/images/products/body-splash.webp?v=0d57e0d3",
    priceCents: 8161,
    wooId: "",
    // Lançamento 01/12: até lá o Body Splash fica "em produção" — sem upsell e fora das sugestões.
    // Espelha BODY_SPLASH_FOR_SALE em src/lib/data.ts; trocar para true ao liberar a venda.
    forSale: false,
  };
  var relatedData = { crossSell: {}, products: {} };
  var affinityData = null; // combinacoes reais de compra (cart-affinity.json)
  var relatedReady = false;
  var root = document.querySelector("[data-pm-cart-page]");
  if (!root) return;
  var mediaBase =
    (window.location && window.location.origin ? window.location.origin : "") +
    "/wp-content/uploads/pm-home/media";
  var payError = "";
  var payBusy = false;
  var couponError = "";
  var couponBusy = false;
  var railResizeBound = false;
  var wooSnapshot = null; // { coupons: string[], subtotal, discount, total }
  var BAG_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-shopping-bag shrink-0" aria-hidden="true"><path d="M16 10a4 4 0 0 1-8 0"></path><path d="M3.103 6.034h17.794"></path><path d="M3.4 5.467a2 2 0 0 0-.4 1.2V20a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6.667a2 2 0 0 0-.4-1.2l-2-2.667A2 2 0 0 0 17 2H7a2 2 0 0 0-1.6.8z"></path></svg>';
  var CART_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-shopping-cart shrink-0" aria-hidden="true"><circle cx="8" cy="21" r="1"></circle><circle cx="19" cy="21" r="1"></circle><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"></path></svg>';
  var SPINNER_SVG =
    '<svg data-pm-cart-spinner class="h-4 w-4 shrink-0 animate-spin" viewBox="0 0 24 24" aria-hidden="true" fill="none">' +
    '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-opacity="0.25" stroke-width="3"></circle>' +
    '<path d="M22 12a10 10 0 0 1-10 10" stroke="currentColor" stroke-width="3" stroke-linecap="round"></path>' +
    "</svg>";
  function btnBusyHtml(label) {
    return SPINNER_SVG + '<span>' + label + "</span>";
  }
  function btnBagHtml(label) {
    return BAG_SVG + "<span>" + label + "</span>";
  }
  function btnPayHtml() {
    return CART_SVG + "<span>Ir para o pagamento</span>";
  }
  var LOCK_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="18" height="11" x="3" y="11" rx="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>';
  var ARROW_L_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6"></path></svg>';
  var ARROW_R_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6"></path></svg>';

  function readCart() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "[]");
    } catch (error) {
      return [];
    }
  }

  function readCoupons() {
    if (window.pmWoo && window.pmWoo.readSavedCoupons) return window.pmWoo.readSavedCoupons();
    try {
      var raw = JSON.parse(localStorage.getItem("pm-coupon-v1") || "[]");
      return Array.isArray(raw) ? raw.filter(Boolean) : [];
    } catch (error) {
      return [];
    }
  }

  function saveCoupons(codes) {
    if (window.pmWoo && window.pmWoo.writeSavedCoupons) {
      return window.pmWoo.writeSavedCoupons(codes);
    }
    localStorage.setItem("pm-coupon-v1", JSON.stringify(codes || []));
    return codes || [];
  }

  function isBodySplash(item) {
    return String((item && item.id) || "").indexOf("body-splash") === 0;
  }

  /**
   * Preços de vitrine vêm do catálogo (cart-related / preço gravado na PDP).
   * No ensaio o Woo podia cobrar valor de teste — NÃO sobrescrever com a Store API.
   * Body Splash permanece em SPLASH.priceCents (R$ 81,61 — de R$ 85,90 com 5% OFF).
   */
  function isIntentionalOneReal(item) {
    var id = String((item && item.id) || "");
    return id === "produto-1-real" || id.indexOf("1-real") !== -1;
  }

  function isTestChargeCents(cents, item) {
    var c = Number(cents) || 0;
    if (c !== 100) return false;
    return !isIntentionalOneReal(item);
  }

  function catalogRowFor(item) {
    if (!item || !relatedData || !relatedData.products) return null;
    var products = relatedData.products;
    var byId = products[String(item.id || "")];
    if (byId) return byId;
    var want = [
      String(item.wooId || ""),
      String(item.variationId || ""),
      String(item.productId || ""),
    ].filter(Boolean);
    if (!want.length) return null;
    var keys = Object.keys(products);
    for (var i = 0; i < keys.length; i++) {
      var row = products[keys[i]];
      if (!row) continue;
      if (want.indexOf(String(row.wooId || "")) !== -1) return row;
      if (want.indexOf(String(row.productId || "")) !== -1) return row;
      var units = row.units || {};
      var uids = Object.keys(units);
      for (var u = 0; u < uids.length; u++) {
        var meta = units[uids[u]];
        if (meta && want.indexOf(String(meta.variationId || "")) !== -1) return row;
      }
    }
    return null;
  }

  function cartLinesForCampaign(items) {
    return (items || readCart()).map(function (it) {
      var row = catalogRowFor(it);
      return {
        id: String((it && it.id) || ""),
        method: (row && row.method) || (it && it.method) || null,
      };
    });
  }

  function catalogPriced(item) {
    if (!item) return { priceCents: 0, oldPriceCents: 0 };
    if (isBodySplash(item)) {
      return { priceCents: SPLASH.priceCents, oldPriceCents: 8590 };
    }
    var row = catalogRowFor(item);
    // Campanha (Esquenta/Black): pmBlackNov.unitPrice usa SEMPRE originalCents (tabela)
    // e aplica a % uma única vez. Nunca reaplicar desconto sobre row.priceCents
    // (que na vitrine já pode vir com a taxa "any" baked no cart-related.json).
    if (window.pmBlackNov && window.pmBlackNov.ready && window.pmBlackNov.ready() && row) {
      var priced = window.pmBlackNov.unitPrice(row, cartLinesForCampaign());
      if (priced && Number(priced.priceCents) > 0) {
        return {
          priceCents: Number(priced.priceCents),
          oldPriceCents: Number(priced.oldPriceCents) || Number(priced.priceCents),
        };
      }
    }
    if (row) {
      var sale = Number(row.priceCents) || 0;
      var list = Number(row.originalCents) || sale;
      if (sale > 0) return { priceCents: sale, oldPriceCents: list > 0 ? list : sale };
    }
    var local = Number(item.priceCents) || 0;
    if (isTestChargeCents(local, item)) return { priceCents: 0, oldPriceCents: 0 };
    return { priceCents: local, oldPriceCents: local };
  }

  function catalogUnitCents(item) {
    return catalogPriced(item).priceCents;
  }

  function syncLocalPricesFromCatalog() {
    var items = readCart();
    if (!items.length) return items;
    var changed = false;
    var next = items.map(function (item) {
      var unit = catalogUnitCents(item);
      if (unit > 0 && unit !== Number(item.priceCents)) {
        changed = true;
        return Object.assign({}, item, { priceCents: unit });
      }
      return item;
    });
    if (changed) {
      localStorage.setItem(KEY, JSON.stringify(next));
      paintBadge(next);
    }
    return next;
  }

  function applyWooSnapshot(data) {
    if (!data) {
      wooSnapshot = null;
      return;
    }
    var totals =
      window.pmWoo && window.pmWoo.totalsCents
        ? window.pmWoo.totalsCents(data)
        : { subtotal: 0, discount: 0, total: 0 };
    var coupons =
      window.pmWoo && window.pmWoo.couponCodesFromCart
        ? window.pmWoo.couponCodesFromCart(data)
        : [];
    // Regra do cupom (percentual/valor) — o desconto exibido é recalculado sobre o
    // subtotal de vitrine a cada render (add/remove/qty), não copiado do Woo.
    var rule =
      window.pmWoo && window.pmWoo.couponRuleFromCart
        ? window.pmWoo.couponRuleFromCart(data)
        : null;
    wooSnapshot = {
      coupons: coupons,
      subtotal: totals.subtotal,
      discount: totals.discount,
      total: totals.total,
      rule: rule,
    };
    saveCoupons(coupons);
    // Cupons/qty via Woo; preços de exibição pelo catálogo
    syncLocalPricesFromCatalog();
  }

  function refreshWooSnapshot() {
    if (!window.pmWoo || !window.pmWoo.getCart) {
      wooSnapshot = null;
      return Promise.resolve(null);
    }
    return window.pmWoo
      .getCart()
      .then(function (data) {
        applyWooSnapshot(data);
        return data;
      })
      .catch(function () {
        return null;
      });
  }

  var FIRST_PURCHASE_COUPON = "PRIMEIRACOMPRA5";
  var FIRST_PURCHASE_USED_MESSAGE =
    "Este cupom vale só para a primeira compra. Você já comprou na Pello Menos, então ele não se aplica.";

  function wooErrorMessage(error, code) {
    var payload = error && error.payload;
    var raw = payload && payload.message ? String(payload.message) : "";
    if (
      String(code || "").trim().toUpperCase() === FIRST_PURCHASE_COUPON &&
      /limite|limit|j\u00e1 (foi )?(usad|utilizad)|already/i.test(raw)
    ) {
      return FIRST_PURCHASE_USED_MESSAGE;
    }
    if (/n\u00e3o existe|does not exist|inv\u00e1lido|invalid/i.test(raw)) {
      return "Cupom não encontrado. Confira o código e tente de novo.";
    }
    if (payload) {
      if (payload.message) return String(payload.message);
      if (payload.data && payload.data.details) {
        try {
          var keys = Object.keys(payload.data.details);
          if (keys.length && payload.data.details[keys[0]].message) {
            return String(payload.data.details[keys[0]].message);
          }
        } catch (e) {}
      }
    }
    return "Não foi possível aplicar este cupom.";
  }

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

  function paintBadge(items) {
    if (window.pmPaintCart) {
      window.pmPaintCart(items);
      return;
    }
    var total = items.reduce(function (sum, item) {
      return sum + (item.qty || 0);
    }, 0);
    document.querySelectorAll('a[href="/carrinho/"], a[href="/carrinho"]').forEach(function (link) {
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

  function writeCart(items) {
    localStorage.setItem(KEY, JSON.stringify(items));
    paintBadge(items);
    render();
  }

  function money(cents) {
    return (cents / 100).toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /** Cupom longo no resumo: corta e coloca "..." (ex.: PM1L47SQ9A…). */
  function shortCouponCode(code, maxLen) {
    var s = String(code || "").toUpperCase();
    var lim = maxLen || 10;
    if (s.length <= lim) return s;
    return s.slice(0, lim) + "...";
  }

  var SHELL =
    "mx-auto flex min-h-[100dvh] w-full max-w-xl flex-col items-center justify-center px-container-margin py-10 text-center";

  function paintLoading() {
    root.setAttribute("data-pm-cart-state", "loading");
    root.className = SHELL;
    root.innerHTML =
      '<style>@keyframes pm-cart-spin{to{transform:rotate(360deg)}}</style>' +
      '<span class="block h-11 w-11 rounded-full border-[3px] border-primary/20 border-t-primary" style="animation:pm-cart-spin 0.75s linear infinite" aria-hidden="true"></span>' +
      '<p class="mt-5 text-sm text-on-surface-variant" role="status">Carregando carrinho…</p>';
  }

  function render() {
    var items = readCart();
    paintBadge(items);
    if (!items.length) {
      root.setAttribute("data-pm-cart-state", "empty");
      root.className = SHELL;
      root.innerHTML =
        '<span class="flex h-20 w-20 items-center justify-center rounded-full bg-surface-container-low text-primary md:h-24 md:w-24">' +
        '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="9" cy="20" r="1"/><circle cx="18" cy="20" r="1"/><path d="M3 4h2l2.2 11.2a2 2 0 0 0 2 1.6h7.7a2 2 0 0 0 2-1.6L21 8H7"/></svg></span>' +
        '<h1 class="mt-6 w-full max-w-md px-2 font-[family-name:var(--font-display)] text-headline-md leading-snug text-primary md:text-headline-lg">Seu carrinho está vazio</h1>' +
        '<p class="mt-3 max-w-sm text-body-md text-on-surface-variant md:max-w-md md:text-body-lg">Escolha um serviço na home para montar o pedido.</p>' +
        '<a href="/" class="btn-lux btn-lux-primary mt-8 inline-flex items-center gap-2 rounded-full px-8 py-3 font-label-md text-label-md text-on-primary uppercase md:mt-10 md:px-10 md:py-3.5">Ver produtos</a>';
      return;
    }
    root.setAttribute("data-pm-cart-state", "ready");

    var totalQty = items.reduce(function (sum, item) {
      return sum + item.qty;
    }, 0);
    // Soma das linhas pelo catálogo (Woo no ensaio fica a R$ 1,00)
    var listSubtotal = 0;
    var saleSubtotal = 0;
    items.forEach(function (item) {
      var priced = catalogPriced(item);
      var sale = priced.priceCents;
      if (!sale) sale = isBodySplash(item) ? SPLASH.priceCents : Number(item.priceCents) || 0;
      var list = priced.oldPriceCents > 0 ? priced.oldPriceCents : sale;
      var qty = item.qty || 0;
      listSubtotal += list * qty;
      saleSubtotal += sale * qty;
    });
    var campaignSavings = Math.max(0, listSubtotal - saleSubtotal);
    var campaignLabel =
      window.pmBlackNov && window.pmBlackNov.discountLabel
        ? window.pmBlackNov.discountLabel()
        : null;
    if (!campaignLabel && campaignSavings > 0) {
      campaignLabel = "Desconto e-commerce (5%)";
    }
    var couponRule = wooSnapshot ? wooSnapshot.rule : null;
    // PM1L / target_total: desconto so nas linhas elegiveis (buco-linha → liquido R$1).
    var couponBase = saleSubtotal;
    if (couponRule && couponRule.type === "target_total" && couponRule.catalogIds) {
      var allowed = {};
      (couponRule.catalogIds || []).forEach(function (id) {
        allowed[String(id)] = true;
      });
      couponBase = 0;
      items.forEach(function (item) {
        if (!allowed[String(item.id)]) return;
        var priced = catalogPriced(item);
        var sale = priced.priceCents;
        if (!sale) sale = isBodySplash(item) ? SPLASH.priceCents : Number(item.priceCents) || 0;
        couponBase += sale * (item.qty || 0);
      });
    }
    var couponDiscount =
      couponRule && window.pmWoo && window.pmWoo.displayDiscountCents
        ? window.pmWoo.displayDiscountCents(couponRule, couponBase)
        : 0;
    var couponLabel = couponRule
      ? couponRule.percent > 0
        ? "Desconto (" +
          escapeHtml(shortCouponCode(couponRule.code)) +
          " · " +
          String(couponRule.percent).replace(".", ",") +
          "%)"
        : "Desconto (" + escapeHtml(shortCouponCode(couponRule.code)) + ")"
      : "Desconto";
    var subtotal = listSubtotal > 0 ? listSubtotal : saleSubtotal;
    var total = Math.max(0, saleSubtotal - couponDiscount);
    var appliedCoupons =
      (wooSnapshot && wooSnapshot.coupons && wooSnapshot.coupons.length
        ? wooSnapshot.coupons
        : readCoupons()) || [];
    var unit = items[0];
    var mixed = items.some(function (item) {
      return item.unitId !== unit.unitId;
    });
    var canPay = !mixed;
    var cards = items
      .map(function (item) {
        var pricedCard = catalogPriced(item);
        var saleCard = pricedCard.priceCents;
        if (!saleCard) saleCard = isBodySplash(item) ? SPLASH.priceCents : Number(item.priceCents) || 0;
        var listCard = pricedCard.oldPriceCents;
        var priceHtml =
          listCard > saleCard && saleCard > 0
            ? '<span class="pm-line__old">' +
              money(listCard) +
              "</span> <span>" +
              money(saleCard) +
              "</span>"
            : money(saleCard);
        return (
          '<article class="pm-line" data-line="' +
          escapeHtml(item.lineId) +
          '"><a href="/produto/' +
          escapeHtml(item.id) +
          '/" class="pm-line__media"><img src="' +
          escapeHtml(productImageUrl(item.image)) +
          '" alt="" width="76" height="96" decoding="async"></a><div class="pm-line__body"><div class="pm-line__top"><div class="min-w-0"><a href="/produto/' +
          escapeHtml(item.id) +
          '/"><h2 class="pm-line__name">' +
          escapeHtml(item.name) +
          '</h2></a><p class="pm-line__unit">Unidade: ' +
          escapeHtml(item.unitName) +
          " · " +
          escapeHtml(item.city) +
          "/" +
          escapeHtml(item.stateName) +
          '</p><p class="pm-line__sku">SKU ' +
          escapeHtml(item.sku) +
          (item.duration ? " · " + escapeHtml(item.duration) : "") +
          '</p></div><button type="button" data-remove="' +
          escapeHtml(item.lineId) +
          '" class="pm-line__remove" aria-label="Remover">×</button></div><div class="pm-line__foot"><p class="pm-line__price">' +
          priceHtml +
          '</p><div class="pm-line__qty"><button type="button" data-dec="' +
          escapeHtml(item.lineId) +
          '" aria-label="Diminuir">−</button><span>' +
          item.qty +
          '</span><button type="button" data-inc="' +
          escapeHtml(item.lineId) +
          '" aria-label="Aumentar">+</button></div></div></div></article>'
        );
      })
      .join("");

    var blackHints = [];
    if (window.pmBlackNov && window.pmBlackNov.multiHint) {
      var linesCamp = cartLinesForCampaign(items);
      ["laser", "cera_esf"].forEach(function (fam) {
        var hint = window.pmBlackNov.multiHint(linesCamp, fam);
        if (hint && hint.need > 0) {
          blackHints.push(
            "Adicione mais " +
              hint.need +
              (hint.need === 1 ? " área diferente" : " áreas diferentes") +
              " de " +
              hint.label +
              " para liberar " +
              Math.round(hint.nextRate * 100) +
              "% OFF.",
          );
        }
      });
    }
    var blackHintHtml = blackHints.length
      ? '<p class="mt-3 rounded-xl bg-surface-container-low px-4 py-3 text-sm text-on-surface" data-pm-black-hint>' +
        blackHints.map(escapeHtml).join("<br>") +
        "</p>"
      : "";

    root.className = "pm-cart-main mx-auto w-full max-w-6xl px-container-margin pt-6 md:pt-10";
    root.innerHTML =
      '<header class="pm-cart-head">' +
      '<p class="pm-cart-head__eyebrow">Pedido</p>' +
      '<div class="pm-cart-head__row">' +
      '<h1 class="pm-cart-head__title">Carrinho</h1>' +
      '<span class="pm-cart-head__count">' +
      totalQty +
      (totalQty === 1 ? " item" : " itens") +
      "</span></div>" +
      '<p class="pm-cart-head__unit">Unidade: ' +
      escapeHtml(unit.unitName) +
      " · " +
      escapeHtml(unit.city) +
      "/" +
      escapeHtml(unit.stateName) +
      "</p></header>" +
      (mixed
        ? '<p class="pm-cart-mixed">Há serviços de unidades diferentes. Esvazie o carrinho ou mantenha só uma loja para finalizar.</p>'
        : "") +
      blackHintHtml +
      '<div class="pm-cart-grid mt-6"><div class="space-y-3 md:space-y-4">' +
      cards +
      relatedUpsellHtml(items, unit) +
      '</div><aside class="pm-cart-summary h-fit"><h2 class="pm-cart-summary__title">Resumo</h2>' +
      '<div class="mt-4 space-y-2 text-sm"><div class="flex justify-between"><span class="text-on-surface-variant">Subtotal</span><span class="font-semibold">' +
      money(subtotal) +
      "</span></div>" +
      (campaignSavings > 0 && campaignLabel
        ? '<div class="flex justify-between text-primary"><span>' +
          escapeHtml(campaignLabel) +
          '</span><span class="font-semibold">−' +
          money(campaignSavings) +
          "</span></div>"
        : "") +
      (couponDiscount > 0
        ? '<div class="flex justify-between gap-3 text-primary"><span class="min-w-0 truncate">' +
          couponLabel +
          '</span><span class="shrink-0 font-semibold">−' +
          money(couponDiscount) +
          "</span></div>"
        : "") +
      '</div><div class="mt-4 flex items-center justify-between border-t border-outline/40 pt-4"><span class="font-semibold">Total</span><span class="pm-cart-summary__total">' +
      money(total) +
      "</span></div>" +
      couponHtml(appliedCoupons) +
      '<button type="button" data-clear class="mt-3 w-full text-sm text-primary underline">Esvaziar carrinho</button>' +
      '<a href="/" class="pm-cart-summary__continue">Continuar comprando</a>' +
      upsellHtml(items, unit) +
      (payError
        ? '<p class="mt-3 rounded-2xl border border-primary/30 bg-surface-container-low px-3 py-3 text-center text-xs text-primary" data-pm-pay-error>' +
          escapeHtml(payError) +
          "</p>"
        : "") +
      '<div class="pm-pay-inline">' +
      (canPay
        ? '<a href="/finalizar-pagamento/" class="btn-lux btn-lux-gold pm-pay-btn' +
          (payBusy ? " is-busy" : "") +
          '" aria-busy="' +
          (payBusy ? "true" : "false") +
          '">' +
          (payBusy ? btnBusyHtml("carregando") : btnPayHtml()) +
          "</a>"
        : '<p class="pm-cart-note">Mantenha só uma unidade para ir ao pagamento.</p>') +
      "</div></aside></div>" +
      (canPay
        ? '<div class="pm-paybar" data-pm-paybar role="region" aria-label="Finalizar compra"><div class="pm-paybar__inner">' +
          '<div class="pm-paybar__total"><span>Total</span><strong>' +
          money(total) +
          "</strong></div>" +
          '<a href="/finalizar-pagamento/" class="btn-lux btn-lux-gold pm-paybar__btn' +
          (payBusy ? " is-busy" : "") +
          '" aria-busy="' +
          (payBusy ? "true" : "false") +
          '">' +
          LOCK_SVG +
          "<span>" +
          (payBusy ? "Carregando…" : "Ir para o pagamento") +
          "</span></a></div></div>"
        : "");

    function couponHtml(codes) {
      var list =
        (codes || [])
          .map(function (code) {
            return (
              '<li class="mt-2 flex items-center justify-between gap-2 rounded-xl bg-surface-container-low px-3 py-2 text-xs">' +
              '<span class="min-w-0 truncate font-semibold uppercase text-primary" title="' +
              escapeHtml(String(code || "").toUpperCase()) +
              '">' +
              escapeHtml(shortCouponCode(code, 16)) +
              '</span><button type="button" data-pm-coupon-remove="' +
              escapeHtml(code) +
              '" class="shrink-0 text-on-surface-variant underline">Remover</button></li>'
            );
          })
          .join("") || "";
      return (
        '<div class="mt-5 border-t border-outline/40 pt-5" data-pm-coupon>' +
        '<p class="text-sm font-semibold text-on-surface">Cupom</p>' +
        '<form data-pm-coupon-form class="mt-2 flex gap-2">' +
        '<input data-pm-coupon-input name="coupon" type="text" autocomplete="off" placeholder="Código do cupom" class="min-w-0 flex-1 rounded-full border border-primary/25 px-4 py-2.5 text-sm text-on-surface outline-none focus:border-primary" />' +
        '<button type="submit" data-pm-coupon-apply class="btn-lux btn-lux-primary shrink-0 rounded-full px-4 py-2.5 text-xs font-semibold text-on-primary uppercase' +
        (couponBusy ? " pointer-events-none opacity-70" : "") +
        '">' +
        (couponBusy ? "…" : "Aplicar") +
        "</button></form>" +
        (couponError
          ? '<p class="mt-2 text-xs text-primary" data-pm-coupon-error>' +
            escapeHtml(couponError) +
            "</p>"
          : "") +
        (list ? '<ul class="mt-1">' + list + "</ul>" : "") +
        "</div>"
      );
    }

    function upsellHtml(list, lockedUnit) {
      if (!SPLASH.forSale || !SPLASH.wooId || !lockedUnit) return "";
      var already = list.some(function (item) {
        return String(item.id || "").indexOf("body-splash") === 0;
      });
      return (
        '<div class="mt-4 rounded-2xl border border-primary/20 bg-surface-container-low p-4" data-pm-upsell>' +
        '<p class="text-sm font-semibold text-primary">Complete sua compra com Body Splash!</p>' +
        '<p class="mt-1 text-xs text-on-surface-variant">Adicione seu favorito ao pedido com apenas um clique.</p>' +
        '<div class="mt-3 flex gap-3"><span class="relative h-16 w-14 shrink-0 overflow-hidden rounded-xl bg-white">' +
        '<img src="' +
        escapeHtml(productImageUrl(SPLASH.image)) +
        '" alt="" class="h-full w-full object-cover"></span><div class="min-w-0 flex-1">' +
        '<p class="truncate text-sm font-semibold text-on-surface">' +
        escapeHtml(SPLASH.name) +
        '</p><p class="mt-0.5 font-semibold text-primary">' +
        money(SPLASH.priceCents) +
        "</p>" +
        (already
          ? '<p class="mt-2 text-xs font-semibold text-primary">Já no carrinho</p>'
          : '<button type="button" data-pm-upsell-add class="btn-lux btn-lux-primary mt-2 inline-flex w-full items-center justify-center gap-2 rounded-full px-3 py-2 text-xs font-semibold text-on-primary uppercase">' +
            btnBagHtml("Adicionar ao carrinho") +
            "</button>") +
        "</div></div></div>"
      );
    }

    function productImageUrl(path) {
      if (!path) return "";
      if (/^https?:\/\//i.test(path)) return path;
      if (path.indexOf("/images/") === 0) return mediaBase + path;
      return path;
    }

    // Disponivel na unidade = existe variacao daquele produto para ela.
    function unitHasProduct(row, unitId) {
      var units = row && row.units;
      if (!units) return false;
      var meta = units[unitId];
      return !!(meta && meta.variationId);
    }

    function pickRelated(list, limit, unitId) {
      if (!relatedData.products || !unitId) return [];
      var inCart = {};
      list.forEach(function (item) {
        inCart[String(item.id || "")] = true;
      });
      var seeds = list
        .map(function (item) {
          return relatedData.products[String(item.id || "")];
        })
        .filter(Boolean);
      if (!seeds.length) return [];
      var audience = seeds[0].audience;

      var unitTop = (affinityData && affinityData.unitTop && affinityData.unitTop[unitId]) || [];
      var globalTop = (affinityData && affinityData.top) || [];
      var pairs = (affinityData && affinityData.pairs) || {};

      var scored = [];
      Object.keys(relatedData.products).forEach(function (pid) {
        if (inCart[pid]) return;
        if (!SPLASH.forSale && pid.indexOf("body-splash") === 0) return;
        var cand = relatedData.products[pid];
        if (!cand) return;
        if (cand.audience !== audience) return;
        // Nunca sugerir o que a unidade do carrinho nao vende.
        if (!unitHasProduct(cand, unitId)) return;

        var score = 0;
        seeds.forEach(function (seed) {
          var n = pairs[seed.id] && pairs[seed.id][pid];
          if (n) score += 1000 + Math.min(Number(n) || 0, 200) * 5;
          if (seed.category && seed.category === cand.category) {
            var complementa =
              (cand.method === "esfoliacao" && seed.method !== "esfoliacao") ||
              (seed.method === "esfoliacao" && cand.method === "cera");
            score += complementa ? 400 : 120;
          }
        });
        var posUnit = unitTop.indexOf(pid);
        if (posUnit >= 0) score += 200 - posUnit * 5;
        var posGlobal = globalTop.indexOf(pid);
        if (posGlobal >= 0) score += 100 - posGlobal * 2;

        scored.push({ row: cand, score: score });
      });

      scored.sort(function (a, b) {
        if (b.score !== a.score) return b.score - a.score;
        return String(a.row.name).localeCompare(String(b.row.name), "pt-BR");
      });
      return scored.slice(0, limit).map(function (entry) {
        return entry.row;
      });
    }

    function relatedUpsellHtml(list, lockedUnit) {
      if (!lockedUnit || !relatedReady) return "";
      var picks = pickRelated(list, 6, lockedUnit.unitId);
      if (!picks.length) return "";
      var setHtml = picks
        .map(function (product) {
          return (
            '<article class="pm-rail__card">' +
            '<a href="/produto/' +
            encodeURIComponent(product.id) +
            '/" class="pm-rail__media" tabindex="-1">' +
            '<img src="' +
            escapeHtml(productImageUrl(product.image)) +
            '" alt="" width="400" height="500" decoding="async" /></a>' +
            '<div class="pm-rail__body">' +
            '<a href="/produto/' +
            encodeURIComponent(product.id) +
            '/"><h3 class="pm-rail__name">' +
            escapeHtml(product.name) +
            "</h3></a>" +
            '<p class="pm-rail__meta">' +
            escapeHtml(product.duration || "") +
            '</p><p class="pm-rail__price">' +
            money(product.priceCents || 0) +
            '</p><button type="button" data-pm-related-add="' +
            escapeHtml(product.id) +
            '" class="btn-lux btn-lux-primary pm-rail__add">' +
            btnBagHtml("Adicionar") +
            "</button></div></article>"
          );
        })
        .join("");
      // Tres copias do mesmo conjunto: o trilho comeca na copia do meio e, ao
      // chegar nas pontas, o scroll e deslocado em exatamente um conjunto —
      // como as copias sao identicas, o salto e invisivel (loop infinito).
      // As copias sao so visualizacao; nenhum item e duplicado no WooCommerce.
      var slides = setHtml + setHtml + setHtml;
      return (
        '<section data-pm-cart-upsell class="pm-rail-section" aria-label="Adicione também">' +
        '<div class="pm-rail__head"><div>' +
        '<p class="pm-rail__eyebrow">Os mais pedidos</p>' +
        '<h2 class="pm-rail__title">Adicione também</h2>' +
        '<p class="pm-rail__sub">Sugestões com base no seu carrinho · ' +
        escapeHtml(lockedUnit.unitName || "") +
        "</p></div>" +
        '<div class="pm-rail__nav"><button type="button" data-pm-rail-prev aria-label="Produto anterior">' +
        ARROW_L_SVG +
        '</button><button type="button" data-pm-rail-next aria-label="Próximo produto">' +
        ARROW_R_SVG +
        "</button></div></div>" +
        '<div class="pm-rail" data-pm-rail tabindex="0">' +
        '<div class="pm-rail__track" data-pm-rail-track data-set-size="' +
        picks.length +
        '">' +
        slides +
        "</div></div></section>"
      );
    }

    /**
     * Loop infinito do carrossel "Adicione também".
     * O trilho tem 3 copias identicas do conjunto; quando o scroll entra na
     * primeira ou na terceira copia ele e deslocado em um conjunto inteiro.
     */
    function mountRail() {
      var rail = root.querySelector("[data-pm-rail]");
      if (!rail) return;
      var track = rail.querySelector("[data-pm-rail-track]");
      if (!track) return;
      var cards = track.children;
      var perSet = parseInt(track.getAttribute("data-set-size"), 10) || 0;
      if (!perSet || cards.length < perSet * 2) {
        return; // poucos itens para rolar: deixa o scroll nativo
      }
      var reduceMotion =
        window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      function setWidth() {
        return cards[perSet].offsetLeft - cards[0].offsetLeft;
      }
      function recenter() {
        var w = setWidth();
        if (w > 0) rail.scrollLeft = w;
      }
      function wrap() {
        var w = setWidth();
        if (w <= 0) return;
        var x = rail.scrollLeft;
        if (x < w * 0.5) rail.scrollLeft = x + w;
        else if (x > w * 1.5) rail.scrollLeft = x - w;
      }
      function step(dir) {
        var gap = parseFloat(getComputedStyle(track).columnGap) || 0;
        var cardW = cards[0].getBoundingClientRect().width + gap;
        rail.scrollBy({ left: dir * cardW, behavior: reduceMotion ? "auto" : "smooth" });
      }

      recenter();

      var queued = false;
      rail.addEventListener(
        "scroll",
        function () {
          if (queued) return;
          queued = true;
          window.requestAnimationFrame(function () {
            queued = false;
            wrap();
          });
        },
        { passive: true },
      );

      var prev = root.querySelector("[data-pm-rail-prev]");
      var next = root.querySelector("[data-pm-rail-next]");
      if (prev) prev.addEventListener("click", function () { step(-1); });
      if (next) next.addEventListener("click", function () { step(1); });
      rail.addEventListener("keydown", function (event) {
        if (event.key === "ArrowLeft") { event.preventDefault(); step(-1); }
        else if (event.key === "ArrowRight") { event.preventDefault(); step(1); }
      });

      var resizeTimer = null;
      if (!railResizeBound) {
        railResizeBound = true;
        window.addEventListener("resize", function () {
          if (resizeTimer) window.clearTimeout(resizeTimer);
          resizeTimer = window.setTimeout(function () {
            var live = root.querySelector("[data-pm-rail]");
            if (!live) return;
            var tr = live.querySelector("[data-pm-rail-track]");
            var n = parseInt(tr && tr.getAttribute("data-set-size"), 10) || 0;
            if (!n || !tr.children[n]) return;
            var w = tr.children[n].offsetLeft - tr.children[0].offsetLeft;
            if (w > 0) live.scrollLeft = w;
          }, 150);
        });
      }
    }

    function syncQty(id, nextQty) {
      var current = readCart();
      var item = current.find(function (entry) {
        return entry.lineId === id;
      });
      if (!item) return;
      var apply = function (line) {
        writeCart(
          current.map(function (entry) {
            if (entry.lineId !== id) return entry;
            var copy = Object.assign({}, entry, { qty: nextQty });
            if (line && line.key) copy.wooKey = line.key;
            copy.priceCents = catalogUnitCents(copy);
            return copy;
          }),
        );
      };
      if (!window.pmWoo || !item.wooId) {
        apply(null);
        return;
      }
      window.pmWoo.setQty(item.wooKey, item.wooId, nextQty).then(apply).catch(function () {
        render();
      });
    }

    root.querySelectorAll("[data-remove]").forEach(function (button) {
      button.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        var id = button.getAttribute("data-remove");
        var current = readCart();
        var item = current.find(function (entry) {
          return entry.lineId === id;
        });
        writeCart(
          current.filter(function (entry) {
            return entry.lineId !== id;
          }),
        );
        if (window.pmWoo && item && (item.wooKey || item.wooId)) {
          var forget = window.pmWoo.removeProduct
            ? window.pmWoo.removeProduct(item.wooId, item.wooKey)
            : window.pmWoo.remove(item.wooKey);
          forget.catch(function () {});
        }
      });
    });
    root.querySelectorAll("[data-dec]").forEach(function (button) {
      button.addEventListener("click", function () {
        var id = button.getAttribute("data-dec");
        var item = readCart().find(function (entry) {
          return entry.lineId === id;
        });
        if (!item) return;
        if (item.qty <= 1) {
          var removeButton = null;
          root.querySelectorAll("[data-remove]").forEach(function (node) {
            if (node.getAttribute("data-remove") === id) removeButton = node;
          });
          if (removeButton) removeButton.click();
          return;
        }
        syncQty(id, item.qty - 1);
      });
    });
    root.querySelectorAll("[data-inc]").forEach(function (button) {
      button.addEventListener("click", function () {
        var id = button.getAttribute("data-inc");
        var item = readCart().find(function (entry) {
          return entry.lineId === id;
        });
        if (!item) return;
        syncQty(id, item.qty + 1);
      });
    });
    var clear = root.querySelector("[data-clear]");
    if (clear) {
      clear.addEventListener("click", function () {
        var current = readCart();
        var coupons = readCoupons();
        writeCart([]);
        saveCoupons([]);
        wooSnapshot = null;
        if (!window.pmWoo) return;
        var chain = Promise.resolve();
        if (window.pmWoo.removeCoupon) {
          coupons.forEach(function (code) {
            chain = chain.then(function () {
              return window.pmWoo.removeCoupon(code).catch(function () {
                return null;
              });
            });
          });
        }
        chain
          .then(function () {
            return Promise.all(
              current.map(function (item) {
                if (window.pmWoo.removeProduct && (item.wooKey || item.wooId)) {
                  return window.pmWoo.removeProduct(item.wooId, item.wooKey);
                }
                return item.wooKey ? window.pmWoo.remove(item.wooKey) : Promise.resolve();
              }),
            );
          })
          .catch(function () {});
      });
    }
    var couponForm = root.querySelector("[data-pm-coupon-form]");
    if (couponForm) {
      couponForm.addEventListener("submit", function (event) {
        event.preventDefault();
        if (couponBusy) return;
        var input = root.querySelector("[data-pm-coupon-input]");
        var code = input ? String(input.value || "").trim() : "";
        if (!code) {
          couponError = "Digite o código do cupom.";
          render();
          return;
        }
        if (!window.pmWoo || !window.pmWoo.applyCoupon) {
          couponError = "Cupom indisponível neste momento. Recarregue a página.";
          render();
          return;
        }
        couponBusy = true;
        couponError = "";
        render();
        window.pmWoo
          .applyCoupon(code)
          .then(function (data) {
            applyWooSnapshot(data);
            couponBusy = false;
            couponError = "";
            render();
          })
          .catch(function (error) {
            couponBusy = false;
            couponError = wooErrorMessage(error, code);
            refreshWooSnapshot().finally(function () {
              render();
            });
          });
      });
    }
    root.querySelectorAll("[data-pm-coupon-remove]").forEach(function (button) {
      button.addEventListener("click", function () {
        var code = button.getAttribute("data-pm-coupon-remove");
        if (!code || !window.pmWoo || !window.pmWoo.removeCoupon) return;
        couponBusy = true;
        couponError = "";
        render();
        window.pmWoo
          .removeCoupon(code)
          .then(function (data) {
            applyWooSnapshot(data);
            couponBusy = false;
            render();
          })
          .catch(function () {
            couponBusy = false;
            couponError = "Não foi possível remover o cupom.";
            refreshWooSnapshot().finally(function () {
              render();
            });
          });
      });
    });

    var upsellAdd = root.querySelector("[data-pm-upsell-add]");
    if (upsellAdd) {
      upsellAdd.addEventListener("click", function () {
        if (upsellAdd.disabled) return;
        var current = readCart();
        var locked = current[0];
        if (!locked) return;
        if (current.some(function (item) {
          return String(item.id || "").indexOf("body-splash") === 0;
        })) {
          return;
        }
        upsellAdd.disabled = true;
        upsellAdd.innerHTML = btnBusyHtml("carregando");
        var lineId = SPLASH.id + "::" + locked.unitId;
        var saved = {
          lineId: lineId,
          id: SPLASH.id,
          name: SPLASH.name,
          image: productImageUrl(SPLASH.image),
          duration: SPLASH.duration,
          sku: SPLASH.sku,
          unitId: locked.unitId,
          unitName: locked.unitName,
          city: locked.city,
          stateName: locked.stateName,
          priceCents: SPLASH.priceCents,
          wooId: SPLASH.wooId,
          qty: 1,
        };
        var finish = function (line) {
          if (line && line.key) saved.wooKey = line.key;
          saved.qty = (line && line.quantity) || 1;
          saved.priceCents = SPLASH.priceCents;
          writeCart(current.concat([saved]));
        };
        if (!window.pmWoo) {
          finish(null);
          return;
        }
        window.pmWoo
          .push(SPLASH.wooId, 1)
          .then(finish)
          .catch(function () {
            upsellAdd.disabled = false;
            upsellAdd.innerHTML = btnBagHtml("Adicionar ao carrinho");
          });
      });
    }

    function variationForUnit(product, unitId) {
      if (!product) return "";
      var units = product.units || {};
      var key = String(unitId || "").toLowerCase();
      var meta = units[key] || units[String(unitId || "")] || null;
      if (!meta) {
        // fallback: match case-insensitive keys
        Object.keys(units).forEach(function (uid) {
          if (!meta && String(uid).toLowerCase() === key) meta = units[uid];
        });
      }
      return meta && meta.variationId ? String(meta.variationId) : "";
    }

    root.querySelectorAll("[data-pm-related-add]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (button.disabled) return;
        var pid = button.getAttribute("data-pm-related-add");
        var product = pid && relatedData.products[pid];
        var current = readCart();
        var locked = current[0];
        if (!product || !locked) return;
        var existing = current.find(function (item) {
          return String(item.id || "") === pid && String(item.unitId) === String(locked.unitId);
        });
        button.disabled = true;
        button.innerHTML = btnBusyHtml("carregando");
        var wooId = variationForUnit(product, locked.unitId);
        if (!wooId) wooId = String(product.wooId || product.productId || "");
        if (!wooId) {
          button.disabled = false;
          button.innerHTML = btnBagHtml("Adicionar");
          payError = "Este item ainda não entra no carrinho da loja nesta unidade.";
          render();
          return;
        }
        var lineId = product.id + "::" + locked.unitId;
        var targetQty = (existing ? existing.qty : 0) + 1;
        var saved = existing || {
          lineId: lineId,
          id: product.id,
          name: product.name,
          image: productImageUrl(product.image),
          duration: product.duration || "",
          sku: product.sku || "",
          unitId: locked.unitId,
          unitName: locked.unitName,
          city: locked.city,
          stateName: locked.stateName,
          priceCents: product.priceCents || 0,
          productId: product.productId || product.wooId || "",
          variationId: wooId,
          wooId: wooId,
          qty: 1,
        };
        saved.variationId = wooId;
        saved.wooId = wooId;
        saved.priceCents = product.priceCents || saved.priceCents || 0;

        var finish = function (line) {
          if (!line || !line.key) throw new Error("woo");
          saved.wooKey = line.key;
          saved.qty = line.quantity || targetQty;
          saved.priceCents = catalogUnitCents(saved);
          if (existing) {
            writeCart(
              current.map(function (item) {
                return item.lineId === lineId ? saved : item;
              }),
            );
          } else {
            writeCart(current.concat([saved]));
          }
        };

        var request;
        if (!window.pmWoo) {
          saved.qty = targetQty;
          if (existing) {
            writeCart(
              current.map(function (item) {
                return item.lineId === lineId ? saved : item;
              }),
            );
          } else {
            writeCart(current.concat([saved]));
          }
          return;
        }
        request =
          existing && existing.wooKey
            ? window.pmWoo.setQty(existing.wooKey, wooId, targetQty, product.id)
            : window.pmWoo.push(wooId, 1, product.id);
        request
          .then(finish)
          .catch(function () {
            button.disabled = false;
            button.innerHTML = btnBagHtml("Adicionar");
            payError =
              'Não foi possível adicionar "' + (product.name || "item") + '" ao carrinho.';
            render();
          });
      });
    });
    // Dois botoes de pagamento (resumo no desktop, barra fixa no mobile):
    // ambos usam exatamente o mesmo fluxo — reconcile + redirect.
    var payLinks = root.querySelectorAll('a[href="/finalizar-pagamento/"]');
    Array.prototype.forEach.call(payLinks, function (pay) {
      pay.addEventListener("click", function (event) {
        event.preventDefault();
        if (payBusy) return;
        var current = readCart();
        if (!current.length) return;
        if (!window.pmWoo || typeof window.pmWoo.reconcile !== "function") {
          payError = "Não foi possível sincronizar o carrinho. Recarregue a página.";
          render();
          return;
        }
        if (current.some(function (item) {
          return !item.wooId;
        })) {
          payError =
            "Há itens sem vínculo com a loja. Remova-os e adicione de novo ao carrinho.";
          render();
          return;
        }
        payError = "";
        payBusy = true;
        render();
        window.pmWoo
          .reconcile(current)
          .then(function () {
            writeCart(current);
            return refreshWooSnapshot();
          })
          .then(function () {
            window.location.href = "/finalizar-pagamento/";
          })
          .catch(function () {
            payBusy = false;
            payError =
              "Não foi possível enviar todos os itens ao pagamento. Tente de novo.";
            render();
          });
      });
    });

    if (root.querySelector("[data-pm-rail]")) mountRail();
  }

  paintLoading();
  var mediaRoot =
    (window.location && window.location.origin ? window.location.origin : "") +
    "/wp-content/uploads/pm-home/";
  var relatedUrl = mediaRoot + "cart-related.json";
  // Opcional: se nao existir, a recomendacao usa so regiao + mais vendidos.
  var affinityPromise = fetch(mediaRoot + "cart-affinity.json", {
    credentials: "same-origin",
    cache: "no-cache",
  })
    .then(function (resp) {
      return resp && resp.ok ? resp.json() : null;
    })
    .then(function (data) {
      if (data && data.pairs) affinityData = data;
    })
    .catch(function () {});
  var boot = Promise.resolve();
  if (window.pmBlackNov && typeof window.pmBlackNov.load === "function") {
    boot = window.pmBlackNov.load();
  }
  Promise.all([boot.catch(function () {}), affinityPromise])
    .then(function () {
      return fetch(relatedUrl, { credentials: "same-origin", cache: "no-cache" });
    })
    .then(function (resp) {
      return resp && resp.ok ? resp.json() : null;
    })
    .then(function (data) {
      if (data && data.products) {
        relatedData = data;
        relatedReady = true;
        // Imagem versionada (?v=hash) do catálogo, igual à ficha — fura o cache da CDN.
        var splashRow = data.products[SPLASH.id];
        if (splashRow && splashRow.image) SPLASH.image = splashRow.image;
        syncLocalPricesFromCatalog();
      }
    })
    .catch(function () {})
    .finally(function () {
      refreshWooSnapshot().finally(function () {
        syncLocalPricesFromCatalog();
        render();
      });
    });
})();
