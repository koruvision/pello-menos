(function () {
  var root = document.querySelector("[data-pm-account-page]");
  if (!root) return;

  var SPINNER_SVG =
    '<svg data-pm-auth-spinner class="h-4 w-4 animate-spin" viewBox="0 0 24 24" aria-hidden="true" fill="none">' +
    '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-opacity="0.25" stroke-width="3"></circle>' +
    '<path d="M22 12a10 10 0 0 1-10 10" stroke="currentColor" stroke-width="3" stroke-linecap="round"></path>' +
    "</svg>";

  function call(op, fields) {
    var body = new URLSearchParams();
    body.set("action", "pm_account");
    body.set("op", op);
    Object.keys(fields || {}).forEach(function (key) {
      body.set(key, fields[key]);
    });
    return fetch("/wp-admin/admin-ajax.php", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    }).then(function (response) {
      return response.json();
    });
  }

  var guest = root.querySelector("[data-pm-guest]");
  var member = root.querySelector("[data-pm-member]");
  var hello = root.querySelector("[data-pm-hello]");
  var message = root.querySelector("[data-pm-message]");
  var ordersBox = root.querySelector("[data-pm-orders]");
  var detailBox = root.querySelector("[data-pm-order-detail]");
  var addressForm = root.querySelector("[data-pm-address]");
  var authForm = root.querySelector("[data-pm-auth]");
  var authMode = "login";

  function showMessage(text) {
    if (!message) return;
    message.textContent = text || "";
    message.classList.toggle("hidden", !text);
  }

  var CHECKING_SHELL = "mx-auto w-full max-w-xl px-container-margin py-10";

  function clearChecking() {
    var panel = root.querySelector("[data-pm-account-checking]");
    if (panel) panel.remove();
    root.removeAttribute("data-pm-account-state");
    root.className = "mx-auto w-full max-w-3xl px-container-margin py-16";
  }

  function paintChecking() {
    root.setAttribute("data-pm-account-state", "checking");
    root.className = CHECKING_SHELL;
    if (guest) guest.classList.add("hidden");
    if (member) member.classList.add("hidden");
    if (message) {
      message.textContent = "";
      message.classList.add("hidden");
    }
    var existing = root.querySelector("[data-pm-account-checking]");
    if (existing) return;
    var panel = document.createElement("div");
    panel.setAttribute("data-pm-account-checking", "");
    // Inline CSS: Tailwind purge nao inclui utilities so de JS.
    panel.style.cssText =
      "display:flex;flex-direction:column;align-items:center;justify-content:center;" +
      "width:100%;min-height:calc(100dvh - 200px);text-align:center;gap:1.25rem;box-sizing:border-box";
    panel.innerHTML =
      '<style>@keyframes pm-account-spin{to{transform:rotate(360deg)}}</style>' +
      '<span style="display:block;width:2.75rem;height:2.75rem;border-radius:9999px;' +
      "border:3px solid rgba(139,21,56,0.2);border-top-color:#8b1538;" +
      'animation:pm-account-spin 0.75s linear infinite" aria-hidden="true"></span>' +
      '<p style="margin:0;font-size:0.875rem;line-height:1.25rem;color:#6b635c" role="status">Verificando login...</p>';
    root.insertBefore(panel, root.firstChild);
  }

  function showMember(data) {
    clearChecking();
    guest.classList.add("hidden");
    member.classList.remove("hidden");
    hello.textContent = data.name || data.email || "";
    loadOrders();
    loadAddress();
  }

  function showGuest() {
    clearChecking();
    member.classList.add("hidden");
    guest.classList.remove("hidden");
  }

  function hideDetail() {
    if (!detailBox) return;
    detailBox.classList.add("hidden");
    detailBox.innerHTML = "";
  }

  function showDetail(orderId) {
    if (!detailBox) return;
    detailBox.classList.remove("hidden");
    detailBox.innerHTML = '<p class="text-sm text-on-surface-variant">Carregando detalhes…</p>';
    call("order", { order_id: String(orderId) }).then(function (data) {
      if (!data || !data.ok || !data.order) {
        detailBox.innerHTML =
          '<p class="text-sm text-primary">' +
          ((data && data.message) || "Não foi possível abrir o pedido.") +
          "</p>";
        return;
      }
      var order = data.order;
      var rows = (order.items || [])
        .map(function (item) {
          return (
            '<div class="flex justify-between gap-3 border-b border-outline/30 py-2 text-sm">' +
            "<span>" +
            item.name +
            " × " +
            item.qty +
            "</span><span class=\"font-semibold text-primary\">" +
            item.total +
            "</span></div>"
          );
        })
        .join("");
      var bill = order.billing || {};
      detailBox.innerHTML =
        '<div class="rounded-2xl border border-outline/40 bg-white p-4">' +
        '<div class="flex items-start justify-between gap-3">' +
        "<div><p class=\"text-xs uppercase tracking-wide text-primary\">Pedido " +
        order.number +
        "</p>" +
        '<p class="mt-1 text-sm text-on-surface-variant">' +
        order.date +
        " · " +
        order.status +
        "</p></div>" +
        '<button type="button" data-pm-order-close class="text-sm font-semibold text-primary underline">Fechar</button></div>' +
        '<div class="mt-4">' +
        rows +
        "</div>" +
        '<p class="mt-4 flex justify-between text-base"><span class="font-semibold">Total</span><span class="font-[family-name:var(--font-display)] text-xl text-primary">' +
        order.total +
        "</span></p>" +
        (order.payment
          ? '<p class="mt-2 text-xs text-on-surface-variant">Pagamento: ' + order.payment + "</p>"
          : "") +
        (bill.name || bill.address
          ? '<p class="mt-4 text-xs text-on-surface-variant">' +
            [bill.name, bill.address, bill.email, bill.phone].filter(Boolean).join(" · ") +
            "</p>"
          : "") +
        "</div>";
      var close = detailBox.querySelector("[data-pm-order-close]");
      if (close) close.addEventListener("click", hideDetail);
    });
  }

  function loadOrders() {
    call("orders").then(function (data) {
      if (!data || !data.ok) return;
      if (!data.orders || !data.orders.length) {
        ordersBox.innerHTML =
          '<p class="text-sm text-white/70">Você ainda não possui pedidos. Quando realizar sua primeira compra, ela aparecerá aqui.</p>' +
          '<a href="/" class="btn-lux btn-lux-primary mt-4 inline-flex rounded-full px-6 py-3 text-sm font-semibold text-on-primary">Continuar comprando</a>';
        return;
      }
      ordersBox.innerHTML = "";
      data.orders.forEach(function (order) {
        var card = document.createElement("article");
        card.className =
          "mt-3 rounded-2xl border border-outline/40 bg-white p-4 text-sm text-on-surface";
        var preview = (order.itemsPreview || []).join(", ");
        card.innerHTML =
          '<div class="flex flex-wrap items-start justify-between gap-3">' +
          "<div><p class=\"font-semibold text-primary\">Pedido " +
          order.number +
          "</p>" +
          '<p class="mt-1 text-on-surface-variant">' +
          order.date +
          " · " +
          order.status +
          "</p>" +
          (preview
            ? '<p class="mt-1 text-xs text-on-surface-variant">' + preview + "</p>"
            : "") +
          '</div><p class="font-semibold text-primary">' +
          order.total +
          "</p></div>" +
          '<button type="button" class="mt-3 text-sm font-semibold text-primary underline" data-pm-order-open="' +
          order.id +
          '">Ver detalhes</button>';
        ordersBox.appendChild(card);
      });
      ordersBox.querySelectorAll("[data-pm-order-open]").forEach(function (button) {
        button.addEventListener("click", function () {
          showDetail(button.getAttribute("data-pm-order-open"));
        });
      });
    });
  }

  function loadAddress() {
    call("address").then(function (data) {
      if (!data || !data.address) return;
      Object.keys(data.address).forEach(function (key) {
        var input = addressForm.querySelector('[name="' + key + '"]');
        if (input) input.value = data.address[key] || "";
      });
    });
  }

  function setAuthMode(mode) {
    authMode = mode === "register" ? "register" : "login";
    showMessage("");
    var title = root.querySelector("[data-pm-auth-title]");
    var subtitle = root.querySelector("[data-pm-auth-subtitle]");
    var label = root.querySelector("[data-pm-auth-submit-label]");
    var password = authForm && authForm.querySelector('[name="password"]');
    if (title) title.textContent = authMode === "login" ? "Entrar" : "Cadastre-se";
    if (subtitle) {
      subtitle.textContent =
        authMode === "login"
          ? "Acesse para acompanhar pedidos e ofertas."
          : "Cadastre-se para comprar mais rápido.";
    }
    if (label) label.textContent = authMode === "login" ? "Acessar" : "Cadastre-se";
    if (password) {
      password.setAttribute(
        "autocomplete",
        authMode === "login" ? "current-password" : "new-password"
      );
    }
    root.querySelectorAll("[data-pm-auth-mode]").forEach(function (button) {
      var active = button.getAttribute("data-pm-auth-mode") === authMode;
      button.className = active
        ? "btn-lux btn-lux-gold rounded-full py-2 text-sm font-semibold text-on-secondary-container"
        : "rounded-full py-2 text-sm text-white/70";
    });
    root.querySelectorAll("[data-pm-auth-login-only]").forEach(function (el) {
      el.classList.toggle("hidden", authMode !== "login");
    });
    root.querySelectorAll("[data-pm-auth-register-only]").forEach(function (el) {
      el.classList.toggle("hidden", authMode !== "register");
    });
    if (authForm) {
      ["username", "email", "name", "phone"].forEach(function (name) {
        var input = authForm.querySelector('[name="' + name + '"]');
        if (!input) return;
        if (authMode === "login") {
          input.required = name === "username";
        } else {
          input.required = name === "email" || name === "name" || name === "phone";
        }
      });
    }
  }

  function setAuthBusy(busy) {
    if (!authForm) return;
    var button = authForm.querySelector("[data-pm-auth-submit]");
    var label = authForm.querySelector("[data-pm-auth-submit-label]");
    if (!button || !label) return;
    button.disabled = !!busy;
    button.classList.toggle("opacity-80", !!busy);
    var spinner = button.querySelector("[data-pm-auth-spinner]");
    if (busy) {
      if (!spinner) button.insertAdjacentHTML("afterbegin", SPINNER_SVG);
      label.textContent = authMode === "login" ? "Entrando…" : "Cadastrando…";
    } else {
      if (spinner) spinner.remove();
      label.textContent = authMode === "login" ? "Acessar" : "Cadastre-se";
    }
  }

  paintChecking();
  call("me")
    .then(function (data) {
      if (data && data.loggedIn) showMember(data);
      else showGuest();
    })
    .catch(function () {
      showGuest();
    });

  root.querySelectorAll("[data-pm-auth-mode]").forEach(function (button) {
    button.addEventListener("click", function () {
      setAuthMode(button.getAttribute("data-pm-auth-mode"));
    });
  });
  setAuthMode("login");

  if (authForm) {
    authForm.addEventListener("submit", function (event) {
      event.preventDefault();
      showMessage("");
      var form = event.currentTarget;
      setAuthBusy(true);
      var request =
        authMode === "login"
          ? call("login", {
              username: form.username.value,
              password: form.password.value,
              remember: form.remember && form.remember.checked ? "1" : "",
            })
          : call("register", {
              name: form.name.value,
              phone: form.phone.value,
              email: form.email.value,
              password: form.password.value,
            });
      request
        .then(function (data) {
          if (!data || !data.ok) {
            showMessage(
              (data && data.message) ||
                (authMode === "login"
                  ? "Não foi possível entrar."
                  : "Não foi possível cadastrar.")
            );
            return;
          }
          if (data.loggedIn) showMember(data);
          else showMessage(data.message || "Conta criada. Entre com o e-mail e a senha.");
        })
        .catch(function () {
          showMessage(
            authMode === "login"
              ? "Não foi possível entrar."
              : "Não foi possível cadastrar."
          );
        })
        .then(function () {
          setAuthBusy(false);
        });
    });
  }

  root.querySelector("[data-pm-logout]").addEventListener("click", function () {
    call("logout").then(function () {
      window.location.href = "/minha-conta/";
    });
  });

  addressForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var fields = {};
    addressForm.querySelectorAll("input").forEach(function (input) {
      fields[input.name] = input.value;
    });
    call("save-address", fields).then(function (data) {
      showMessage(data && data.ok ? "Endereço salvo." : (data && data.message) || "Não foi possível salvar.");
    });
  });
})();
