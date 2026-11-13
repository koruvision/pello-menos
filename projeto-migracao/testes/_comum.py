# -*- coding: utf-8 -*-
"""Ajudantes dos testes do treino de migração.

PM_BASE escolhe o site testado. Padrão: o destino de ensaio. Para a loja oficial, só com GO explícito:
  $env:PM_BASE = "https://loja.pellomenos.com.br"
Nenhum teste envia formulário de pagamento.
"""
import os
from pathlib import Path

BASE = os.environ.get("PM_BASE", "https://pellomenosoficialteste.companygenesis.com.br").rstrip("/")
HERE = Path(__file__).resolve().parent
OUT = HERE / "saida"
OUT.mkdir(exist_ok=True)
REF = HERE.parent / "fase0-finalizar-pagamento.html"
ENV_FILE = Path(os.environ.get("PM_ENV_FILE", HERE.parent / ".secrets" / "oficialteste.env"))


def read_env(path=None):
    values = {}
    for line in Path(path or ENV_FILE).read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def cart_state(page):
    return page.evaluate(
        """async () => {
          const response = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin', cache: 'no-store' });
          const data = await response.json();
          return { status: response.status, items: (data.items || []).map((item) => ({ id: item.id, name: item.name, qty: item.quantity, key: item.key })) };
        }"""
    )


def clear_cart(page):
    page.evaluate(
        """async () => {
          localStorage.removeItem('pm-cart-v1');
          let response = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
          let nonce = response.headers.get('Nonce') || '';
          let data = await response.json();
          for (const item of data.items || []) {
            response = await fetch('/wp-json/wc/store/v1/cart/remove-item', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: nonce },
              body: JSON.stringify({ key: item.key })
            });
            nonce = response.headers.get('Nonce') || nonce;
          }
        }"""
    )


def choose_unit(page, which="first"):
    select = page.locator("[data-pm-unit]").first
    options = select.locator("option")
    values = [options.nth(i).get_attribute("value") or "" for i in range(options.count())]
    values = [v for v in values if v]
    if not values:
        return ""
    value = values[0] if which == "first" else values[-1]
    select.select_option(value)
    return value


def add_current(page):
    page.locator("[data-pm-add]").first.click()
    page.wait_for_timeout(2500)
    note = page.locator("[data-pm-added]").first
    error = page.locator("[data-pm-unit-error]").first
    return {
        "note": note.inner_text().strip() if note.count() and note.is_visible() else "",
        "error": error.inner_text().strip() if error.count() and error.is_visible() else "",
    }


def local_cart(page):
    return page.evaluate("() => JSON.parse(localStorage.getItem('pm-cart-v1') || 'null')")
