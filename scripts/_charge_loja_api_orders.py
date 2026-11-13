# -*- coding: utf-8 -*-
"""Cria pedidos R$1–R$2 cobrando Accesstage no servidor + order Woo (bypass CF7 UI)."""
from __future__ import annotations

import base64
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
CARD = ROOT / "projeto-migracao" / ".secrets" / "ot-test-card.env"
SKUS = json.loads((ROOT / "scripts" / "_loja_esquenta_test_skus.json").read_text(encoding="utf-8"))
CHEAP = json.loads((ROOT / "scripts" / "_loja_cheap_fixture.json").read_text(encoding="utf-8"))
OUT = ROOT / "scripts" / "_charge_loja_api_orders_result.json"
NAME = "pm-accesstage-normalize-test"

CASES = [
    {"id": "api_laser_2", "product_id": int(SKUS["pm-teste-esquenta-laser"]), "amount_cents": 200, "label": "2.00"},
    {"id": "api_laser_190", "product_id": int(SKUS["pm-teste-esquenta-laser"]), "amount_cents": 190, "label": "1.90"},
    {"id": "api_normal_199", "product_id": int(CHEAP["product_id"]), "amount_cents": 199, "label": "1.99"},
    {"id": "api_normal_100", "product_id": int(CHEAP["product_id"]), "amount_cents": 100, "label": "1.00"},
    {"id": "api_normal_189", "product_id": int(CHEAP["product_id"]), "amount_cents": 189, "label": "1.89"},
    {"id": "api_laser_200b", "product_id": int(SKUS["pm-teste-esquenta-laser"]), "amount_cents": 200, "label": "2.00"},
]


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def card():
    c = {}
    for line in CARD.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            c[k.strip()] = v.strip()
    return c


def call(method, path, payload=None):
    e = env()
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        e["PM_LOJA_URL"].rstrip("/") + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-api-orders",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read().decode()
        return json.loads(body) if body else {}


def publish_endpoint():
    c = card()
    number = c["PM_TEST_CARD_NUMBER"].replace(" ", "")
    holder = c["PM_TEST_CARD_HOLDER"].replace("\\", "\\\\").replace("'", "\\'")
    exp = c["PM_TEST_CARD_EXP"]
    cvv = c["PM_TEST_CARD_CVV"]
    code = f'''
function pm_live_keys_from_theme() {{
    static $cache = null;
    if ($cache !== null) return $cache;
    $path = get_stylesheet_directory() . '/functions.php';
    $src = is_readable($path) ? file_get_contents($path) : '';
    $api = array(); $apikey = array();
    if (preg_match('/\\$api\\s*=\\s*array\\((.*?)\\);/s', $src, $m)) {{
        preg_match_all("/'([a-z0-9_]+)'\\s*=>\\s*'([^']+)'/i", $m[1], $mm, PREG_SET_ORDER);
        foreach ($mm as $row) $api[$row[1]] = $row[2];
    }}
    if (preg_match('/\\$apikey\\s*=\\s*array\\((.*?)\\);/s', $src, $m)) {{
        preg_match_all("/'([a-z0-9_]+)'\\s*=>\\s*'([^']+)'/i", $m[1], $mm, PREG_SET_ORDER);
        foreach ($mm as $row) $apikey[$row[1]] = $row[2];
    }}
    $cache = array($api, $apikey);
    return $cache;
}}
add_action('rest_api_init', function () {{
    register_rest_route('pm-home/v1', '/test-order', array(
        'methods' => 'POST',
        'permission_callback' => function () {{ return current_user_can('manage_options'); }},
        'callback' => function ($req) {{
            list($api, $apikey) = pm_live_keys_from_theme();
            $unit = sanitize_text_field($req->get_param('unit') ?: 'botafogo');
            $amount = intval($req->get_param('amount_cents') ?: 199);
            $product_id = intval($req->get_param('product_id'));
            $case_id = sanitize_text_field($req->get_param('case_id') ?: 'api');
            $email = 'teste.loja.api.' . $case_id . '.' . time() . '@example.com';
            $cpf = '52998224725';
            $pedidoaccess = (string) time() . wp_generate_password(6, false, false);
            $infos = array(
                'orderId' => $pedidoaccess,
                'amount' => $amount,
                'type' => 'CREDIT_CARD',
                'installments' => 1,
                'capture' => true,
                'customer' => array(
                    'name' => 'Teste Loja API ' . $case_id,
                    'identity' => $cpf,
                    'email' => $email,
                    'identityType' => 'CPF',
                    'phone' => '21988887777',
                ),
                'card' => array(
                    'number' => '{number}',
                    'holder' => '{holder}',
                    'expiration' => '{exp}',
                    'securityCode' => '{cvv}',
                    'brand' => 'mastercard',
                ),
            );
            if (empty($api[$unit]) || empty($apikey[$unit])) {{
                return new WP_Error('no_key', 'unit without api key', array('status' => 400));
            }}
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
            if ($cerr || !is_object($success) || (($success->returnMessage ?? '') !== 'Success.' && ($success->returnCode ?? '') !== '00')) {{
                return array(
                    'ok' => false,
                    'curl_err' => $cerr,
                    'response' => is_string($response) ? substr($response, 0, 400) : null,
                    'email' => $email,
                );
            }}
            if (null == email_exists($email)) {{
                $user_id = wp_insert_user(array('user_login' => $email, 'user_email' => $email));
            }} else {{
                $user = get_user_by('email', $email);
                $user_id = $user ? $user->ID : 0;
            }}
            $order = wc_create_order();
            $prod = wc_get_product($product_id);
            if ($prod) $order->add_product($prod, 1);
            $address = array(
                'first_name' => 'Teste Loja API',
                'email' => $email,
                'phone' => '21988887777',
                'address_1' => 'Rua Teste',
                'address_2' => '10',
                'city' => 'Rio de Janeiro',
                'state' => 'RJ',
                'postcode' => '22041080',
            );
            $order->set_address($address, 'billing');
            $order->set_address($address, 'shipping');
            $order->calculate_totals();
            $order->set_total(number_format($amount / 100, 2, '.', ''));
            if ($user_id) $order->set_customer_id($user_id);
            $order->update_status('completed');
            update_post_meta($order->get_id(), 'Pedido Accesstage', $pedidoaccess);
            update_post_meta($order->get_id(), 'Unidade', $unit);
            update_post_meta($order->get_id(), 'CPF', $cpf);
            update_post_meta($order->get_id(), 'Modalidade', 'Cartão de crédito');
            update_post_meta($order->get_id(), 'Cartão', 'mastercard');
            update_post_meta($order->get_id(), '_pm_cf7_totalamount', number_format($amount / 100, 2, '.', ''));
            update_post_meta($order->get_id(), '_pm_accesstage_lines_synced', '1');
            update_post_meta($order->get_id(), '_pm_accesstage_amount_cents', (string) $amount);
            $order->save();
            return array(
                'ok' => true,
                'order_id' => $order->get_id(),
                'total' => $order->get_total(),
                'email' => $email,
                'tid' => $success->tid ?? null,
                'amount_cents' => $amount,
            );
        }},
    ));
}});
'''
    rows = call("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    sn = next((x for x in rows if x.get("name") == NAME), None)
    payload = {"name": NAME, "code": code, "scope": "global", "active": True}
    if sn:
        saved = call("PUT", f"/wp-json/code-snippets/v1/snippets/{sn['id']}", payload)
    else:
        saved = call("POST", "/wp-json/code-snippets/v1/snippets", payload)
    print("endpoint", saved.get("id"), saved.get("active"))


def main():
    publish_endpoint()
    # restore original payment_CF7 by not removing it in this snippet
    results = []
    for case in CASES:
        print("====", case["id"], case["label"])
        try:
            body = call(
                "POST",
                "/wp-json/pm-home/v1/test-order",
                {
                    "unit": "botafogo",
                    "amount_cents": case["amount_cents"],
                    "product_id": case["product_id"],
                    "case_id": case["id"],
                },
            )
        except Exception as err:
            body = {"ok": False, "error": str(err)}
        print(body)
        results.append({"case": case["id"], **(body if isinstance(body, dict) else {"raw": body})})
        time.sleep(2)
    summary = {
        "ok": all(r.get("ok") for r in results),
        "passed": sum(1 for r in results if r.get("ok")),
        "total": len(results),
        "order_ids": [r.get("order_id") for r in results if r.get("order_id")],
        "results": results,
        "ts": int(time.time()),
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT, "passed", summary["passed"], "/", summary["total"], "orders", summary["order_ids"])
    if not summary["ok"]:
        raise SystemExit("API_ORDERS_FAIL")
    print("API_ORDERS_OK")


if __name__ == "__main__":
    main()
