(function () {
  var KEY = "pm-cart-v1";

  function readCart() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "[]");
    } catch (error) {
      return [];
    }
  }

  function count(items) {
    return items.reduce(function (sum, item) {
      return sum + item.qty;
    }, 0);
  }

  function money(cents) {
    return (cents / 100).toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  }

  // Alinhado ao CF7 #1831: total < R$ 180 → 1x; cera/esfoliação até 3x; plano/presente 1x; demais até 10x; piso R$ 50.
  var MIN_INSTALLMENT_ORDER_CENTS = 18000;
  var MIN_INSTALLMENT_CENTS = 5000;
  function installment(cents, method) {
    if (method === "plano" || method === "presente") {
      return { times: 1, installment: cents };
    }
    if (cents < MIN_INSTALLMENT_ORDER_CENTS) {
      return { times: 1, installment: cents };
    }
    var maxTimes = method === "cera" || method === "esfoliacao" ? 3 : 10;
    var byFloor = Math.max(1, Math.floor(cents / MIN_INSTALLMENT_CENTS));
    var times = Math.min(maxTimes, byFloor);
    if (times < 1) times = 1;
    return { times: times, installment: Math.ceil(cents / times) };
  }

  function writeCart(items) {
    localStorage.setItem(KEY, JSON.stringify(items));
    paintBadge(items);
  }

  function paintBadge(items) {
    if (window.pmPaintCart) {
      window.pmPaintCart(items);
      return;
    }
    var total = count(items);
    document.querySelectorAll('a[href="/carrinho/"], a[href="/carrinho"]').forEach(function (link) {
      var badge = link.querySelector("[data-pm-badge]");
      if (!total) {
        if (badge) badge.remove();
        return;
      }
      if (!badge) {
        badge = document.createElement("span");
        badge.setAttribute("data-pm-badge", "");
        badge.className =
          "absolute flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-white";
        badge.style.top = "-10px";
        badge.style.right = "-10px";
        badge.style.zIndex = "3";
        link.appendChild(badge);
      }
      badge.textContent = String(total);
    });
  }

  function selected(box) {
    var select = box.querySelector("[data-pm-unit]");
    var option = select && select.selectedOptions ? select.selectedOptions[0] : null;
    var region = option && option.getAttribute("data-region") === "sp-df" ? "sp" : "rj";
    return {
      select: select,
      option: option,
      region: region,
      sale: Number(box.getAttribute("data-" + region + "-sale")) || 0,
      regular: Number(box.getAttribute("data-" + region + "-regular")) || 0,
    };
  }

  function applyPrice(box) {
    var state = selected(box);
    var method = box.getAttribute("data-method") || "cera";
    var parcel = installment(state.sale, method);
    var saleNode = box.querySelector("[data-pm-sale]");
    var totalNode = box.querySelector("[data-pm-total]");
    var regularNode = box.querySelector("[data-pm-regular]");
    var offNode = box.querySelector("[data-pm-off]");
    var regionNode = box.querySelector("[data-pm-region]");
    if (saleNode) {
      saleNode.textContent =
        parcel.times > 1
          ? parcel.times + "x de " + money(parcel.installment)
          : money(state.sale);
    }
    if (totalNode) {
      if (parcel.times > 1) {
        totalNode.classList.remove("hidden");
        totalNode.textContent = "Total " + money(state.sale);
      } else {
        totalNode.classList.add("hidden");
      }
    }
    if (regularNode) {
      if (state.regular > state.sale) {
        regularNode.classList.remove("hidden");
        regularNode.classList.add("line-through");
        regularNode.textContent = money(state.regular);
      } else {
        regularNode.classList.add("hidden");
      }
    }
    if (offNode) {
      if (state.regular > state.sale) {
        offNode.classList.remove("hidden");
        offNode.textContent = "-" + Math.round((1 - state.sale / state.regular) * 100) + "%";
      } else {
        offNode.classList.add("hidden");
      }
    }
    if (regionNode) {
      if (!state.select || !state.select.value) {
        regionNode.textContent =
          "Tabela de Rio de Janeiro e interior de São Paulo. O valor muda ao escolher a unidade.";
      } else if (state.region === "sp") {
        regionNode.textContent = "Tabela de São Paulo capital e DF";
      } else {
        regionNode.textContent = "Tabela de Rio de Janeiro e interior de São Paulo";
      }
    }
    return state;
  }

  function showError(box, message) {
    var node = box.querySelector("[data-pm-unit-error]");
    var select = box.querySelector("[data-pm-unit]");
    if (node) {
      node.textContent = message;
      node.classList.toggle("hidden", !message);
    }
    if (select) select.classList.toggle("border-primary", Boolean(message));
  }

  var wooNonce = "";

  function wooRefresh(response) {
    var next = response.headers.get("Nonce");
    if (next) wooNonce = next;
    return response.json().then(function (data) {
      if (!response.ok) {
        var error = new Error("woo");
        error.payload = data;
        throw error;
      }
      return data;
    });
  }

  function wooNonceReady() {
    if (wooNonce) return Promise.resolve(wooNonce);
    return fetch("/wp-json/wc/store/v1/cart", { credentials: "same-origin" }).then(wooRefresh).then(function () {
      return wooNonce;
    });
  }

  function wooPost(path, payload) {
    return wooNonceReady().then(function () {
      return fetch("/wp-json/wc/store/v1/cart/" + path, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          Nonce: wooNonce,
        },
        body: JSON.stringify(payload),
      })
        .then(wooRefresh)
        .then(function (data) {
          scheduleWcarRecapture(data);
          return data;
        });
    });
  }

  // ---------------------------------------------------------------------------
  // Carrinho abandonado fora do checkout: quando a cliente já é conhecida
  // (identidade salva em pm-identity-v1 pelo checkout ou conta logada), cada
  // mudança no carrinho (adicionar / quantidade / remover) atualiza a linha do
  // plugin Cart Abandonment Recovery — assim o lembrete sai mesmo para quem
  // nunca chegou ao checkout nesta visita. Config (nonce) vem de pm-wcar/v1/config.
  // ---------------------------------------------------------------------------
  var WCAR_IDENTITY_KEY = "pm-identity-v1";
  var wcarConfigPromise = null;
  var wcarRecaptureTimer = null;
  var wcarLastRecapture = "";

  function wcarReadIdentity() {
    try {
      var raw = JSON.parse(localStorage.getItem(WCAR_IDENTITY_KEY) || "null");
      return raw && typeof raw === "object" ? raw : null;
    } catch (error) {
      return null;
    }
  }

  function wcarWriteIdentity(patch) {
    var current = wcarReadIdentity() || {};
    Object.keys(patch || {}).forEach(function (key) {
      var value = patch[key];
      if (value != null && String(value).trim()) current[key] = String(value).trim();
    });
    if (!current.leadId) {
      var chars = "abcdefghijklmnopqrstuvwxyz0123456789";
      var id = "";
      for (var i = 0; i < 20; i++) id += chars.charAt(Math.floor(Math.random() * chars.length));
      current.leadId = id;
    }
    current.updatedAt = new Date().toISOString();
    try {
      localStorage.setItem(WCAR_IDENTITY_KEY, JSON.stringify(current));
      document.cookie = "pm_lead_id=" + encodeURIComponent(current.leadId) + "; path=/; max-age=31536000; SameSite=Lax";
    } catch (error) {}
    return current;
  }

  function wcarConfig() {
    if (wcarConfigPromise) return wcarConfigPromise;
    wcarConfigPromise = fetch("/wp-json/pm-wcar/v1/config", { credentials: "same-origin" })
      .then(function (response) {
        return response.ok ? response.json() : null;
      })
      .then(function (cfg) {
        if (cfg && cfg.user && cfg.user.email) wcarWriteIdentity(cfg.user);
        return cfg && cfg.enabled && cfg.nonce && cfg.ajaxurl ? cfg : null;
      })
      .catch(function () {
        return null;
      });
    return wcarConfigPromise;
  }

  function wcarValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(value || "").trim());
  }

  function wcarRecapture(cartData) {
    var identity = wcarReadIdentity();
    var hasLead = identity && (identity.name || identity.phone || identity.cpf);
    if (!identity || (!wcarValidEmail(identity.email) && !hasLead)) {
      // Sem identidade local: ainda vale consultar a conta logada.
      return wcarConfig().then(function (cfg) {
        var fresh = wcarReadIdentity();
        if (cfg && fresh && wcarValidEmail(fresh.email) && !identity) wcarRecapture(cartData);
      });
    }
    return wcarConfig().then(function (cfg) {
      if (!cfg) return;
      var items = (cartData && cartData.items) || [];
      var sig = items
        .map(function (line) {
          return line.key + ":" + line.quantity;
        })
        .join(",") + "|" + ((cartData && cartData.totals && cartData.totals.total_price) || "");
      var key = sig + "|" + (identity.email || "") + "|" + (identity.phone || "");
      if (key === wcarLastRecapture) return;
      wcarLastRecapture = key;
      var parts = String(identity.name || "").split(/\s+/).filter(Boolean);
      var unit = identity.unit || "";
      try {
        var local = JSON.parse(localStorage.getItem("pm-cart-v1") || "[]");
        if (Array.isArray(local) && local.length && local[0].unitName) {
          unit = [local[0].unitName, local[0].city, local[0].stateName].filter(Boolean).join(" · ");
        }
      } catch (error) {}
      var body = new URLSearchParams();
      if (wcarValidEmail(identity.email)) {
        var data = {
          action: "cartflows_save_cart_abandonment_data",
          security: cfg.nonce,
          wcf_post_id: cfg.postId || 0,
          wcf_email: identity.email,
          wcf_phone: identity.phone || "",
          wcf_name: parts.shift() || "",
          wcf_surname: parts.join(" "),
          wcf_city: identity.city || "",
          wcf_billing_state: identity.state || "",
          wcf_billing_postcode: identity.cep || "",
          wcf_billing_address_1: identity.address1 || "",
          wcf_billing_address_2: identity.address2 || "",
          wcf_country: "BR",
          pm_cpf: identity.cpf || "",
          pm_unidade: unit,
          pm_lead_id: identity.leadId || "",
          pm_source: items.length ? "cart" : "cart-empty",
        };
        Object.keys(data).forEach(function (k) {
          body.append(k, data[k] == null ? "" : String(data[k]));
        });
        fetch(cfg.ajaxurl, { method: "POST", credentials: "same-origin", body: body }).catch(function () {});
      }
      if (cfg.leadNonce && hasLead) {
        var lead = new URLSearchParams();
        var leadData = {
          action: "pm_lead_save",
          security: cfg.leadNonce,
          lead_id: identity.leadId || "",
          name: identity.name || "",
          phone: identity.phone || "",
          cpf: identity.cpf || "",
          unit: unit,
          email: wcarValidEmail(identity.email) ? identity.email : "",
          city: identity.city || "",
          state: identity.state || "",
          page: window.location.pathname,
          cart: sig,
        };
        Object.keys(leadData).forEach(function (k) {
          lead.append(k, leadData[k] == null ? "" : String(leadData[k]));
        });
        fetch(cfg.ajaxurl, { method: "POST", credentials: "same-origin", body: lead }).catch(function () {});
      }
    });
  }

  function scheduleWcarRecapture(cartData) {
    window.clearTimeout(wcarRecaptureTimer);
    wcarRecaptureTimer = window.setTimeout(function () {
      wcarRecapture(cartData);
    }, 1500);
  }

  /** Extrai pm_catalog_id da linha Store API (item_data / extensions / meta). */
  function lineCatalogId(line) {
    if (!line) return "";
    var raw =
      line.pm_catalog_id ||
      (line.extensions &&
        (line.extensions.pm_catalog_id ||
          (line.extensions["pellomenos"] && line.extensions["pellomenos"].pm_catalog_id))) ||
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

  /**
   * Casa linha Woo: catalogId desambigua esfoliação vs cera (mesmo variationId).
   * Preferência: key → catalogId → wooId (último só se único / sem catalog pedido).
   */
  function wooLine(data, wooId, catalogId, preferKey) {
    var items = (data && data.items) || [];
    var wantCat = catalogId ? String(catalogId) : "";
    var wantWoo = wooId != null ? String(wooId) : "";
    if (preferKey) {
      for (var k = 0; k < items.length; k++) {
        if (String(items[k].key) === String(preferKey)) return items[k];
      }
    }
    if (wantCat) {
      for (var c = 0; c < items.length; c++) {
        if (lineCatalogId(items[c]) === wantCat) return items[c];
      }
    }
    var matches = [];
    for (var index = 0; index < items.length; index++) {
      if (wantWoo && String(items[index].id) === wantWoo) matches.push(items[index]);
    }
    if (wantCat) {
      // Sem item_data ainda: pega a linha do mesmo wooId que ainda não tem outro catalog.
      for (var m = 0; m < matches.length; m++) {
        var cid = lineCatalogId(matches[m]);
        if (!cid || cid === wantCat) return matches[m];
      }
    }
    return matches.length ? matches[matches.length - 1] : null;
  }

  window.pmWoo = {
    lineCatalogId: lineCatalogId,
    push: function (wooId, quantity, catalogId) {
      if (!wooId) return Promise.resolve(null);
      var payload = { id: Number(wooId), quantity: quantity };
      if (catalogId) payload.pm_catalog_id = String(catalogId);
      return wooPost("add-item", payload).then(function (data) {
        return wooLine(data, wooId, catalogId);
      });
    },
    setQty: function (key, wooId, quantity, catalogId) {
      if (!key) return this.push(wooId, quantity, catalogId);
      var payload = { key: key, quantity: quantity };
      if (catalogId) payload.pm_catalog_id = String(catalogId);
      return wooPost("update-item", payload).then(function (data) {
        return wooLine(data, wooId, catalogId, key);
      });
    },
    remove: function (key) {
      if (!key) return Promise.resolve(null);
      return wooPost("remove-item", { key: key });
    },
    getCart: function () {
      return fetch("/wp-json/wc/store/v1/cart", { credentials: "same-origin" }).then(wooRefresh);
    },
    applyCoupon: function (code) {
      var trimmed = String(code || "").trim();
      if (!trimmed) return Promise.reject(new Error("coupon-empty"));
      return wooPost("apply-coupon", { code: trimmed });
    },
    removeCoupon: function (code) {
      var trimmed = String(code || "").trim();
      if (!trimmed) return Promise.reject(new Error("coupon-empty"));
      return wooPost("remove-coupon", { code: trimmed });
    },
    /** Persist preferred coupon codes across reconcile (localStorage). */
    readSavedCoupons: function () {
      try {
        var raw = JSON.parse(localStorage.getItem("pm-coupon-v1") || "[]");
        return Array.isArray(raw)
          ? raw.map(function (c) {
              return String(c || "").trim();
            }).filter(Boolean)
          : [];
      } catch (error) {
        return [];
      }
    },
    writeSavedCoupons: function (codes) {
      var list = (codes || [])
        .map(function (c) {
          return String(c || "").trim();
        })
        .filter(Boolean);
      localStorage.setItem("pm-coupon-v1", JSON.stringify(list));
      return list;
    },
    couponCodesFromCart: function (data) {
      return ((data && data.coupons) || [])
        .map(function (c) {
          return String((c && (c.code || c)) || "").trim();
        })
        .filter(Boolean);
    },
    /** Store API money fields are usually minor units (cents) as strings. */
    totalsCents: function (data) {
      var t = (data && data.totals) || {};
      function n(key) {
        var v = t[key];
        if (v == null || v === "") return 0;
        return Math.round(Number(v));
      }
      return {
        subtotal: n("total_items"),
        discount: n("total_discount"),
        total: n("total_price"),
        currencyMinorUnit: Number(t.currency_minor_unit != null ? t.currency_minor_unit : 2),
      };
    },
    /**
     * Regra do cupom aplicado, independente do preço cobrado pelo Woo.
     * No ensaio o Woo cobra R$ 1,00 por item; a vitrine mostra o preço do catálogo.
     * Para cupom percentual, a razão total_discount / total_items é o percentual real
     * (0,25 / 5,00 = 5%) e vale para qualquer base de preço.
     */
    couponRuleFromCart: function (data) {
      var coupons = (data && data.coupons) || [];
      if (!coupons.length) return null;
      var t = (data && data.totals) || {};
      var discount = Math.round(Number(t.total_discount || 0)) || 0;
      var items = Math.round(Number(t.total_items || 0)) || 0;
      var first = coupons[0] || {};
      var code = String(first.code || first || "").trim();
      var type = String(first.discount_type || "").toLowerCase();
      // Cupom interno PM1L: hook no Woo força líquido R$1 no buço-linha.
      // Nao tratar como % (senao a vitrine mostra −R$0,20 em vez de ~−R$18,87).
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
      var rule = { code: code, type: type || "percent", percent: 0, fixedCents: discount };
      if (type === "fixed_cart") {
        return rule;
      }
      if (items > 0 && discount > 0) {
        var pct = (discount / items) * 100;
        // Arredonda para o percentual "humano" (5, 10, 15…) quando estiver próximo.
        var rounded = Math.round(pct * 2) / 2;
        rule.percent = Math.abs(pct - rounded) < 0.4 ? rounded : Math.round(pct * 100) / 100;
        if (type !== "percent" && type !== "fixed_product") rule.type = "percent";
        if (type === "fixed_product") rule.type = "percent";
      }
      return rule;
    },
    /** Desconto para exibir, em centavos, a partir do subtotal de vitrine. */
    displayDiscountCents: function (rule, subtotalCents) {
      if (!rule) return 0;
      var subtotal = Math.max(0, Math.round(Number(subtotalCents) || 0));
      if (rule.type === "target_total") {
        var target = Math.max(0, Math.round(Number(rule.targetCents) || 100));
        return Math.max(0, subtotal - target);
      }
      if (rule.type === "fixed_cart") return Math.min(subtotal, Math.max(0, rule.fixedCents || 0));
      if (rule.percent > 0) return Math.min(subtotal, Math.round((subtotal * rule.percent) / 100));
      return Math.min(subtotal, Math.max(0, rule.fixedCents || 0));
    },
    /** Unit price in cents from a Store API cart line. */
    lineUnitCents: function (line) {
      if (!line) return 0;
      var qty = Math.max(1, Number(line.quantity) || 1);
      var t = line.totals || {};
      if (t.line_subtotal != null && t.line_subtotal !== "") {
        return Math.round(Number(t.line_subtotal) / qty);
      }
      if (t.line_total != null && t.line_total !== "") {
        return Math.round(Number(t.line_total) / qty);
      }
      var prices = line.prices || {};
      if (prices.price != null && prices.price !== "") {
        return Math.round(Number(prices.price));
      }
      return 0;
    },
    removeProduct: function (wooId, key) {
      var self = this;
      var first = key ? self.remove(key) : Promise.reject(new Error("woo"));
      return first.catch(function () {
        return fetch("/wp-json/wc/store/v1/cart", { credentials: "same-origin" }).then(wooRefresh).then(function (data) {
          var pending = ((data && data.items) || []).filter(function (item) {
            return !wooId || String(item.id) === String(wooId);
          });
          return pending.reduce(function (chain, item) {
            return chain.then(function () {
              return self.remove(item.key);
            });
          }, Promise.resolve());
        });
      });
    },
    /** Rebuild Woo session from local cart lines (mutates items with fresh wooKey). */
    reconcile: function (localItems) {
      var self = this;
      var needed = (localItems || []).filter(function (item) {
        return item && item.wooId;
      });
      if (!needed.length) {
        return Promise.reject(new Error("woo-empty"));
      }
      if (needed.length !== (localItems || []).length) {
        return Promise.reject(new Error("woo-missing-id"));
      }
      // Woo on this store drops variable/service lines when some simple
      // products (ex. Body Splash) are added last — push simples first.
      function wooRank(item) {
        var id = String(item.id || "");
        var wooId = String(item.wooId || "");
        if (id.indexOf("body-splash") === 0) return 0;
        if (id.indexOf("cartao-presente") === 0) return 0;
        return 1;
      }
      var ordered = needed.slice().sort(function (a, b) {
        return wooRank(a) - wooRank(b);
      });

      function clearCart() {
        return fetch("/wp-json/wc/store/v1/cart", { credentials: "same-origin" })
          .then(wooRefresh)
          .then(function (data) {
            var existing = (data && data.items) || [];
            return existing.reduce(function (chain, line) {
              return chain.then(function () {
                return self.remove(line.key);
              });
            }, Promise.resolve());
          });
      }

      function pushAll(list) {
        return list.reduce(function (chain, item) {
          return chain.then(function () {
            // catalog id evita fundir esfoliação + cera no mesmo variationId Woo
            return self.push(item.wooId, item.qty || 1, item.id).then(function (line) {
              if (!line || !line.key) throw new Error("woo-push");
              item.wooKey = line.key;
              return line;
            });
          });
        }, Promise.resolve());
      }

      function verify() {
        return fetch("/wp-json/wc/store/v1/cart", { credentials: "same-origin" })
          .then(wooRefresh)
          .then(function (data) {
            var wooItems = (data && data.items) || [];
            if (wooItems.length < needed.length) throw new Error("woo-mismatch");
            var usedKeys = {};
            needed.forEach(function (item) {
              var matched = null;
              var wantCat = String(item.id || "");
              if (wantCat) {
                for (var i = 0; i < wooItems.length; i++) {
                  if (usedKeys[wooItems[i].key]) continue;
                  if (lineCatalogId(wooItems[i]) === wantCat) {
                    matched = wooItems[i];
                    break;
                  }
                }
              }
              if (!matched && item.wooKey) {
                for (var j = 0; j < wooItems.length; j++) {
                  if (usedKeys[wooItems[j].key]) continue;
                  if (String(wooItems[j].key) === String(item.wooKey)) {
                    matched = wooItems[j];
                    break;
                  }
                }
              }
              if (!matched) {
                for (var k = 0; k < wooItems.length; k++) {
                  if (usedKeys[wooItems[k].key]) continue;
                  if (String(wooItems[k].id) === String(item.wooId)) {
                    matched = wooItems[k];
                    break;
                  }
                }
              }
              if (!matched) throw new Error("woo-mismatch");
              usedKeys[matched.key] = true;
              item.wooKey = matched.key;
              if ((matched.quantity || 0) < (item.qty || 1)) throw new Error("woo-mismatch");
            });
            return needed;
          });
      }

      var savedCoupons = self.readSavedCoupons();

      function reapplyCoupons(codes) {
        var unique = [];
        (codes || []).forEach(function (code) {
          var c = String(code || "").trim();
          if (c && unique.indexOf(c) === -1) unique.push(c);
        });
        return unique.reduce(function (chain, code) {
          return chain.then(function () {
            return self.applyCoupon(code).catch(function () {
              // Skip codes that no longer apply after rebuild
              return null;
            });
          });
        }, Promise.resolve()).then(function () {
          return self.getCart().then(function (data) {
            self.writeSavedCoupons(self.couponCodesFromCart(data));
            return data;
          });
        });
      }

      return clearCart()
        .then(function () {
          return pushAll(ordered);
        })
        .then(verify)
        .then(function () {
          return reapplyCoupons(savedCoupons);
        })
        .then(function () {
          return needed;
        });
    },
  };

  /** Store capacity sets — keep in sync with src/lib/data.ts storeUnits flags. */
  var CERA_MASC = {
    rec: 1,
    "sp-aug": 1,
    "sp-avp": 1,
    urg: 1,
    ban: 1,
    bot: 1,
    "copa-2": 1,
    eba: 1,
    fla: 1,
    fre: 1,
    ica: 1,
    lbi: 1,
    nig2: 1,
  };
  var LASER_FEM = {
    rec: 1,
    cen: 1,
    sgo: 1,
    nil: 1,
    lma: 1,
    "sp-sjc": 1,
    pet: 1,
    ig02: 1,
    hut: 1,
    urg: 1,
    ban: 1,
    bot: 1,
    "copa-2": 1,
    eba: 1,
    fla: 1,
    fre: 1,
    ica: 1,
    lbi: 1,
    nig2: 1,
  };
  var LASER_MASC = {
    urg: 1,
    ban: 1,
    bot: 1,
    "copa-2": 1,
    eba: 1,
    fla: 1,
    fre: 1,
    ica: 1,
    lbi: 1,
    nig2: 1,
  };

  function allowedUnitsForCatalog(catalogId, method, audience) {
    var id = catalogId || "";
    var base = id.slice(-5) === "-masc" ? id.slice(0, -5) : id;
    var isMasc = audience === "masculino" || id.slice(-5) === "-masc";
    if (
      method === "linha" ||
      method === "esfoliacao" ||
      method === "presente" ||
      method === "produto" ||
      base.indexOf("body-splash") === 0
    ) {
      return null;
    }
    if (method === "plano") {
      if (base === "plano-clube-laser") return isMasc ? {} : LASER_FEM;
      return isMasc ? CERA_MASC : null;
    }
    if (method === "cera") return isMasc ? CERA_MASC : null;
    if (method === "laser") return isMasc ? LASER_MASC : LASER_FEM;
    return null;
  }

  function pruneUnitSelect(box) {
    var select = box.querySelector("[data-pm-unit]");
    if (!select) return;
    var root = document.querySelector("[data-audience]");
    var audience = root ? root.getAttribute("data-audience") || "feminino" : "feminino";
    var allow = allowedUnitsForCatalog(
      box.getAttribute("data-catalog-id") || "",
      box.getAttribute("data-method") || "",
      audience,
    );
    if (!allow) return;
    var options = Array.prototype.slice.call(select.querySelectorAll("option"));
    options.forEach(function (opt) {
      var value = opt.value;
      if (!value) return;
      if (!allow[value]) opt.remove();
    });
    Array.prototype.slice.call(select.querySelectorAll("optgroup")).forEach(function (group) {
      if (!group.querySelector("option")) group.remove();
    });
  }

  function bindBuy(box) {
    pruneUnitSelect(box);
    var select = box.querySelector("[data-pm-unit]");
    if (select) {
      select.addEventListener("change", function () {
        showError(box, "");
        applyPrice(box);
      });
    }
    var qtyNode = box.querySelector("[data-pm-qty]");
    var dec = box.querySelector("[data-pm-dec]");
    var inc = box.querySelector("[data-pm-inc]");
    function qty() {
      return Math.max(1, parseInt(qtyNode ? qtyNode.textContent : "1", 10) || 1);
    }
    if (dec) {
      dec.addEventListener("click", function () {
        if (qtyNode) qtyNode.textContent = String(Math.max(1, qty() - 1));
      });
    }
    if (inc) {
      inc.addEventListener("click", function () {
        if (qtyNode) qtyNode.textContent = String(qty() + 1);
      });
    }
    var moreBtn = document.querySelector("[data-pm-more-toggle]");
    var longCopy = document.querySelector("[data-pm-long]");
    function applyClamp(closed) {
      if (!longCopy) return;
      if (!closed) {
        longCopy.style.display = "";
        longCopy.style.webkitBoxOrient = "";
        longCopy.style.webkitLineClamp = "";
        longCopy.style.overflow = "";
        return;
      }
      var lines = window.matchMedia("(min-width: 768px)").matches ? "4" : "6";
      longCopy.style.display = "-webkit-box";
      longCopy.style.webkitBoxOrient = "vertical";
      longCopy.style.webkitLineClamp = lines;
      longCopy.style.overflow = "hidden";
    }
    if (moreBtn && longCopy) {
      var chars = parseInt(longCopy.getAttribute("data-pm-chars") || "0", 10);
      if (chars <= 280) {
        moreBtn.classList.add("hidden");
        longCopy.classList.remove("pm-clamp");
        applyClamp(false);
      } else {
        applyClamp(true);
        window.addEventListener("resize", function () {
          if (longCopy.classList.contains("pm-clamp")) applyClamp(true);
        });
      }
      moreBtn.addEventListener("click", function () {
        var closed = longCopy.classList.toggle("pm-clamp");
        applyClamp(closed);
        moreBtn.textContent = closed ? "Ler mais" : "Ler menos";
      });
    }
    var add = box.querySelector("[data-pm-add]");
    if (!add) return;
    add.addEventListener("click", function () {
      var state = applyPrice(box);
      if (!state.select || !state.select.value || !state.option) {
        showError(box, "Escolha a unidade para continuar.");
        return;
      }
      var option = state.option;
      var wooId = option.getAttribute("data-variation") || "";
      if (!wooId) {
        box.querySelectorAll("[data-variation]").forEach(function (node) {
          if (!wooId && node.getAttribute("data-variation")) {
            wooId = node.getAttribute("data-variation");
          }
        });
      }
      if (!wooId) wooId = box.getAttribute("data-product-id") || "";
      if (!wooId) {
        showError(box, "Este serviço ainda não entra no pagamento da loja.");
        return;
      }
      showError(box, "");
      var amount = qty();
      var lineId = box.getAttribute("data-catalog-id") + "::" + state.select.value;
      var photo = document.querySelector("[data-pm-photo]");
      var items = readCart();
      var locked = items[0];
      if (locked && locked.unitId !== state.select.value) {
        showError(
          box,
          "O carrinho é da unidade " +
            locked.unitName +
            ". Esvazie ou finalize para comprar em outra loja.",
        );
        return;
      }
      var existing = items.find(function (item) {
        return item.lineId === lineId;
      });
      var targetQty = (existing ? existing.qty : 0) + amount;
      add.disabled = true;
      var catalogId = box.getAttribute("data-catalog-id") || "";
      var request = existing && existing.wooKey
        ? window.pmWoo.setQty(existing.wooKey, wooId, targetQty, catalogId)
        : window.pmWoo.push(wooId, amount, catalogId);
      request.then(function (line) {
        if (!line) throw new Error("woo");
        var saved = existing || {
          lineId: lineId,
          id: box.getAttribute("data-catalog-id"),
          name: box.getAttribute("data-name"),
          image: photo ? photo.getAttribute("src") || photo.src : "",
          duration: box.getAttribute("data-duration"),
          sku: box.getAttribute("data-sku"),
          unitId: state.select.value,
          unitName: option.getAttribute("data-unit-name") || option.textContent,
          city: option.getAttribute("data-city") || "",
          stateName: option.getAttribute("data-state") || "",
          priceCents: state.sale,
          variationId: option.getAttribute("data-variation") || "",
          productId: box.getAttribute("data-product-id") || "",
          wooOption: option.getAttribute("data-woo-option") || "",
        };
        // Nunca herdar qty fundida do Woo (esfoliação + cera no mesmo SKU).
        saved.qty = targetQty;
        saved.wooKey = line.key;
        saved.wooId = wooId;
        if (!existing) items.push(saved);
        writeCart(items);
        var note = box.querySelector("[data-pm-added]");
        if (note) {
          note.textContent = box.getAttribute("data-name") + " adicionado · " + (option.getAttribute("data-unit-name") || "");
          note.classList.remove("hidden");
        }
      }).catch(function () {
        showError(box, "Não foi possível enviar este item ao carrinho da loja.");
      }).then(function () {
        add.disabled = false;
      });
    });
  }

  function syncAudienceFromProductUrl() {
    var path = (location.pathname || "/").replace(/\/$/, "") || "/";
    var match = path.match(/^\/produto\/([^/]+)$/);
    if (!match) return;
    var id = decodeURIComponent(match[1]);
    if (id.slice(-5) !== "-masc") return;
    var root = document.querySelector("[data-audience]");
    if (!root) return;
    // Já masculino no HTML: não reescreve classes (evita flash).
    if (root.getAttribute("data-audience") === "masculino") return;
    root.setAttribute("data-audience", "masculino");
    document.querySelectorAll("[aria-label='Público'] a, [role='navigation'][aria-label='Público'] a").forEach(function (link) {
      var href = (link.getAttribute("href") || "").replace(/\/$/, "") || "/";
      var isMale = href === "/masculino";
      if (isMale) {
        link.className =
          "rounded-full bg-primary px-5 py-1.5 text-xs font-semibold tracking-wide text-on-primary uppercase";
      } else {
        link.className =
          "rounded-full px-5 py-1.5 text-xs font-semibold tracking-wide text-primary uppercase hover:bg-primary/10";
      }
    });
  }

  paintBadge(readCart());
  syncAudienceFromProductUrl();
  document.querySelectorAll("[data-pm-buy]").forEach(bindBuy);
})();
