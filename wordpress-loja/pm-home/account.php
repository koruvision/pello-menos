<?php
if (!defined('ABSPATH')) {
    exit;
}

add_action('wp_ajax_pm_account', 'pm_account_ajax');
add_action('wp_ajax_nopriv_pm_account', 'pm_account_ajax');

function pm_account_ajax() {
    $op = isset($_POST['op']) ? sanitize_key(wp_unslash($_POST['op'])) : '';
    if ($op === 'me') {
        pm_account_me();
    } elseif ($op === 'login') {
        pm_account_login();
    } elseif ($op === 'register') {
        pm_account_register();
    } elseif ($op === 'logout') {
        wp_logout();
        wp_send_json(array('ok' => true, 'loggedIn' => false));
    } elseif ($op === 'orders') {
        pm_account_orders();
    } elseif ($op === 'order') {
        pm_account_order();
    } elseif ($op === 'address') {
        pm_account_address();
    } elseif ($op === 'save-address') {
        pm_account_save_address();
    } else {
        wp_send_json(array('ok' => false, 'message' => 'Ação desconhecida.'));
    }
}

function pm_account_me() {
    if (!is_user_logged_in()) {
        wp_send_json(array('ok' => true, 'loggedIn' => false));
    }
    $user = wp_get_current_user();
    wp_send_json(array(
        'ok' => true,
        'loggedIn' => true,
        'name' => $user->display_name,
        'email' => $user->user_email,
    ));
}

function pm_account_login() {
    $login = isset($_POST['username']) ? sanitize_text_field(wp_unslash($_POST['username'])) : '';
    $password = isset($_POST['password']) ? (string) wp_unslash($_POST['password']) : '';
    $remember = !empty($_POST['remember']);
    $user = wp_signon(array(
        'user_login' => $login,
        'user_password' => $password,
        'remember' => $remember,
    ), is_ssl());
    if (is_wp_error($user)) {
        wp_send_json(array('ok' => false, 'message' => 'Usuário ou senha incorretos.'));
    }
    wp_send_json(array(
        'ok' => true,
        'loggedIn' => true,
        'name' => $user->display_name,
        'email' => $user->user_email,
    ));
}

function pm_account_register() {
    $email = isset($_POST['email']) ? sanitize_email(wp_unslash($_POST['email'])) : '';
    $password = isset($_POST['password']) ? (string) wp_unslash($_POST['password']) : '';
    $name = isset($_POST['name']) ? sanitize_text_field(wp_unslash($_POST['name'])) : '';
    $phone = isset($_POST['phone']) ? sanitize_text_field(wp_unslash($_POST['phone'])) : '';
    $name = trim($name);
    $phone = trim($phone);
    if ($name === '' || $phone === '' || !is_email($email) || $password === '') {
        wp_send_json(array('ok' => false, 'message' => 'Informe nome, telefone, e-mail e senha.'));
    }
    if (!function_exists('wc_create_new_customer')) {
        wp_send_json(array('ok' => false, 'message' => 'O cadastro da loja não está disponível.'));
    }
    $user_id = wc_create_new_customer($email, '', $password);
    if (is_wp_error($user_id)) {
        wp_send_json(array('ok' => false, 'message' => wp_strip_all_tags($user_id->get_error_message())));
    }
    $user_id = (int) $user_id;
    wp_update_user(array(
        'ID' => $user_id,
        'first_name' => $name,
        'display_name' => $name,
    ));
    update_user_meta($user_id, 'billing_first_name', $name);
    update_user_meta($user_id, 'billing_phone', $phone);
    $billing_email = get_user_meta($user_id, 'billing_email', true);
    if (!$billing_email) {
        update_user_meta($user_id, 'billing_email', $email);
    }
    $user = wp_signon(array(
        'user_login' => $email,
        'user_password' => $password,
        'remember' => true,
    ), is_ssl());
    if (is_wp_error($user)) {
        wp_send_json(array('ok' => true, 'loggedIn' => false, 'message' => 'Conta criada. Entre com o e-mail e a senha.'));
    }
    wp_send_json(array(
        'ok' => true,
        'loggedIn' => true,
        'name' => $name,
        'email' => $user->user_email,
    ));
}

function pm_account_require_user() {
    if (!is_user_logged_in()) {
        wp_send_json(array('ok' => false, 'loggedIn' => false, 'message' => 'Entre na sua conta.'));
    }
    return wp_get_current_user();
}

function pm_account_orders() {
    $user = pm_account_require_user();
    $orders = array();
    if (function_exists('wc_get_orders')) {
        $uid = (int) $user->ID;
        $email = strtolower(trim((string) $user->user_email));
        $seen = array();
        $rows = array();

        foreach (array(
            array('customer_id' => $uid),
            // Pedidos feitos como visitante (ou com outro login) mas com o mesmo e-mail da conta.
            $email !== '' ? array('billing_email' => $email) : null,
        ) as $args) {
            if (!$args) {
                continue;
            }
            // Só concluído e reembolsado (mais recente em cima).
            $statuses = array('completed', 'refunded');
            $found = wc_get_orders(array_merge($args, array(
                'limit' => 20,
                'orderby' => 'date',
                'order' => 'DESC',
                'status' => $statuses,
            )));
            foreach ($found as $order) {
                $id = (int) $order->get_id();
                if (isset($seen[$id])) {
                    continue;
                }
                $seen[$id] = true;
                $rows[] = $order;
            }
        }

        usort($rows, function ($a, $b) {
            $da = $a->get_date_created() ? $a->get_date_created()->getTimestamp() : 0;
            $db = $b->get_date_created() ? $b->get_date_created()->getTimestamp() : 0;
            return $db <=> $da;
        });
        $rows = array_slice($rows, 0, 20);

        foreach ($rows as $order) {
            $summary = array();
            foreach ($order->get_items() as $item) {
                $summary[] = $item->get_name();
            }
            $orders[] = array(
                'id' => $order->get_id(),
                'number' => $order->get_order_number(),
                'date' => $order->get_date_created() ? $order->get_date_created()->date_i18n('d/m/Y') : '',
                'status' => function_exists('wc_get_order_status_name') ? wc_get_order_status_name($order->get_status()) : $order->get_status(),
                'total' => wp_strip_all_tags($order->get_formatted_order_total()),
                'itemsPreview' => array_slice($summary, 0, 3),
            );
        }
    }
    wp_send_json(array('ok' => true, 'loggedIn' => true, 'orders' => $orders));
}

function pm_account_order() {
    $user = pm_account_require_user();
    $order_id = isset($_POST['order_id']) ? absint($_POST['order_id']) : 0;
    $order = function_exists('wc_get_order') ? wc_get_order($order_id) : false;
    $email = strtolower(trim((string) $user->user_email));
    $order_email = $order ? strtolower(trim((string) $order->get_billing_email())) : '';
    $owns = $order && (
        (int) $order->get_user_id() === (int) $user->ID
        || ($email !== '' && $order_email === $email)
    );
    $visible = $order && in_array($order->get_status(), array('completed', 'refunded'), true);
    if (!$owns || !$visible) {
        wp_send_json(array('ok' => false, 'message' => 'Pedido não encontrado.'));
    }
    $items = array();
    foreach ($order->get_items() as $item) {
        $items[] = array(
            'name' => $item->get_name(),
            'qty' => $item->get_quantity(),
            'total' => wp_strip_all_tags($order->get_formatted_line_subtotal($item)),
        );
    }
    wp_send_json(array(
        'ok' => true,
        'loggedIn' => true,
        'order' => array(
            'id' => $order->get_id(),
            'number' => $order->get_order_number(),
            'date' => $order->get_date_created() ? $order->get_date_created()->date_i18n('d/m/Y H:i') : '',
            'status' => function_exists('wc_get_order_status_name') ? wc_get_order_status_name($order->get_status()) : $order->get_status(),
            'total' => wp_strip_all_tags($order->get_formatted_order_total()),
            'payment' => $order->get_payment_method_title(),
            'items' => $items,
            'billing' => array(
                'name' => trim($order->get_formatted_billing_full_name()),
                'address' => trim($order->get_billing_address_1() . ' ' . $order->get_billing_city() . '/' . $order->get_billing_state()),
                'email' => $order->get_billing_email(),
                'phone' => $order->get_billing_phone(),
            ),
        ),
    ));
}

function pm_account_address() {
    $user = pm_account_require_user();
    $address = array(
        'first_name' => '',
        'last_name' => '',
        'address_1' => '',
        'city' => '',
        'state' => '',
        'postcode' => '',
        'phone' => '',
        'email' => $user->user_email,
    );
    if (class_exists('WC_Customer')) {
        $customer = new WC_Customer($user->ID);
        $address = array(
            'first_name' => $customer->get_billing_first_name(),
            'last_name' => $customer->get_billing_last_name(),
            'address_1' => $customer->get_billing_address_1(),
            'city' => $customer->get_billing_city(),
            'state' => $customer->get_billing_state(),
            'postcode' => $customer->get_billing_postcode(),
            'phone' => $customer->get_billing_phone(),
            'email' => $customer->get_billing_email() ? $customer->get_billing_email() : $user->user_email,
        );
    }
    wp_send_json(array('ok' => true, 'loggedIn' => true, 'address' => $address));
}

function pm_account_save_address() {
    $user = pm_account_require_user();
    if (!class_exists('WC_Customer')) {
        wp_send_json(array('ok' => false, 'message' => 'Endereço indisponível.'));
    }
    $customer = new WC_Customer($user->ID);
    $fields = array('first_name', 'last_name', 'address_1', 'city', 'state', 'postcode', 'phone', 'email');
    foreach ($fields as $field) {
        $value = isset($_POST[$field]) ? sanitize_text_field(wp_unslash($_POST[$field])) : '';
        if ($field === 'email') {
            $value = sanitize_email($value);
        }
        $setter = 'set_billing_' . $field;
        $customer->$setter($value);
    }
    $customer->save();
    wp_send_json(array('ok' => true, 'loggedIn' => true));
}

if (!function_exists('pm_home_order_body')) {
function pm_home_order_body($order_id) {
    $order_id = (int) $order_id;
    $order = function_exists('wc_get_order') ? wc_get_order($order_id) : false;
    $key = isset($_GET['key']) ? sanitize_text_field(wp_unslash($_GET['key'])) : '';
    $open = $order && $key !== '' && hash_equals($order->get_order_key(), $key);
    $number = $order ? $order->get_order_number() : (string) $order_id;
    $html = '<main class="mx-auto w-full max-w-3xl px-container-margin py-12">'
        . '<p class="text-sm uppercase tracking-wide text-primary">Pedido recebido</p>'
        . '<h1 class="mt-2 font-[family-name:var(--font-display)] text-4xl text-primary">Obrigado. Seu pedido foi recebido.</h1>'
        . '<p class="mt-3 text-on-surface-variant">Pedido ' . esc_html($number) . '. A utilização do serviço começa 24 horas depois da confirmação do pagamento.</p>';
    if (!$open) {
        $html .= '<div class="mt-8 rounded-3xl border border-outline/40 bg-white p-6">'
            . '<p class="text-on-surface">Entre na sua conta para ver os itens deste pedido.</p>'
            . '<a class="btn-lux btn-lux-primary mt-6 inline-flex rounded-full px-6 py-3 text-sm font-semibold text-on-primary" href="/minha-conta/">Entrar</a>'
            . '</div></main>';
        return $html;
    }
    $rows = '';
    foreach ($order->get_items() as $item) {
        $rows .= '<div class="flex items-start justify-between gap-4 border-b border-outline/30 py-3 text-sm">'
            . '<div><p class="font-semibold text-on-surface">' . esc_html($item->get_name()) . '</p>'
            . '<p class="text-on-surface-variant">Quantidade ' . esc_html($item->get_quantity()) . '</p></div>'
            . '<p class="shrink-0 font-semibold text-primary">' . wp_kses_post($order->get_formatted_line_subtotal($item)) . '</p>'
            . '</div>';
    }
    $when = $order->get_date_created();
    $date = $when ? $when->date_i18n('d/m/Y H:i') : '';
    $status = function_exists('wc_get_order_status_name') ? wc_get_order_status_name($order->get_status()) : $order->get_status();
    $pay = $order->get_payment_method_title();
    $pay_html = $pay !== ''
        ? '<p><span class="block text-on-surface-variant">Pagamento</span><span class="font-semibold text-on-surface">' . esc_html($pay) . '</span></p>'
        : '';
    $html .= '<section class="mt-8 rounded-3xl border border-outline/40 bg-white p-6">'
        . '<div class="grid gap-4 text-sm ' . ($pay !== '' ? 'sm:grid-cols-3' : 'sm:grid-cols-2') . '">'
        . '<p><span class="block text-on-surface-variant">Data</span><span class="font-semibold text-on-surface">' . esc_html($date) . '</span></p>'
        . '<p><span class="block text-on-surface-variant">Situação</span><span class="font-semibold text-on-surface">' . esc_html($status) . '</span></p>'
        . $pay_html
        . '</div>'
        . '<div class="mt-6">' . $rows . '</div>'
        . '<div class="mt-4 flex justify-between text-base"><span class="font-semibold">Total</span><span class="font-[family-name:var(--font-display)] text-2xl text-primary">' . wp_kses_post($order->get_formatted_order_total()) . '</span></div>'
        . '</section>'
        . '<div class="mt-8 flex flex-wrap gap-3">'
        . '<a class="btn-lux btn-lux-primary inline-flex rounded-full px-6 py-3 text-sm font-semibold text-on-primary" href="/">Voltar à home</a>'
        . '<a class="inline-flex rounded-full border border-primary/30 px-6 py-3 text-sm font-semibold text-primary" href="/minha-conta/">Minha conta</a>'
        . '</div></main>';
    return $html;
}
}

add_action('template_redirect', function () {
    $method = isset($_SERVER['REQUEST_METHOD']) ? $_SERVER['REQUEST_METHOD'] : 'GET';
    if ($method !== 'GET' || is_admin() || wp_doing_ajax() || isset($_GET['wc-ajax'])) {
        return;
    }
    $path = isset($_SERVER['REQUEST_URI']) ? wp_parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH) : '/';
    $path = rawurldecode(is_string($path) ? $path : '/');
    $path = rtrim($path, '/');
    if (!preg_match('#^/(?:finaliza-compra|finalizar-pagamento|checkout)/order-received/([0-9]+)$#', $path, $match)) {
        return;
    }
    $upload = wp_upload_dir();
    $file = $upload['basedir'] . '/pm-home/pedido-recebido.html';
    if (!is_readable($file)) {
        return;
    }
    while (ob_get_level() > 0) {
        ob_end_clean();
    }
    status_header(200);
    header('Content-Type: text/html; charset=UTF-8');
    header('Cache-Control: private, no-store');
    $html = file_get_contents($file);
    echo str_replace('<!--PM_ORDER_BODY-->', pm_home_order_body((int) $match[1]), $html);
    exit;
}, -1);
