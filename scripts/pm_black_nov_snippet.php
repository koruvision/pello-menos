<?php
/**
 * pm-black-nov-pricing — descontos Black Novembro no carrinho Woo (e-commerce).
 * Espelha wordpress-loja/pm-home/black-nov-campaign.json + src/lib/black-nov-campaign.ts
 *
 * Força fase (smoke): define('PM_BLACK_NOV_FORCE', 'esquenta'); // ou black_week | off
 * Meta de mapeamento: _pm_catalog_id no produto (id do catálogo). Fallback: slug / SKU.
 */

if (!defined('ABSPATH')) {
    return;
}

if (!defined('PM_BLACK_NOV_FORCE')) {
    define('PM_BLACK_NOV_FORCE', '');
}

// Alinha a UI (pmBlackNov) ao FORCE mesmo se o snippet pm-home carregar antes.
add_action('wp_enqueue_scripts', function () {
    $force = strtolower(trim((string) PM_BLACK_NOV_FORCE));
    if (!in_array($force, array('esquenta', 'black_week', 'off'), true)) {
        return;
    }
    wp_register_script('pm-black-nov-force', false, array(), null, true);
    wp_enqueue_script('pm-black-nov-force');
    wp_add_inline_script(
        'pm-black-nov-force',
        'window.__PM_BLACK_PHASE__=' . wp_json_encode($force) . ';',
        'before'
    );
}, 1);

if (!function_exists('pm_black_nov_cfg')) {
function pm_black_nov_cfg() {
    static $cfg = null;
    if ($cfg !== null) {
        return $cfg;
    }
    $upload = wp_upload_dir();
    $path = trailingslashit($upload['basedir']) . 'pm-home/black-nov-campaign.json';
    $raw = is_readable($path) ? file_get_contents($path) : false;
    $cfg = $raw ? json_decode($raw, true) : null;
    if (!is_array($cfg)) {
        $cfg = array();
    }
    return $cfg;
}
}

if (!function_exists('pm_black_nov_phase')) {
function pm_black_nov_phase() {
    $force = strtolower(trim((string) PM_BLACK_NOV_FORCE));
    if (in_array($force, array('esquenta', 'black_week', 'off'), true)) {
        return $force;
    }
    $cfg = pm_black_nov_cfg();
    if (!$cfg) {
        return 'off';
    }
    $now = time();
    $a = strtotime($cfg['esquentaStart'] ?? '');
    $b = strtotime($cfg['esquentaEnd'] ?? '');
    $c = strtotime($cfg['blackWeekStart'] ?? '');
    $d = strtotime($cfg['blackWeekEnd'] ?? '');
    if ($a && $b && $now >= $a && $now <= $b) {
        return 'esquenta';
    }
    if ($c && $d && $now >= $c && $now <= $d) {
        return 'black_week';
    }
    return 'off';
}
}

if (!function_exists('pm_black_nov_bridge_map')) {
function pm_black_nov_bridge_map() {
    static $map = null;
    if ($map !== null) {
        return $map;
    }
    $map = array();
    $upload = wp_upload_dir();
    $path = trailingslashit($upload['basedir']) . 'pm-home/woo-bridge.json';
    $raw = is_readable($path) ? file_get_contents($path) : false;
    $data = $raw ? json_decode($raw, true) : null;
    if (!is_array($data)) {
        return $map;
    }
    $prefer = function ($woo_id, $catalog_id) use (&$map) {
        $cid = (string) $catalog_id;
        $wid = (string) $woo_id;
        if ($wid === '' || $cid === '') {
            return;
        }
        $prev = isset($map[$wid]) ? (string) $map[$wid] : '';
        $is_esf = (strpos($cid, 'esfoliacao') === 0);
        $prev_esf = ($prev !== '' && strpos($prev, 'esfoliacao') === 0);
        // Cera/esfoliação compartilham o mesmo produto Woo no bridge: preferir id de cera.
        if ($prev === '' || ($prev_esf && !$is_esf)) {
            $map[$wid] = $cid;
        }
    };
    foreach ($data as $catalog_id => $entry) {
        if (!is_array($entry)) {
            continue;
        }
        $pid = isset($entry['productId']) ? (string) $entry['productId'] : '';
        if ($pid !== '') {
            $prefer($pid, $catalog_id);
        }
        $units = $entry['units'] ?? null;
        if (is_array($units)) {
            foreach ($units as $meta) {
                if (!is_array($meta)) {
                    continue;
                }
                $vid = isset($meta['variationId']) ? (string) $meta['variationId'] : '';
                if ($vid !== '') {
                    $prefer($vid, $catalog_id);
                }
            }
        }
    }
    return $map;
}
}

if (!function_exists('pm_black_nov_catalog_id_from_item')) {
function pm_black_nov_catalog_id_from_item($item, $product = null) {
    if (is_array($item)) {
        foreach (array('pm_catalog_id', '_pm_catalog_id') as $key) {
            if (!empty($item[$key]) && is_string($item[$key])) {
                return $item[$key];
            }
        }
    }
    return pm_black_nov_catalog_id($product ? $product : ($item['data'] ?? null));
}
}

if (!function_exists('pm_black_nov_catalog_id')) {
function pm_black_nov_catalog_id($product) {
    if (!$product || !is_a($product, 'WC_Product')) {
        return '';
    }
    $meta = $product->get_meta('_pm_catalog_id', true);
    if (is_string($meta) && $meta !== '') {
        return $meta;
    }
    $parent_id = $product->get_parent_id();
    $parent = $parent_id ? wc_get_product($parent_id) : null;
    if ($parent) {
        $meta = $parent->get_meta('_pm_catalog_id', true);
        if (is_string($meta) && $meta !== '') {
            return $meta;
        }
    }
    $bridge = pm_black_nov_bridge_map();
    $self_id = (string) $product->get_id();
    if (isset($bridge[$self_id])) {
        return $bridge[$self_id];
    }
    if ($parent_id) {
        $parent_key = (string) $parent_id;
        if (isset($bridge[$parent_key])) {
            return $bridge[$parent_key];
        }
    }
    $slug = $parent ? $parent->get_slug() : $product->get_slug();
    return is_string($slug) ? $slug : '';
}
}

if (!function_exists('pm_black_nov_family')) {
function pm_black_nov_family($catalog_id, $method_hint = '') {
    $cfg = pm_black_nov_cfg();
    $pid = (string) $catalog_id;
    foreach (($cfg['excludeIdPrefixes'] ?? array()) as $prefix) {
        if ($pid === $prefix || strpos($pid, $prefix) === 0) {
            return 'excluded';
        }
    }
    $m = strtolower((string) $method_hint);
    $ex = $cfg['excludeMethods'] ?? array();
    if ($m && in_array($m, $ex, true)) {
        return 'excluded';
    }
    if ($m === 'laser' || strpos($pid, '-laser') !== false || substr($pid, -5) === 'laser') {
        return 'laser';
    }
    if ($m === 'cera' || $m === 'esfoliacao') {
        return 'cera_esf';
    }
    if (
        strpos($pid, '-cera') !== false
        || strpos($pid, 'esfoliacao') !== false
        || $pid === 'realce'
        || $pid === 'henna'
        || strpos($pid, 'tintura-pelos') !== false
    ) {
        return 'cera_esf';
    }
    return 'excluded';
}
}

if (!function_exists('pm_black_nov_cera_tier')) {
function pm_black_nov_cera_tier($catalog_id) {
    $cfg = pm_black_nov_cfg();
    $pid = (string) $catalog_id;
    foreach (array('P' => 'ceraTierP', 'M' => 'ceraTierM', 'G' => 'ceraTierG') as $tier => $key) {
        $list = $cfg[$key] ?? array();
        if (in_array($pid, $list, true)) {
            return $tier;
        }
    }
    return 'G';
}
}

if (!function_exists('pm_black_nov_infer_method')) {
function pm_black_nov_infer_method($catalog_id) {
    $pid = (string) $catalog_id;
    if (strpos($pid, 'esfoliacao') !== false) {
        return 'esfoliacao';
    }
    if (strpos($pid, 'laser') !== false) {
        return 'laser';
    }
    if (strpos($pid, 'linha') !== false) {
        return 'linha';
    }
    if (strpos($pid, 'plano') !== false) {
        return 'plano';
    }
    if (strpos($pid, 'cartao-presente') !== false || strpos($pid, 'body-splash') !== false) {
        return 'presente';
    }
    return 'cera';
}
}

if (!function_exists('pm_black_nov_cart_families')) {
function pm_black_nov_cart_families($cart) {
    $laser = array();
    $cera = array();
    foreach ($cart->get_cart() as $item) {
        $product = $item['data'] ?? null;
        if (!$product) {
            continue;
        }
        $cid = pm_black_nov_catalog_id_from_item($item, $product);
        if ($cid === '') {
            continue;
        }
        $fam = pm_black_nov_family($cid, pm_black_nov_infer_method($cid));
        if ($fam === 'laser') {
            $laser[$cid] = true;
        } elseif ($fam === 'cera_esf') {
            $cera[$cid] = true;
        }
    }
    return array(
        'laser' => count($laser),
        'cera_esf' => count($cera),
    );
}
}

if (!function_exists('pm_black_nov_rate')) {
function pm_black_nov_rate($catalog_id, $counts) {
    $phase = pm_black_nov_phase();
    if ($phase === 'off') {
        return null;
    }
    $cfg = pm_black_nov_cfg();
    if (!$cfg) {
        return null;
    }
    $method = pm_black_nov_infer_method($catalog_id);
    $fam = pm_black_nov_family($catalog_id, $method);
    if ($fam === 'excluded') {
        return null;
    }
    $thr = intval($cfg['multiThreshold'] ?? 3);
    if ($fam === 'laser') {
        $table = $cfg['laser'][$phase] ?? null;
        if (!$table) {
            return null;
        }
        $n = intval($counts['laser'] ?? 0);
        return $n >= $thr ? floatval($table['multi']) : floatval($table['any']);
    }
    $is_esf = ($method === 'esfoliacao');
    if ($phase === 'esquenta') {
        $table = $cfg['ceraEsf']['esquenta'] ?? null;
        if (!$table) {
            return null;
        }
        $n = intval($counts['cera_esf'] ?? 0);
        return $n >= $thr ? floatval($table['multi']) : floatval($table['any']);
    }
    // black_week
    if ($is_esf) {
        return floatval($cfg['ceraEsf']['black_week_esfoliacao'] ?? 0.15);
    }
    $tier = pm_black_nov_cera_tier($catalog_id);
    $map = $cfg['ceraEsf']['black_week_cera'] ?? array();
    return floatval($map[$tier] ?? 0.25);
}
}

if (!function_exists('pm_black_nov_catalog_row')) {
function pm_black_nov_catalog_row($catalog_id) {
    static $by_id = null;
    if ($by_id === null) {
        $by_id = array();
        $upload = wp_upload_dir();
        $path = trailingslashit($upload['basedir']) . 'pm-home/cart-related.json';
        $raw = is_readable($path) ? file_get_contents($path) : false;
        $data = $raw ? json_decode($raw, true) : null;
        $products = is_array($data) ? ($data['products'] ?? $data) : null;
        if (is_array($products)) {
            foreach ($products as $id => $row) {
                if (is_array($row)) {
                    $by_id[(string) $id] = $row;
                }
            }
        }
    }
    $cid = (string) $catalog_id;
    return isset($by_id[$cid]) ? $by_id[$cid] : null;
}
}

if (!function_exists('pm_black_nov_table_reais')) {
/**
 * Base de tabela (reais) alinhada ao JS: se skipDiscount (masc cera/esf já −5%),
 * reconstrói tabela com ÷0.95 sobre o regular Woo / originalCents do catálogo.
 */
function pm_black_nov_table_reais($catalog_id, $woo_regular) {
    $regular = floatval($woo_regular);
    $row = pm_black_nov_catalog_row($catalog_id);
    $method = pm_black_nov_infer_method($catalog_id);
    if (is_array($row)) {
        if (!empty($row['skipDiscount']) && ($method === 'cera' || $method === 'esfoliacao')) {
            $base_cents = null;
            if (isset($row['originalCents'])) {
                $base_cents = intval($row['originalCents']);
            } elseif ($regular > 0) {
                $base_cents = (int) round($regular * 100);
            }
            if ($base_cents !== null && $base_cents > 0) {
                return round(($base_cents / 0.95) / 100, 2);
            }
        }
        if (isset($row['originalCents']) && intval($row['originalCents']) > 0) {
            $orig = intval($row['originalCents']) / 100.0;
            // Woo de ensaio (~R$1): catálogo manda.
            if ($regular <= 1.01) {
                return round($orig, 2);
            }
            // Mesma tabela (RJ) ou arredondamento: catálogo.
            if (abs($regular - $orig) < 0.02) {
                return round($orig, 2);
            }
            // Uplift regional SP/DF típico (até ~25% acima do catálogo RJ).
            if ($regular > $orig && $regular <= $orig * 1.25) {
                return round($regular, 2);
            }
            // SKU Woo compartilhado / preço menor desatualizado: catálogo (hero/carrinho).
            return round($orig, 2);
        }
    }
    return $regular > 0 ? $regular : 0.0;
}
}

if (!function_exists('pm_black_nov_apply_cart')) {
function pm_black_nov_apply_cart($cart) {
    if (is_admin() && !defined('DOING_AJAX')) {
        return;
    }
    if (!$cart || pm_black_nov_phase() === 'off') {
        return;
    }

    $counts = pm_black_nov_cart_families($cart);
    foreach ($cart->get_cart() as $key => $item) {
        $product = $item['data'] ?? null;
        if (!$product || !is_a($product, 'WC_Product')) {
            continue;
        }
        if ($product->get_meta('_pm_skip_black_nov', true) === '1' || $product->get_meta('_pm_test_cheap', true) === '1') {
            continue;
        }
        $cid = pm_black_nov_catalog_id_from_item($item, $product);
        if ($cid === '') {
            continue;
        }
        $rate = pm_black_nov_rate($cid, $counts);
        if ($rate === null || $rate <= 0) {
            continue;
        }
        $regular = floatval($product->get_regular_price());
        if ($regular <= 0) {
            $regular = floatval($product->get_price());
        }
        $table = pm_black_nov_table_reais($cid, $regular);
        if ($table <= 0) {
            continue;
        }
        // Campanha aplica % sobre a tabela (mesma base do pmBlackNov no front).
        $sale = round($table * (1 - $rate), 2);
        $product->set_price($sale);
    }
}
}

add_action('woocommerce_before_calculate_totals', 'pm_black_nov_apply_cart', 20);
add_action('woocommerce_cart_loaded_from_session', function () {
    if (function_exists('WC') && WC()->cart) {
        pm_black_nov_apply_cart(WC()->cart);
    }
}, 20);

// Store API: aceita pm_catalog_id no body do add-item para desambiguar cera vs esfoliação.
add_filter('woocommerce_store_api_add_to_cart_data', function ($add_to_cart_data, $request) {
    $cid = $request->get_param('pm_catalog_id');
    if (!$cid) {
        $cid = $request->get_param('_pm_catalog_id');
    }
    if (is_string($cid) && $cid !== '') {
        $add_to_cart_data['cart_item_data']['pm_catalog_id'] = sanitize_text_field($cid);
    }
    return $add_to_cart_data;
}, 10, 2);

add_filter('woocommerce_add_cart_item_data', function ($cart_item_data, $product_id, $variation_id) {
    if (empty($cart_item_data['pm_catalog_id']) && isset($_REQUEST['pm_catalog_id'])) {
        $cart_item_data['pm_catalog_id'] = sanitize_text_field(wp_unslash($_REQUEST['pm_catalog_id']));
    }
    return $cart_item_data;
}, 10, 3);

add_filter('woocommerce_get_cart_item_from_session', function ($cart_item, $values) {
    if (!empty($values['pm_catalog_id'])) {
        $cart_item['pm_catalog_id'] = $values['pm_catalog_id'];
    }
    return $cart_item;
}, 10, 2);

// Store API update-item: manter pm_catalog_id se enviado de novo (qty change).
add_filter('woocommerce_store_api_update_cart_item', function ($cart_item, $request) {
    if (!is_array($cart_item) || !is_object($request) || !method_exists($request, 'get_param')) {
        return $cart_item;
    }
    $cid = $request->get_param('pm_catalog_id');
    if (!$cid) {
        $cid = $request->get_param('_pm_catalog_id');
    }
    if (is_string($cid) && $cid !== '') {
        $cart_item['pm_catalog_id'] = sanitize_text_field($cid);
    }
    return $cart_item;
}, 10, 2);

// Expõe pm_catalog_id no item_data da Store API (front casa esfoliação vs cera).
add_filter('woocommerce_get_item_data', function ($item_data, $cart_item) {
    if (!is_array($item_data)) {
        $item_data = array();
    }
    if (!empty($cart_item['pm_catalog_id'])) {
        $cid = sanitize_text_field((string) $cart_item['pm_catalog_id']);
        $exists = false;
        foreach ($item_data as $row) {
            $key = strtolower((string) (isset($row['key']) ? $row['key'] : (isset($row['name']) ? $row['name'] : '')));
            if ($key === 'pm_catalog_id' || $key === '_pm_catalog_id') {
                $exists = true;
                break;
            }
        }
        if (!$exists) {
            $item_data[] = array(
                'key'     => 'pm_catalog_id',
                'value'   => $cid,
                'display' => $cid,
                'hidden'  => true,
            );
        }
    }
    return $item_data;
}, 10, 2);

// Nome de vitrine no carrinho Woo quando o item veio de um serviço do catálogo (esfoliação).
add_filter('woocommerce_cart_item_name', function ($name, $cart_item) {
    if (empty($cart_item['pm_catalog_id']) || !is_string($cart_item['pm_catalog_id'])) {
        return $name;
    }
    $cid = $cart_item['pm_catalog_id'];
    static $catalog_names = null;
    if ($catalog_names === null) {
        $catalog_names = array();
        $upload = wp_upload_dir();
        $path = trailingslashit($upload['basedir']) . 'pm-home/cart-related.json';
        if (is_readable($path)) {
            $decoded = json_decode((string) file_get_contents($path), true);
            if (is_array($decoded) && !empty($decoded['products']) && is_array($decoded['products'])) {
                foreach ($decoded['products'] as $id => $row) {
                    if (is_array($row) && !empty($row['name'])) {
                        $catalog_names[(string) $id] = (string) $row['name'];
                    }
                }
            }
        }
    }
    if (!empty($catalog_names[$cid])) {
        return $catalog_names[$cid];
    }
    return $name;
}, 20, 2);
