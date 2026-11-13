/**
 * Motor Black Nov (e-commerce) — espelho de src/lib/black-nov-campaign.ts
 * Carrega black-nov-campaign.json e expõe window.pmBlackNov.
 */
(function () {
  "use strict";

  var cfg = null;
  var tierP = new Set();
  var tierM = new Set();
  var tierG = new Set();

  function applyCfg(data) {
    cfg = data || null;
    tierP = new Set((cfg && cfg.ceraTierP) || []);
    tierM = new Set((cfg && cfg.ceraTierM) || []);
    tierG = new Set((cfg && cfg.ceraTierG) || []);
  }

  function forcedPhase() {
    try {
      var v = String(window.__PM_BLACK_PHASE__ || "").toLowerCase();
      if (v === "esquenta" || v === "black_week" || v === "off") return v;
    } catch (e) {}
    return null;
  }

  function phaseAt(now) {
    var forced = forcedPhase();
    if (forced) return forced;
    if (!cfg) return "off";
    var t = (now || new Date()).getTime();
    var a = Date.parse(cfg.esquentaStart);
    var b = Date.parse(cfg.esquentaEnd);
    var c = Date.parse(cfg.blackWeekStart);
    var d = Date.parse(cfg.blackWeekEnd);
    if (t >= a && t <= b) return "esquenta";
    if (t >= c && t <= d) return "black_week";
    return "off";
  }

  function isExcluded(id, method) {
    if (!cfg) return true;
    var pid = String(id || "");
    var prefixes = cfg.excludeIdPrefixes || [];
    for (var i = 0; i < prefixes.length; i++) {
      if (pid === prefixes[i] || pid.indexOf(prefixes[i]) === 0) return true;
    }
    var m = String(method || "").toLowerCase();
    var methods = cfg.excludeMethods || [];
    if (m && methods.indexOf(m) !== -1) return true;
    return false;
  }

  function familyFor(id, method) {
    if (isExcluded(id, method)) return "excluded";
    var m = String(method || "").toLowerCase();
    var pid = String(id || "");
    if (m === "laser" || pid.indexOf("-laser") !== -1 || /laser$/.test(pid)) return "laser";
    if (m === "cera" || m === "esfoliacao") return "cera_esf";
    if (
      pid.indexOf("-cera") !== -1 ||
      pid.indexOf("esfoliacao") !== -1 ||
      pid === "realce" ||
      pid === "henna" ||
      pid.indexOf("tintura-pelos") !== -1
    ) {
      return "cera_esf";
    }
    return "excluded";
  }

  function ceraTier(id) {
    var pid = String(id || "");
    if (tierP.has(pid)) return "P";
    if (tierM.has(pid)) return "M";
    if (tierG.has(pid)) return "G";
    return "G";
  }

  function countDistinct(lines, family) {
    var ids = {};
    (lines || []).forEach(function (line) {
      if (!line || !line.id) return;
      if (familyFor(line.id, line.method) !== family) return;
      ids[String(line.id)] = true;
    });
    return Object.keys(ids).length;
  }

  function discountRate(productId, method, lines, now) {
    var phase = phaseAt(now);
    if (phase === "off" || !cfg) return null;
    var family = familyFor(productId, method);
    if (family === "excluded") return null;
    var thr = cfg.multiThreshold || 3;

    if (family === "laser") {
      var n = countDistinct(lines, "laser");
      var table = cfg.laser[phase];
      return n >= thr ? table.multi : table.any;
    }

    var m = String(method || "").toLowerCase();
    var isEsf = m === "esfoliacao" || String(productId).indexOf("esfoliacao") === 0;
    if (phase === "esquenta") {
      var n2 = countDistinct(lines, "cera_esf");
      var t2 = cfg.ceraEsf.esquenta;
      return n2 >= thr ? t2.multi : t2.any;
    }
    if (isEsf) return cfg.ceraEsf.black_week_esfoliacao;
    return cfg.ceraEsf.black_week_cera[ceraTier(productId)];
  }

  function baseCents(originalCents, skipDiscount, method) {
    var base = Math.max(0, Math.round(Number(originalCents) || 0));
    if (!skipDiscount) return base;
    var m = String(method || "").toLowerCase();
    if (m === "cera" || m === "esfoliacao") return Math.round(base / 0.95);
    return base;
  }

  function applyRate(originalCents, rate, skipDiscount, method) {
    var oldPriceCents = baseCents(originalCents, skipDiscount, method);
    return {
      oldPriceCents: oldPriceCents,
      priceCents: Math.round(oldPriceCents * (1 - rate)),
      discountRate: rate,
    };
  }

  function unitPrice(row, lines, now) {
    if (!row) return null;
    var rate = discountRate(row.id, row.method, lines || [{ id: row.id, method: row.method }], now);
    var original = row.originalCents != null ? row.originalCents : row.priceCents;
    if (rate == null) {
      return {
        priceCents: Number(row.priceCents) || 0,
        oldPriceCents: row.skipDiscount ? undefined : Number(original) || undefined,
      };
    }
    return applyRate(original, rate, !!row.skipDiscount, row.method);
  }

  function multiHint(lines, family, now) {
    var phase = phaseAt(now);
    if (phase === "off" || !cfg) return null;
    var thr = cfg.multiThreshold || 3;
    if (family === "laser") {
      var n = countDistinct(lines, "laser");
      if (n >= thr) return null;
      return { need: thr - n, nextRate: cfg.laser[phase].multi, label: "laser" };
    }
    if (family === "cera_esf" && phase === "esquenta") {
      var n2 = countDistinct(lines, "cera_esf");
      if (n2 >= thr) return null;
      return { need: thr - n2, nextRate: cfg.ceraEsf.esquenta.multi, label: "cera e esfoliação" };
    }
    return null;
  }

  /** Rótulo do desconto de campanha no resumo (carrinho / checkout). */
  function discountLabel(now) {
    var phase = phaseAt(now);
    if (phase === "esquenta") return "Desconto Esquenta Black";
    if (phase === "black_week") return "Desconto Black Week";
    return null;
  }

  function load(url) {
    var src =
      url ||
      ((window.location && window.location.origin ? window.location.origin : "") +
        "/wp-content/uploads/pm-home/black-nov-campaign.json");
    return fetch(src + (src.indexOf("?") >= 0 ? "&" : "?") + "v=black1", { credentials: "same-origin" })
      .then(function (r) {
        return r.ok ? r.json() : null;
      })
      .then(function (data) {
        if (data) applyCfg(data);
        return cfg;
      })
      .catch(function () {
        return null;
      });
  }

  window.pmBlackNov = {
    load: load,
    applyCfg: applyCfg,
    phaseAt: phaseAt,
    discountRate: discountRate,
    discountLabel: discountLabel,
    unitPrice: unitPrice,
    multiHint: multiHint,
    familyFor: familyFor,
    countDistinct: countDistinct,
    ready: function () {
      return !!cfg;
    },
  };
})();
