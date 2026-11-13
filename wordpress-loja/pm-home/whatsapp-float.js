(function () {
  // Reunião 29/10: a consultora (Mariana) só atende laser; demais serviços se compram no site.
  var BUBBLE_TEXT = "D\u00favidas sobre laser? Fale com a nossa consultora \uD83D\uDC9C";
  var INTERVAL_MS = 30000;
  var VISIBLE_MS = 5000;
  var HREF =
    "https://wa.me/552125494265?text=" +
    encodeURIComponent(
      "Olá! Quero tirar dúvidas sobre a depilação a laser da Pello Menos. (Cera, linha e esfoliação eu compro direto no site.)"
    );

  function blocked() {
    var path = (location.pathname || "/").replace(/\/$/, "") || "/";
    return (
      path === "/carrinho" ||
      path.indexOf("/finalizar-pagamento") === 0 ||
      path.indexOf("/finaliza-compra") === 0 ||
      path.indexOf("/checkout") === 0
    );
  }

  if (blocked()) return;

  if (!document.getElementById("pm-wa-shine-style")) {
    var shineStyle = document.createElement("style");
    shineStyle.id = "pm-wa-shine-style";
    shineStyle.textContent =
      ".pm-wa-shine{position:relative;overflow:hidden}" +
      ".pm-wa-shine>*{position:relative;z-index:1}" +
      ".pm-wa-shine::before{content:'';position:absolute;inset:0;border-radius:inherit;" +
      "background:linear-gradient(105deg,transparent 36%,rgba(255,255,255,.22) 47%," +
      "rgba(255,255,255,.72) 50%,rgba(255,255,255,.22) 53%,transparent 64%);" +
      "transform:translateX(-130%);animation:pm-wa-shine 7.2s ease-in-out infinite;" +
      "pointer-events:none;z-index:0}" +
      "@keyframes pm-wa-shine{0%,8%{transform:translateX(-130%)}22%,100%{transform:translateX(130%)}}" +
      "@media (prefers-reduced-motion:reduce){.pm-wa-shine::before{animation:none}}";
    document.head.appendChild(shineStyle);
  }

  var host = document.createElement("div");
  host.setAttribute("data-pm-whatsapp", "");
  host.style.cssText =
    "position:fixed;right:16px;bottom:96px;z-index:70;display:flex;flex-direction:column;align-items:flex-end;gap:8px;pointer-events:none";
  if (window.matchMedia("(min-width:768px)").matches) host.style.bottom = "32px";

  var bubble = document.createElement("div");
  bubble.style.cssText =
    "display:none;position:relative;max-width:min(calc(100vw - 5rem),260px);pointer-events:auto";
  bubble.innerHTML =
    '<a href="' +
    HREF +
    '" target="_blank" rel="noreferrer" style="display:block;border-radius:22px;border-bottom-right-radius:6px;background:#25D366;color:#fff;padding:12px 16px;font-size:15px;line-height:1.35;text-decoration:none;box-shadow:0 8px 24px rgba(37,211,102,.35)">' +
    BUBBLE_TEXT +
    '</a><button type="button" aria-label="Fechar notificação" style="position:absolute;top:-8px;left:-8px;width:24px;height:24px;border-radius:999px;border:0;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.15);cursor:pointer">×</button>';

  var btn = document.createElement("a");
  btn.href = HREF;
  btn.target = "_blank";
  btn.rel = "noreferrer";
  btn.setAttribute("aria-label", "WhatsApp SAC Pello Menos");
  btn.className = "pm-wa-shine";
  btn.style.cssText =
    "pointer-events:auto;display:flex;width:56px;height:56px;align-items:center;justify-content:center;border-radius:999px;background:#25D366;color:#fff;box-shadow:0 10px 28px rgba(37,211,102,.45);text-decoration:none;position:relative;overflow:hidden";
  btn.innerHTML =
    '<svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M19.05 4.91A9.82 9.82 0 0 0 12.04 2C6.55 2 2.08 6.45 2.08 11.94c0 1.76.46 3.48 1.34 5L2 22l5.2-1.36a10 10 0 0 0 4.84 1.23h.01c5.49 0 9.96-4.45 9.96-9.94a9.87 9.87 0 0 0-2.96-7.02Zm-7.01 15.29h-.01a8.3 8.3 0 0 1-4.23-1.16l-.3-.18-3.08.81.82-3-.2-.31a8.23 8.23 0 0 1-1.27-4.41c0-4.54 3.72-8.24 8.29-8.24 2.21 0 4.29.86 5.85 2.41a8.18 8.18 0 0 1 2.43 5.83c0 4.55-3.73 8.25-8.3 8.25Zm4.55-6.17c-.25-.12-1.47-.72-1.7-.81-.23-.08-.4-.12-.56.13-.17.24-.64.8-.79.97-.14.16-.29.18-.54.06-.25-.13-1.05-.38-2-1.23-.74-.66-1.24-1.47-1.38-1.72-.15-.25-.02-.38.11-.5.11-.11.25-.29.37-.43.13-.15.17-.25.25-.41.08-.17.04-.31-.02-.43-.06-.12-.56-1.34-.76-1.84-.2-.48-.4-.41-.56-.42h-.48c-.17 0-.43.06-.66.31-.23.24-.87.85-.87 2.07 0 1.22.9 2.4 1.02 2.56.13.17 1.77 2.7 4.29 3.79.6.26 1.07.41 1.43.53.6.19 1.15.16 1.58.1.48-.07 1.47-.6 1.68-1.18.21-.58.21-1.07.14-1.18-.06-.10-.23-.17-.48-.29Z"></path></svg>';

  host.appendChild(bubble);
  host.appendChild(btn);
  document.body.appendChild(host);

  // Cards de prova social ficam à esquerda; WhatsApp fica à direita.
  document.querySelectorAll(".fixed.bottom-24.right-4, .fixed.bottom-8.right-4").forEach(function (node) {
    if (node.getAttribute("data-pm-whatsapp") != null) return;
    node.style.right = "auto";
    node.style.left = "16px";
  });

  var dismissed = false;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var closeBtn = bubble.querySelector("button");
  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      dismissed = true;
      bubble.style.display = "none";
    });
  }

  function show() {
    if (dismissed || document.hidden) return;
    bubble.style.display = "block";
    window.setTimeout(
      function () {
        bubble.style.display = "none";
      },
      reduce ? 1 : VISIBLE_MS,
    );
  }

  window.setTimeout(show, INTERVAL_MS);
  window.setInterval(show, INTERVAL_MS);
})();
