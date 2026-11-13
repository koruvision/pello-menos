# -*- coding: utf-8 -*-
"""Cria pedidos Woo via Accesstage server-side (Nilópolis + LMA) com nome/UF corretos."""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
CARD_ENV = ROOT / "projeto-migracao" / ".secrets" / "ot-test-card.env"
CHEAP = json.loads((ROOT / "scripts" / "_loja_cheap_fixture.json").read_text(encoding="utf-8"))
OUT = ROOT / "scripts" / "_smoke_nil_lma_api_orders_result.json"
NAME = "pm-home-test-order-nil-lma"


def load_env(path):
    e = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def card():
    e = load_env(CARD_ENV)
    return {
        "number": e["PM_TEST_CARD_NUMBER"].strip().replace(" ", ""),
        "holder": e["PM_TEST_CARD_HOLDER"].strip(),
        "exp": e["PM_TEST_CARD_EXP"].strip(),
        "cvv": e["PM_TEST_CARD_CVV"].strip(),
    }


def call(method, path, payload=None, timeout=120):
    e = load_env(ENV)
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    base = e["PM_LOJA_URL"].rstrip("/")
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        base + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-nil-lma-api",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode()
        return json.loads(body) if body else {}


CODE = r"""
function pm_live_keys_from_theme() {
    $path = get_stylesheet_directory() . '/functions.php';
    $text = is_readable($path) ? file_get_contents($path) : '';
    $api = array();
    $apikey = array();
    if (preg_match('/\$api\s*=\s*array\((.*?)\);\s*\$apikey\s*=\s*array\((.*?)\);/s', $text, $m)) {
        if (preg_match_all("/'([^']+)'\s*=>\s*'([^']+)'/", $m[1], $mm, PREG_SET_ORDER)) {
            foreach ($mm as $row) { $api[$row[1]] = $row[2]; }
        }
        if (preg_match_all("/'([^']+)'\s*=>\s*'([^']+)'/", $m[2], $mm, PREG_SET_ORDER)) {
            foreach ($mm as $row) { $apikey[$row[1]] = $row[2]; }
        }
    }
    return array($api, $apikey);
}
add_action('rest_api_init', function () {
    register_rest_route('pm-home/v1', '/test-order-nil-lma', array(
        'methods' => 'POST',
        'permission_callback' => function () { return current_user_can('manage_woocommerce'); },
        'callback' => function ($req) {
            list($api, $apikey) = pm_live_keys_from_theme();
            $unit = sanitize_text_field($req->get_param('unit') ?: 'nilopolis');
            $amount = intval($req->get_param('amount_cents') ?: 199);
            $product_id = intval($req->get_param('product_id'));
            $case_id = sanitize_text_field($req->get_param('case_id') ?: 'api');
            $name = sanitize_text_field($req->get_param('name') ?: 'Teste Sync ERP');
            $email = 'teste.nil.lma.' . $case_id . '.' . time() . '@example.com';
            $cpf = '52998224725';
            $pedidoaccess = (string) time() . substr($cpf, 0, 4);
            $c = array(
                'number' => '{number}',
                'holder' => '{holder}',
                'expiration' => '{exp}',
                'securityCode' => '{cvv}',
                'brand' => 'mastercard',
            );
            $infos = array(
                'orderId' => $pedidoaccess,
                'amount' => $amount,
                'type' => 'CREDIT_CARD',
                'installments' => 1,
                'capture' => true,
                'customer' => array(
                    'name' => $name,
                    'identity' => $cpf,
                    'email' => $email,
                    'identityType' => 'CPF',
                    'phone' => '21988887777',
                ),
                'card' => $c,
            );
            if (empty($api[$unit]) || empty($apikey[$unit])) {
                return new WP_Error('no_key', 'unit without api key: ' . $unit, array('status' => 400));
            }
            $curl = curl_init();
            curl_setopt_array($curl, array(
                CURLOPT_URL => 'https://www.accesstage.net.br/access-pay/transactions?gateway=REDE',
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_TIMEOUT => 30,
                CURLOPT_CUSTOMREQUEST => 'POST',
                CURLOPT_POSTFIELDS => wp_json_encode($infos),
                CURLOPT_HTTPHEADER => array(
                    'API: ' . $api[$unit],
                    'APIKey: ' . $apikey[$unit],
                    'Content-Type: application/json',
                    'Accept: application/json',
                ),
            ));
            $response = curl_exec($curl);
            $cerr = curl_error($curl);
            $success = json_decode(is_string($response) ? $response : '');
            if ($cerr || !is_object($success) || (($success->returnMessage ?? '') !== 'Success.' && ($success->returnCode ?? '') !== '00')) {
                return array(
                    'ok' => false,
                    'unit' => $unit,
                    'curl_err' => $cerr,
                    'response' => is_string($response) ? substr($response, 0, 400) : null,
                    'email' => $email,
                );
            }
            if (null == email_exists($email)) {
                $user_id = wp_insert_user(array(
                    'user_login' => $email,
                    'user_email' => $email,
                    'first_name' => $name,
                    'display_name' => $name,
                ));
            } else {
                $user = get_user_by('email', $email);
                $user_id = $user ? $user->ID : 0;
            }
            $order = wc_create_order();
            $prod = wc_get_product($product_id);
            if ($prod) $order->add_product($prod, 1);
            $address = array(
                'first_name' => $name,
                'email' => $email,
                'phone' => '21988887777',
                'address_1' => 'Rua Teste Sync',
                'address_2' => '10',
                'city' => 'Rio de Janeiro',
                'state' => 'RJ',
                'postcode' => '22041080',
                'country' => 'BR',
            );
            $order->set_address($address, 'billing');
            $order->set_address($address, 'shipping');
            $order->set_customer_id($user_id);
            $order->calculate_totals();
            $order->update_status('completed');
            update_post_meta($order->get_id(), 'Pedido Accesstage', $pedidoaccess);
            update_post_meta($order->get_id(), 'Unidade', $unit);
            update_post_meta($order->get_id(), 'CPF', $cpf);
            $order->save();
            return array(
                'ok' => true,
                'order_id' => $order->get_id(),
                'email' => $email,
                'unit' => $unit,
                'billing_state' => $order->get_billing_state(),
                'billing_first_name' => $order->get_billing_first_name(),
                'tid' => $success->tid ?? null,
            );
        },
    ));
});
"""


def main():
    c = card()
    code = (
        CODE.replace("{number}", c["number"])
        .replace("{holder}", c["holder"])
        .replace("{exp}", c["exp"])
        .replace("{cvv}", c["cvv"])
    )
    rows = call("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    sn = next((x for x in rows if x.get("name") == NAME), None)
    payload = {"name": NAME, "code": code, "scope": "global", "active": True}
    if sn:
        saved = call("PUT", f"/wp-json/code-snippets/v1/snippets/{sn['id']}", payload)
    else:
        saved = call("POST", "/wp-json/code-snippets/v1/snippets", payload)
    print("endpoint", saved.get("id"), saved.get("active"))

    results = []
    for unit, case_id in (("nilopolis", "nil"), ("largomachado", "lma")):
        print("====", unit)
        body = call(
            "POST",
            "/wp-json/pm-home/v1/test-order-nil-lma",
            {
                "unit": unit,
                "amount_cents": 199,
                "product_id": int(CHEAP["product_id"]),
                "case_id": case_id,
                "name": f"Teste ERP {case_id.upper()}",
            },
        )
        print(body)
        results.append(body)
        time.sleep(2)

    # deactivate ephemeral endpoint
    rows = call("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    sn = next((x for x in rows if x.get("name") == NAME), None)
    if sn:
        call(
            "PUT",
            f"/wp-json/code-snippets/v1/snippets/{sn['id']}",
            {"name": NAME, "code": code, "scope": "global", "active": False},
        )
        print("endpoint deactivated", sn["id"])

    summary = {
        "ok": all(r.get("ok") for r in results if isinstance(r, dict)),
        "results": results,
        "ts": int(time.time()),
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT, "ok", summary["ok"])


if __name__ == "__main__":
    main()
