(function () {
  var root = document.querySelector("[data-pm-search-page]");
  if (!root) return;

  function params() {
    return new URLSearchParams(window.location.search);
  }

  function parseCategories(raw) {
    return String(raw || "")
      .split(",")
      .map(function (part) {
        return part.trim();
      })
      .filter(Boolean);
  }

  function readFilters() {
    var p = params();
    var minRaw = (p.get("min") || "").replace(",", ".");
    var maxRaw = (p.get("max") || "").replace(",", ".");
    var minNum = minRaw ? Number(minRaw) : NaN;
    var maxNum = maxRaw ? Number(maxRaw) : NaN;
    var sort = p.get("sort") || "relevance";
    if (sort !== "name" && sort !== "price-asc" && sort !== "price-desc") {
      sort = "relevance";
    }
    var audienceRaw = p.get("audience") || "";
    var audience =
      audienceRaw === "masculino"
        ? "masculino"
        : audienceRaw === "feminino"
          ? "feminino"
          : "todos";
    var sessionsRaw = p.get("sessions") || "";
    var sessions =
      sessionsRaw === "avulso" || sessionsRaw === "pacote" ? sessionsRaw : "";
    var categories = parseCategories(p.get("category") || "");
    return {
      q: (p.get("q") || "").trim().toLowerCase(),
      categories: categories,
      category: categories[0] || "",
      method: (p.get("method") || "").trim(),
      min: Number.isFinite(minNum) ? Math.round(minNum * 100) : null,
      max: Number.isFinite(maxNum) ? Math.round(maxNum * 100) : null,
      sort: sort,
      audience: audience,
      sessions: sessions,
      unit: (p.get("unit") || "").trim(),
      promo: p.get("promo") === "1" || p.get("promo") === "true",
    };
  }

  function buildHref(next) {
    var cur = readFilters();
    var f = Object.assign({}, cur, next || {});
    if (next && Object.prototype.hasOwnProperty.call(next, "categories")) {
      f.categories = next.categories || [];
      f.category = f.categories[0] || "";
    } else if (next && Object.prototype.hasOwnProperty.call(next, "category")) {
      f.categories = next.category ? [next.category] : [];
      f.category = next.category || "";
    }
    var p = new URLSearchParams();
    if (f.q) p.set("q", f.q);
    if (f.audience && f.audience !== "todos") p.set("audience", f.audience);
    if (f.categories && f.categories.length) {
      p.set("category", f.categories.join(","));
    }
    if (f.method) p.set("method", f.method);
    if (f.min != null) p.set("min", (f.min / 100).toFixed(2));
    if (f.max != null) p.set("max", (f.max / 100).toFixed(2));
    if (f.sort && f.sort !== "relevance") p.set("sort", f.sort);
    if (f.sessions) p.set("sessions", f.sessions);
    if (f.unit) p.set("unit", f.unit);
    if (f.promo) p.set("promo", "1");
    var qs = p.toString();
    return qs ? "/busca?" + qs : "/busca";
  }

  function go(next) {
    window.location.href = buildHref(next);
  }

  function matchCard(card, f) {
    var audience = card.getAttribute("data-audience") || "";
    if (f.audience !== "todos" && audience !== f.audience) return false;
    if (f.q) {
      var hay = (card.getAttribute("data-haystack") || "").toLowerCase();
      if (hay.indexOf(f.q) === -1) return false;
    }
    if (f.categories && f.categories.length) {
      var cat = card.getAttribute("data-category") || "";
      if (f.categories.indexOf(cat) === -1) return false;
    }
    if (f.method && (card.getAttribute("data-method") || "") !== f.method) {
      return false;
    }
    var price = Number(card.getAttribute("data-price-cents") || "0");
    if (f.min != null && price < f.min) return false;
    if (f.max != null && price > f.max) return false;
    if (f.sessions) {
      var sessions = card.getAttribute("data-sessions") || "";
      if (sessions !== f.sessions) return false;
    }
    if (f.unit) {
      var units = (card.getAttribute("data-units") || "").split(",");
      if (units.indexOf(f.unit) === -1) return false;
    }
    if (f.promo && (card.getAttribute("data-promo") || "0") !== "1") {
      return false;
    }
    return true;
  }

  function countActive(f) {
    var n = 0;
    if (f.audience === "feminino" || f.audience === "masculino") n += 1;
    if (f.categories && f.categories.length) n += 1;
    if (f.method) n += 1;
    if (f.min != null || f.max != null) n += 1;
    if (f.sessions) n += 1;
    if (f.unit) n += 1;
    if (f.promo) n += 1;
    return n;
  }

  function selectedAreas(scope) {
    return Array.prototype.slice
      .call((scope || root).querySelectorAll("[data-pm-search-area]:checked"))
      .map(function (el) {
        return el.value;
      });
  }

  function selectedAudience(scope) {
    var checked = (scope || root).querySelector(
      "[data-pm-search-audience-group] input[type=radio]:checked"
    );
    if (!checked) return "todos";
    return checked.value || "todos";
  }

  function readDraftFrom(scope) {
    var minEl = scope.querySelector("[data-pm-search-min]");
    var maxEl = scope.querySelector("[data-pm-search-max]");
    var methodEl = scope.querySelector("[data-pm-search-method]");
    var minRaw = ((minEl && minEl.value) || "").trim().replace(",", ".");
    var maxRaw = ((maxEl && maxEl.value) || "").trim().replace(",", ".");
    var minNum = minRaw ? Number(minRaw) : NaN;
    var maxNum = maxRaw ? Number(maxRaw) : NaN;
    return {
      audience: selectedAudience(scope),
      categories: selectedAreas(scope),
      method: (methodEl && methodEl.value) || "",
      min: Number.isFinite(minNum) ? Math.round(minNum * 100) : null,
      max: Number.isFinite(maxNum) ? Math.round(maxNum * 100) : null,
    };
  }

  function syncAudienceRadios(audience) {
    root.querySelectorAll("[data-pm-search-audience-group]").forEach(function (group) {
      group.querySelectorAll('input[type="radio"]').forEach(function (input) {
        input.checked = input.value === audience;
      });
    });
  }

  function syncAreaChecks(categories) {
    var set = {};
    (categories || []).forEach(function (id) {
      set[id] = true;
    });
    root.querySelectorAll("[data-pm-search-area]").forEach(function (input) {
      input.checked = !!set[input.value];
    });
  }

  function apply() {
    var f = readFilters();
    var cards = Array.prototype.slice.call(
      root.querySelectorAll("[data-pm-search-card]")
    );
    var visible = cards.filter(function (card) {
      return matchCard(card, f);
    });

    if (f.sort === "name") {
      visible.sort(function (a, b) {
        return (a.getAttribute("data-name") || "").localeCompare(
          b.getAttribute("data-name") || "",
          "pt-BR"
        );
      });
    } else if (f.sort === "price-asc") {
      visible.sort(function (a, b) {
        return (
          Number(a.getAttribute("data-price-cents") || 0) -
          Number(b.getAttribute("data-price-cents") || 0)
        );
      });
    } else if (f.sort === "price-desc") {
      visible.sort(function (a, b) {
        return (
          Number(b.getAttribute("data-price-cents") || 0) -
          Number(a.getAttribute("data-price-cents") || 0)
        );
      });
    } else if (f.q) {
      visible.sort(function (a, b) {
        var an = (a.getAttribute("data-name") || "").indexOf(f.q) === 0 ? 0 : 1;
        var bn = (b.getAttribute("data-name") || "").indexOf(f.q) === 0 ? 0 : 1;
        if (an !== bn) return an - bn;
        return (a.getAttribute("data-name") || "").localeCompare(
          b.getAttribute("data-name") || "",
          "pt-BR"
        );
      });
    }

    var grid = root.querySelector("[data-pm-search-grid]");
    cards.forEach(function (card) {
      card.classList.add("hidden");
    });
    visible.forEach(function (card) {
      card.classList.remove("hidden");
      if (grid) grid.appendChild(card);
    });

    var empty = root.querySelector("[data-pm-search-empty]");
    if (empty) empty.classList.toggle("hidden", visible.length > 0);
    if (grid) grid.classList.toggle("hidden", visible.length === 0);

    var count = root.querySelector("[data-pm-search-count]");
    if (count) {
      count.textContent = "Tratamentos (" + visible.length + ")";
    }

    var qLabel = root.querySelector("[data-pm-search-query-label]");
    var qRaw = (params().get("q") || "").trim();
    if (qLabel) {
      qLabel.textContent = qRaw ? 'Resultados para "' + qRaw + '"' : "";
      qLabel.classList.toggle("hidden", !qRaw);
    }

    var input = root.querySelector("[data-pm-search-input]");
    if (input && document.activeElement !== input) {
      input.value = qRaw;
    }
    root.querySelectorAll("[data-pm-search-min]").forEach(function (minEl) {
      if (document.activeElement !== minEl) {
        minEl.value = f.min != null ? String(f.min / 100) : "";
      }
    });
    root.querySelectorAll("[data-pm-search-max]").forEach(function (maxEl) {
      if (document.activeElement !== maxEl) {
        maxEl.value = f.max != null ? String(f.max / 100) : "";
      }
    });

    syncAudienceRadios(f.audience);
    syncAreaChecks(f.categories);
    root.querySelectorAll("[data-pm-search-method]").forEach(function (el) {
      el.value = f.method || "";
    });
    var sortEl = root.querySelector("[data-pm-search-sort]");
    if (sortEl) sortEl.value = f.sort;

    var region = root.querySelector("[data-pm-search-quick-region]");
    if (region) region.value = f.categories[0] || "";
    var sessionsEl = root.querySelector("[data-pm-search-quick-sessions]");
    if (sessionsEl) sessionsEl.value = f.sessions || "";
    var unitEl = root.querySelector("[data-pm-search-quick-unit]");
    if (unitEl) unitEl.value = f.unit || "";
    var promoBtn = root.querySelector("[data-pm-search-quick-promo]");
    if (promoBtn) {
      promoBtn.setAttribute("aria-pressed", f.promo ? "true" : "false");
      promoBtn.classList.toggle("bg-primary", f.promo);
      promoBtn.classList.toggle("text-on-primary", f.promo);
    }

    var badge = root.querySelector("[data-pm-search-filter-count]");
    var active = countActive(f);
    if (badge) {
      badge.textContent = String(active);
      badge.classList.toggle("hidden", active === 0);
    }
  }

  function closeDrawer() {
    var drawer = root.querySelector("[data-pm-search-drawer]");
    if (drawer) drawer.classList.add("hidden");
    document.documentElement.classList.remove("overflow-hidden");
  }

  function openDrawer() {
    var drawer = root.querySelector("[data-pm-search-drawer]");
    if (drawer) drawer.classList.remove("hidden");
    document.documentElement.classList.add("overflow-hidden");
  }

  var openBtn = root.querySelector("[data-pm-search-open-drawer]");
  if (openBtn) {
    openBtn.addEventListener("click", openDrawer);
  }

  root.querySelectorAll("[data-pm-search-drawer] [aria-label='Fechar filtros'], [data-pm-search-drawer] [aria-label='Fechar']").forEach(function (btn) {
    btn.addEventListener("click", closeDrawer);
  });

  root.querySelectorAll("[data-pm-search-apply]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var scope =
        btn.closest("[data-pm-search-filters-form]") ||
        btn.closest("[data-pm-search-sidebar]") ||
        btn.closest("[data-pm-search-drawer]") ||
        root;
      var draft = readDraftFrom(scope);
      var f = readFilters();
      go({
        audience: draft.audience,
        categories: draft.categories,
        method: draft.method,
        min: draft.min,
        max: draft.max,
        sessions: f.sessions,
        unit: f.unit,
        promo: f.promo,
        q: f.q,
        sort: f.sort,
      });
    });
  });

  root.querySelectorAll("[data-pm-search-clear]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var f = readFilters();
      go({
        q: f.q,
        sort: f.sort,
        audience: "todos",
        categories: [],
        category: "",
        method: "",
        min: null,
        max: null,
        sessions: "",
        unit: "",
        promo: false,
      });
    });
  });

  var region = root.querySelector("[data-pm-search-quick-region]");
  if (region) {
    region.addEventListener("change", function () {
      go({ categories: region.value ? [region.value] : [] });
    });
  }
  var sessionsEl = root.querySelector("[data-pm-search-quick-sessions]");
  if (sessionsEl) {
    sessionsEl.addEventListener("change", function () {
      go({ sessions: sessionsEl.value || "" });
    });
  }
  var unitEl = root.querySelector("[data-pm-search-quick-unit]");
  if (unitEl) {
    unitEl.addEventListener("change", function () {
      go({ unit: unitEl.value || "" });
    });
  }
  var promoBtn = root.querySelector("[data-pm-search-quick-promo]");
  if (promoBtn) {
    promoBtn.addEventListener("click", function () {
      var f = readFilters();
      go({ promo: !f.promo });
    });
  }

  var sortEl = root.querySelector("[data-pm-search-sort]");
  if (sortEl) {
    sortEl.addEventListener("change", function () {
      go({ sort: sortEl.value || "relevance" });
    });
  }

  apply();
})();
