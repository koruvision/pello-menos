/**
 * pm-wcar — carrinho abandonado (plugin "Cart Abandonment Recovery for WooCommerce", CartFlows).
 *
 * Snippet do Code Snippets (escopo global). Faz:
 *  1. Configura o plugin uma única vez (opções + 6 e-mails em português) — guardado por PM_WCAR_SETUP_VERSION.
 *  2. Traduz as strings que aparecem no e-mail do cliente (o plugin não tem pt_BR).
 *  3. Injeta window.pmWcar (ajaxurl + nonces + identidade conhecida) no checkout-shell e expõe
 *     GET /wp-json/pm-wcar/v1/config para o product.js (carrinho / ficha) — o nosso checkout é CF7 e
 *     o script de captura do plugin só roda no checkout nativo do Woo.
 *  4. Campos extras (CPF, unidade, lead id) gravados em other_fields da linha do carrinho.
 *  5. Sem duplicidade: a mesma pessoa (mesmo e-mail) em outra sessão/aparelho reaproveita a linha
 *     que já está recebendo a sequência em vez de abrir outra.
 *  6. Leads parciais (digitou nome/telefone/CPF mas não o e-mail) em tabela própria + tela
 *     WooCommerce → "Leads do checkout" com export CSV. Registros apagados após 30 dias.
 *  7. Janela de envio 8h–21h (horário do site): e-mails agendados fora disso vão para as 8h seguintes.
 *  8. Cabeçalho/logo iguais aos e-mails de pedido do Woo (mesma imagem, via opção do Woo).
 *  9. Pedido pago só "recupera" linha abandonada do mesmo e-mail dentro de 30 dias (padrão 90).
 *
 * Revisão do arquivo: 2026-10-30.2 (o setup — item 1 — só roda de novo quando PM_WCAR_SETUP_VERSION muda).
 * Publicado via REST do Code Snippets (ver projeto-migracao/historico/21-pos-reuniao-29-10-2026.md).
 */

if (!defined('ABSPATH')) {
    return;
}

if (!defined('PM_WCAR_SETUP_VERSION')) {
    define('PM_WCAR_SETUP_VERSION', '2026-10-30.1');
}
if (!defined('PM_WCAR_LEADS_TABLE')) {
    define('PM_WCAR_LEADS_TABLE', 'pm_checkout_leads');
}
if (!defined('PM_WCAR_RETENTION_DAYS')) {
    define('PM_WCAR_RETENTION_DAYS', 30);
}
if (!defined('PM_WCAR_SEND_HOUR_START')) {
    define('PM_WCAR_SEND_HOUR_START', 8);
}
if (!defined('PM_WCAR_SEND_HOUR_END')) {
    define('PM_WCAR_SEND_HOUR_END', 21);
}

// ---------------------------------------------------------------------------
// 2) Strings do e-mail em português.
// ---------------------------------------------------------------------------
add_filter('gettext', function ($translated, $text, $domain) {
    if ($domain !== 'woo-cart-abandonment-recovery') {
        return $translated;
    }
    static $map = array(
        'Item' => 'Item',
        'Name' => 'Produto',
        'Quantity' => 'Qtd.',
        'Price' => 'Preço',
        'Line Subtotal' => 'Subtotal',
        'Cart Total ( Cart Total + Shipping + Tax )' => 'Total do carrinho',
        "Don't remind me again." => 'Não quero mais receber estes lembretes.',
        'there' => 'tudo bem',
        '(incl. tax)' => '',
        '(excl. tax)' => '',
        'You have successfully unsubscribed from our email list.' => 'Pronto: você não vai mais receber lembretes deste carrinho.',
        'Unsubscribed' => 'Descadastrado',
    );
    return isset($map[$text]) ? $map[$text] : $translated;
}, 10, 3);

add_filter('woo_ca_default_first_name', function () {
    return 'tudo bem';
});

// Na tabela do e-mail o plugin usa get_formatted_name(), que acrescenta o SKU: "Body Splash - Livre (PM-BODY-SPLASH)".
// Troca pelo nome puro de cada produto do carrinho antes do envio.
add_filter('wcf_ca_email_body_before_send', function ($body, $email_data) {
    if (empty($email_data->cart_contents) || !function_exists('wc_get_product')) {
        return $body;
    }
    $items = maybe_unserialize($email_data->cart_contents);
    if (!is_array($items)) {
        return $body;
    }
    foreach ($items as $item) {
        $id = !empty($item['variation_id']) ? (int) $item['variation_id'] : (int) ($item['product_id'] ?? 0);
        $product = $id ? wc_get_product($id) : null;
        if ($product) {
            $body = str_replace($product->get_formatted_name(), $product->get_name(), $body);
        }
    }
    return $body;
}, 10, 2);

// ---------------------------------------------------------------------------
// Remetente SEMPRE igual ao dos e-mails de pedido do WooCommerce (nome e endereço vêm das opções do Woo;
// o WP Mail SMTP aplica por cima a mesma regra de "forçar remetente" que vale para os pedidos).
// ---------------------------------------------------------------------------
add_filter('cartflows_ca_email_headers', function ($headers) {
    $name = (string) get_option('woocommerce_email_from_name');
    $email = (string) get_option('woocommerce_email_from_address');
    if (!$name || !is_email($email)) {
        return $headers;
    }
    $lines = preg_split("/\r\n|\n|\r/", (string) $headers);
    $lines = array_filter($lines, function ($line) {
        return $line !== '' && !preg_match('/^(From|Reply-To):/i', $line);
    });
    array_unshift($lines, 'From: ' . $name . ' <' . $email . '>', 'Reply-To: ' . $name . ' <' . $email . '>');
    return implode("\r\n", $lines) . "\r\n";
});
add_action('init', function () {
    if (!function_exists('wcf_ca')) {
        return;
    }
    $name = (string) get_option('woocommerce_email_from_name');
    $email = (string) get_option('woocommerce_email_from_address');
    if ($name && get_option('wcf_ca_from_name') !== $name) {
        update_option('wcf_ca_from_name', $name);
    }
    if (is_email($email) && get_option('wcf_ca_from_email') !== $email) {
        update_option('wcf_ca_from_email', $email);
        update_option('wcf_ca_reply_email', $email);
    }
}, 100);

// ---------------------------------------------------------------------------
// Tabela de produtos: centralizada, largura total, bordas no padrão dos e-mails de pedido.
// ---------------------------------------------------------------------------
add_filter('woo_ca_email_template_table_style', function ($style) {
    $cell = 'padding: 10px 12px; border: 1px solid #F0E4EA; text-align: center; vertical-align: middle; color: #1A1A1A; font-size: 14px;';
    $style['table'] = array(
        'style' => $cell,
        'attribute' => 'align="center" width="100%" role="presentation"',
    );
    $style['product_image'] = array(
        'style' => 'height: 48px; width: 48px; border-radius: 8px;',
        'attribute' => 'width="48" height="48"',
    );
    return $style;
});
add_filter('wcf_ca_email_body_before_send', function ($body) {
    // O plugin fixa float/borda no <table>; alinha com o resto do e-mail e centraliza.
    return str_replace(
        'cellpadding="10" cellspacing="0" style="float: none; border: 1px solid #e5e5e5;">',
        'cellpadding="0" cellspacing="0" style="margin: 16px auto; border-collapse: collapse; border: 1px solid #F0E4EA;">',
        $body
    );
}, 20);

// ---------------------------------------------------------------------------
// 8) Logo: a mesma imagem dos e-mails de pedido (opção woocommerce_email_header_image).
// O plugin já usa o cabeçalho do Woo (use_woo_email_style). Opcionalmente embute a imagem
// como anexo CID (pm_wcar_logo_mode = 'cid') para clientes que bloqueiam imagens remotas;
// o padrão 'url' deixa o <img> exatamente como no e-mail "Pedido recebido".
// ---------------------------------------------------------------------------
if (!function_exists('pm_wcar_logo_path')) {
    function pm_wcar_logo_path() {
        $url = (string) get_option('woocommerce_email_header_image');
        if (!$url) {
            return '';
        }
        $dir = wp_upload_dir();
        if (strpos($url, $dir['baseurl']) !== 0) {
            return '';
        }
        $path = $dir['basedir'] . substr($url, strlen($dir['baseurl']));
        return is_readable($path) ? $path : '';
    }
}
$GLOBALS['pm_wcar_sending'] = false;
add_filter('wcf_ca_email_body_before_send', function ($body) {
    $GLOBALS['pm_wcar_sending'] = true;
    return $body;
}, 5);
add_filter('woocommerce_mail_content', function ($message) {
    if (empty($GLOBALS['pm_wcar_sending'])) {
        return $message;
    }
    $url = (string) get_option('woocommerce_email_header_image');
    if (get_option('pm_wcar_logo_mode', 'url') === 'cid' && $url && pm_wcar_logo_path()) {
        $width = (int) get_option('woocommerce_email_header_image_width', 140);
        $width = $width > 0 ? $width : 140;
        $message = preg_replace(
            '/<img([^>]*?)src="' . preg_quote($url, '/') . '"([^>]*)>/i',
            '<img$1src="cid:pm-wcar-logo" width="' . $width . '" height="' . $width . '"$2>',
            $message,
            1
        );
    }
    return $message;
}, 99);
add_action('phpmailer_init', function ($phpmailer) {
    if (empty($GLOBALS['pm_wcar_sending'])) {
        return;
    }
    $GLOBALS['pm_wcar_sending'] = false;
    $path = pm_wcar_logo_path();
    if ($path && strpos((string) $phpmailer->Body, 'cid:pm-wcar-logo') !== false) {
        $phpmailer->AddEmbeddedImage($path, 'pm-wcar-logo', 'pello-menos-logo.png', 'base64', 'image/png');
    }
}, 99);

// ---------------------------------------------------------------------------
// 3) Config para o front (checkout-shell inline + REST para product.js).
// ---------------------------------------------------------------------------
if (!function_exists('pm_wcar_known_identity')) {
    /** Identidade conhecida no servidor: conta logada (billing do Woo) e/ou linha restaurada pelo link do e-mail. */
    function pm_wcar_known_identity() {
        $out = array('user' => null, 'restored' => null);
        if (is_user_logged_in()) {
            $user = wp_get_current_user();
            $identity = array('email' => (string) $user->user_email);
            if (class_exists('WC_Customer')) {
                try {
                    $customer = new WC_Customer($user->ID);
                    $name = trim($customer->get_billing_first_name() . ' ' . $customer->get_billing_last_name());
                    if (!$name) {
                        $name = trim($customer->get_first_name() . ' ' . $customer->get_last_name());
                    }
                    if (!$name) {
                        $name = (string) $user->display_name;
                    }
                    $identity['name'] = $name;
                    $identity['phone'] = (string) $customer->get_billing_phone();
                    $identity['city'] = (string) $customer->get_billing_city();
                    $identity['state'] = (string) $customer->get_billing_state();
                    $identity['cep'] = (string) $customer->get_billing_postcode();
                    $cpf = (string) get_user_meta($user->ID, 'billing_cpf', true);
                    if ($cpf) {
                        $identity['cpf'] = preg_replace('/\D+/', '', $cpf);
                    }
                } catch (Exception $e) {
                    $identity['name'] = (string) $user->display_name;
                }
            }
            $out['user'] = array_filter($identity);
        }
        $token = isset($_GET['wcf_ac_token']) ? sanitize_text_field(wp_unslash($_GET['wcf_ac_token'])) : '';
        if ($token && class_exists('Cartflows_Ca_Tracking') && class_exists('Cartflows_Ca_Helper')) {
            $tracking = Cartflows_Ca_Tracking::get_instance();
            if (method_exists($tracking, 'is_valid_token') && $tracking->is_valid_token($token)) {
                $data = $tracking->wcf_decode_token($token);
                if (is_array($data) && !empty($data['wcf_session_id'])) {
                    $row = Cartflows_Ca_Helper::get_instance()->get_checkout_details($data['wcf_session_id']);
                    if ($row && !empty($row->email)) {
                        $other = maybe_unserialize($row->other_fields);
                        $other = is_array($other) ? $other : array();
                        $out['restored'] = array_filter(array(
                            'email' => (string) $row->email,
                            'name' => trim(($other['wcf_first_name'] ?? '') . ' ' . ($other['wcf_last_name'] ?? '')),
                            'phone' => (string) ($other['wcf_phone_number'] ?? ''),
                            'cpf' => (string) ($other['wcf_cpf'] ?? ''),
                            'unit' => (string) ($other['wcf_unidade'] ?? ''),
                            'city' => (string) ($other['wcf_city'] ?? ''),
                            'state' => (string) ($other['wcf_billing_state'] ?? ''),
                            'cep' => (string) ($other['wcf_billing_postcode'] ?? ''),
                        ));
                    }
                }
            }
        }
        return $out;
    }
}
if (!function_exists('pm_wcar_front_config')) {
    function pm_wcar_front_config() {
        $enabled = function_exists('wcf_ca') && get_option('wcf_ca_status', 'on') === 'on' && !isset($_COOKIE['wcf_ca_skip_track_data']);
        $known = pm_wcar_known_identity();
        return array(
            'enabled' => $enabled,
            'ajaxurl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('cartflows_save_cart_abandonment_data'),
            'leadNonce' => wp_create_nonce('pm_lead_save'),
            'postId' => (int) get_queried_object_id(),
            'user' => $known['user'],
            'restored' => $known['restored'],
        );
    }
}
add_action('wp_enqueue_scripts', function () {
    if (!wp_script_is('pm-checkout-shell', 'enqueued')) {
        return;
    }
    $cfg = pm_wcar_front_config();
    if (!$cfg['enabled']) {
        return;
    }
    wp_add_inline_script('pm-checkout-shell', 'window.pmWcar = ' . wp_json_encode($cfg) . ';', 'before');
}, 50);
add_action('rest_api_init', function () {
    register_rest_route('pm-wcar/v1', '/config', array(
        'methods' => 'GET',
        'permission_callback' => '__return_true',
        'callback' => function () {
            $cfg = pm_wcar_front_config();
            $response = new WP_REST_Response($cfg);
            $response->header('Cache-Control', 'private, no-store');
            return $response;
        },
    ));

    // Relatório read-only de carrinhos abandonados (auth Woo/admin).
    register_rest_route('pm-wcar/v1', '/abandonment-report', array(
        'methods' => 'GET',
        'permission_callback' => function () {
            return current_user_can('manage_woocommerce') || current_user_can('manage_options');
        },
        'args' => array(
            'after' => array(
                'required' => true,
                'type' => 'string',
            ),
            'before' => array(
                'required' => true,
                'type' => 'string',
            ),
        ),
        'callback' => function (WP_REST_Request $req) {
            global $wpdb;
            if (!function_exists('wcf_ca') && !defined('CARTFLOWS_CA_CART_ABANDONMENT_TABLE')) {
                return new WP_Error('pm_wcar_missing', 'Plugin de carrinho abandonado indisponível.', array('status' => 503));
            }
            $table = $wpdb->prefix . (defined('CARTFLOWS_CA_CART_ABANDONMENT_TABLE')
                ? CARTFLOWS_CA_CART_ABANDONMENT_TABLE
                : 'cartflows_ca_cart_abandonment');
            if ($wpdb->get_var($wpdb->prepare('SHOW TABLES LIKE %s', $table)) !== $table) {
                return new WP_Error('pm_wcar_no_table', 'Tabela de abandono não encontrada.', array('status' => 404));
            }

            $after = sanitize_text_field((string) $req->get_param('after'));
            $before = sanitize_text_field((string) $req->get_param('before'));
            // Aceita ISO datetime; normaliza para MySQL.
            $after_sql = str_replace('T', ' ', $after);
            $before_sql = str_replace('T', ' ', $before);
            if (strlen($after_sql) === 10) {
                $after_sql .= ' 00:00:00';
            }
            if (strlen($before_sql) === 10) {
                $before_sql .= ' 00:00:00';
            }

            $rows = $wpdb->get_results(
                $wpdb->prepare(
                    "SELECT order_status,
                            COUNT(*) AS carts,
                            COALESCE(SUM(CAST(cart_total AS DECIMAL(12,2))), 0) AS gross
                     FROM {$table}
                     WHERE `time` >= %s AND `time` < %s
                     GROUP BY order_status",
                    $after_sql,
                    $before_sql
                ),
                ARRAY_A
            );

            $by_status = array();
            foreach ((array) $rows as $row) {
                $status = (string) ($row['order_status'] ?? '');
                $by_status[$status] = array(
                    'carts' => (int) ($row['carts'] ?? 0),
                    'gross' => round((float) ($row['gross'] ?? 0), 2),
                );
            }

            $abandoned_key = defined('WCF_CART_ABANDONED_ORDER') ? WCF_CART_ABANDONED_ORDER : 'abandoned';
            $normal_key = defined('WCF_CART_NORMAL_ORDER') ? WCF_CART_NORMAL_ORDER : 'normal';
            $completed_key = defined('WCF_CART_COMPLETED_ORDER') ? WCF_CART_COMPLETED_ORDER : 'completed';

            $abandoned = $by_status[$abandoned_key] ?? array('carts' => 0, 'gross' => 0.0);
            $normal = $by_status[$normal_key] ?? array('carts' => 0, 'gross' => 0.0);
            $recovered = $by_status[$completed_key] ?? array('carts' => 0, 'gross' => 0.0);

            $response = new WP_REST_Response(array(
                'after' => $after_sql,
                'before' => $before_sql,
                'abandoned' => $abandoned,
                'normal' => $normal,
                'recovered' => $recovered,
                'by_status' => $by_status,
                'source' => $table,
            ));
            $response->header('Cache-Control', 'private, no-store');
            return $response;
        },
    ));
});

// ---------------------------------------------------------------------------
// 4) Campos extras na linha do carrinho abandonado (CPF, unidade, lead id, origem).
// sanitize_post_data() do plugin só lê chaves conhecidas; as nossas continuam em $_POST.
// ---------------------------------------------------------------------------
add_filter('wcar_cart_default_other_fields', function ($fields) {
    $cpf = isset($_POST['pm_cpf']) ? preg_replace('/\D+/', '', (string) wp_unslash($_POST['pm_cpf'])) : '';
    $unidade = isset($_POST['pm_unidade']) ? sanitize_text_field(wp_unslash($_POST['pm_unidade'])) : '';
    $lead = isset($_POST['pm_lead_id']) ? sanitize_key(wp_unslash($_POST['pm_lead_id'])) : '';
    $source = isset($_POST['pm_source']) ? sanitize_key(wp_unslash($_POST['pm_source'])) : '';
    if ($cpf) {
        $fields['wcf_cpf'] = substr($cpf, 0, 14);
    }
    if ($unidade) {
        $fields['wcf_unidade'] = substr($unidade, 0, 120);
    }
    if ($lead) {
        $fields['wcf_lead_id'] = substr($lead, 0, 40);
    }
    if ($source) {
        $fields['wcf_source'] = $source;
    }
    return $fields;
});

// ---------------------------------------------------------------------------
// 5) Sem duplicidade por e-mail. O plugin cria uma linha por sessão do Woo; a mesma pessoa em
// outro navegador/aparelho (ou depois do cookie expirar) abriria uma segunda sequência. Aqui,
// depois de cada gravação, se existir outra linha ativa com o mesmo e-mail nos últimos 30 dias:
//  - se essa linha ainda não terminou a sequência → ela vira a linha "oficial": recebe o carrinho
//    atual, a nova é apagada e a sessão passa a apontar para ela (um único fluxo de e-mails);
//  - se a sequência antiga já acabou → a nova linha segue normalmente (novo abandono).
// ---------------------------------------------------------------------------
add_action('wcf_ca_after_save_abandonment_data', function ($session_id, $checkout_details) {
    global $wpdb;
    if (empty($session_id) || !is_array($checkout_details) || empty($checkout_details['email'])) {
        return;
    }
    $email = sanitize_email($checkout_details['email']);
    if (!$email) {
        return;
    }
    $table = $wpdb->prefix . CARTFLOWS_CA_CART_ABANDONMENT_TABLE;
    $history = $wpdb->prefix . CARTFLOWS_CA_EMAIL_HISTORY_TABLE;
    $templates = $wpdb->prefix . CARTFLOWS_CA_EMAIL_TEMPLATE_TABLE;
    $current = $wpdb->get_row($wpdb->prepare("SELECT * FROM {$table} WHERE session_id = %s", $session_id));
    if (!$current) {
        return;
    }
    $others = $wpdb->get_results($wpdb->prepare(
        "SELECT * FROM {$table} WHERE email = %s AND session_id <> %s AND order_status IN (%s, %s) AND unsubscribed = 0 AND `time` >= DATE_SUB(%s, INTERVAL %d DAY) ORDER BY `time` ASC",
        $email,
        $session_id,
        WCF_CART_NORMAL_ORDER,
        WCF_CART_ABANDONED_ORDER,
        current_time(WCF_CA_DATETIME_FORMAT),
        PM_WCAR_RETENTION_DAYS
    ));
    if (!$others) {
        return;
    }
    $active_templates = (int) $wpdb->get_var("SELECT COUNT(*) FROM {$templates} WHERE is_activated = 1");
    $keeper = null;
    foreach ($others as $row) {
        $sent = (int) $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM {$history} WHERE ca_session_id = %s AND email_sent = 1", $row->session_id));
        $scheduled = (int) $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM {$history} WHERE ca_session_id = %s", $row->session_id));
        $finished = $row->order_status === WCF_CART_ABANDONED_ORDER && $scheduled > 0 && $sent >= min($scheduled, max(1, $active_templates));
        if ($finished) {
            // Sequência antiga encerrada: não reaproveita; segue com a linha nova.
            continue;
        }
        if (!$keeper) {
            $keeper = $row;
            continue;
        }
        // Mais de uma linha antiga ativa (não deveria): mantém a primeira, apaga as demais sem e-mail enviado.
        if ($sent === 0) {
            $wpdb->delete($history, array('ca_session_id' => $row->session_id));
            $wpdb->delete($table, array('session_id' => $row->session_id));
        }
    }
    if (!$keeper) {
        return;
    }
    // Mantém o dono da linha antiga (wcf_ca_owner_id) e acrescenta os campos novos.
    $old_fields = maybe_unserialize($keeper->other_fields);
    $new_fields = maybe_unserialize($checkout_details['other_fields'] ?? '');
    $old_fields = is_array($old_fields) ? $old_fields : array();
    $new_fields = is_array($new_fields) ? $new_fields : array();
    $owner = $old_fields['wcf_ca_owner_id'] ?? null;
    $merged = array_merge($old_fields, array_filter($new_fields, function ($v) {
        return $v !== '' && $v !== null;
    }));
    if ($owner) {
        $merged['wcf_ca_owner_id'] = $owner;
    }
    $update = array(
        'cart_contents' => $checkout_details['cart_contents'] ?? $keeper->cart_contents,
        'cart_total' => $checkout_details['cart_total'] ?? $keeper->cart_total,
        'other_fields' => maybe_serialize($merged),
        'checkout_id' => $checkout_details['checkout_id'] ?? $keeper->checkout_id,
    );
    if ($keeper->order_status === WCF_CART_NORMAL_ORDER) {
        // Ainda dentro do cut-off: atualiza a hora como o plugin faria para a mesma sessão.
        $update['time'] = $checkout_details['time'] ?? current_time(WCF_CA_DATETIME_FORMAT);
    }
    $wpdb->update($table, $update, array('session_id' => $keeper->session_id));
    // Apaga a linha recém-criada (ainda sem e-mails) e aponta a sessão para a antiga.
    $wpdb->delete($history, array('ca_session_id' => $session_id));
    $wpdb->delete($table, array('session_id' => $session_id));
    if (function_exists('WC') && WC()->session) {
        WC()->session->set('wcf_session_id', $keeper->session_id);
    }
}, 10, 2);

// ---------------------------------------------------------------------------
// 7) Janela de envio 8h–21h (horário do site). O plugin agenda "hora do carrinho + N";
// aqui empurramos para as 8h seguintes o que cair fora da janela.
// ---------------------------------------------------------------------------
add_action('wcf_ca_message_scheduled', function ($args) {
    global $wpdb;
    if (!is_array($args) || empty($args['scheduled_time']) || empty($args['ca_session_id']) || empty($args['template_id'])) {
        return;
    }
    $ts = strtotime($args['scheduled_time']);
    if (!$ts) {
        return;
    }
    $hour = (int) date('G', $ts);
    $new = null;
    if ($hour < PM_WCAR_SEND_HOUR_START) {
        $new = strtotime(date('Y-m-d', $ts) . ' ' . sprintf('%02d:00:00', PM_WCAR_SEND_HOUR_START));
    } elseif ($hour >= PM_WCAR_SEND_HOUR_END) {
        $new = strtotime(date('Y-m-d', $ts) . ' ' . sprintf('%02d:00:00', PM_WCAR_SEND_HOUR_START) . ' +1 day');
    }
    if (!$new) {
        return;
    }
    // Dois e-mails da mesma sequência não podem cair no mesmo horário (ex.: abandono às 23h →
    // 1h e 6h iriam ambos para 08:00). Empurra 4h enquanto colidir com outro já agendado (±2h).
    $history = $wpdb->prefix . CARTFLOWS_CA_EMAIL_HISTORY_TABLE;
    $others = $wpdb->get_col($wpdb->prepare(
        "SELECT scheduled_time FROM {$history} WHERE ca_session_id = %s AND template_id <> %d",
        (string) $args['ca_session_id'],
        (int) $args['template_id']
    ));
    $taken = array_filter(array_map('strtotime', (array) $others));
    for ($i = 0; $i < 12; $i++) {
        $clash = false;
        foreach ($taken as $t) {
            if (abs($t - $new) < 2 * HOUR_IN_SECONDS) {
                $clash = true;
                break;
            }
        }
        if (!$clash) {
            break;
        }
        $new += 4 * HOUR_IN_SECONDS;
        if ((int) date('G', $new) >= PM_WCAR_SEND_HOUR_END) {
            $new = strtotime(date('Y-m-d', $new) . ' ' . sprintf('%02d:00:00', PM_WCAR_SEND_HOUR_START) . ' +1 day');
        }
    }
    $wpdb->update(
        $history,
        array('scheduled_time' => date(WCF_CA_DATETIME_FORMAT, $new)),
        array('ca_session_id' => (string) $args['ca_session_id'], 'template_id' => (int) $args['template_id'])
    );
});

// ---------------------------------------------------------------------------
// 6) Leads parciais do checkout (sem e-mail o plugin não grava nada).
// ---------------------------------------------------------------------------
if (!function_exists('pm_wcar_leads_table')) {
    function pm_wcar_leads_table() {
        global $wpdb;
        return $wpdb->prefix . PM_WCAR_LEADS_TABLE;
    }
}
if (!function_exists('pm_wcar_ensure_leads_table')) {
    function pm_wcar_ensure_leads_table() {
        global $wpdb;
        $table = pm_wcar_leads_table();
        if (get_option('pm_wcar_leads_schema') === '1' && $wpdb->get_var("SHOW TABLES LIKE '{$table}'") === $table) {
            return;
        }
        require_once ABSPATH . 'wp-admin/includes/upgrade.php';
        $charset = $wpdb->get_charset_collate();
        dbDelta("CREATE TABLE {$table} (
            id BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
            lead_id VARCHAR(40) NOT NULL,
            email VARCHAR(190) NOT NULL DEFAULT '',
            name VARCHAR(190) NOT NULL DEFAULT '',
            phone VARCHAR(40) NOT NULL DEFAULT '',
            cpf VARCHAR(14) NOT NULL DEFAULT '',
            unit VARCHAR(120) NOT NULL DEFAULT '',
            city VARCHAR(120) NOT NULL DEFAULT '',
            state VARCHAR(40) NOT NULL DEFAULT '',
            page VARCHAR(190) NOT NULL DEFAULT '',
            cart TEXT NULL,
            wc_session VARCHAR(64) NOT NULL DEFAULT '',
            user_id BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY  (id),
            UNIQUE KEY lead_id (lead_id),
            KEY email (email),
            KEY updated_at (updated_at)
        ) {$charset};");
        update_option('pm_wcar_leads_schema', '1');
    }
}
add_action('init', 'pm_wcar_ensure_leads_table', 98);

if (!function_exists('pm_wcar_cart_summary')) {
    /** Resumo legível do carrinho atual do Woo ("Abdômen – Cera ×5; Axila – Cera ×1"). */
    function pm_wcar_cart_summary() {
        if (!function_exists('WC') || !WC()->cart) {
            return '';
        }
        $parts = array();
        foreach (WC()->cart->get_cart() as $item) {
            $product = isset($item['data']) && is_object($item['data']) ? $item['data'] : null;
            $name = $product ? $product->get_name() : '';
            if ($name) {
                $parts[] = $name . ' ×' . (int) ($item['quantity'] ?? 1);
            }
        }
        return implode('; ', $parts);
    }
}
if (!function_exists('pm_wcar_save_lead')) {
    function pm_wcar_save_lead() {
        check_ajax_referer('pm_lead_save', 'security');
        global $wpdb;
        pm_wcar_ensure_leads_table();
        $table = pm_wcar_leads_table();
        $get = function ($key, $max = 190) {
            return isset($_POST[$key]) ? substr(sanitize_text_field(wp_unslash($_POST[$key])), 0, $max) : '';
        };
        $lead_id = sanitize_key($get('lead_id', 40));
        $email = sanitize_email($get('email'));
        $name = $get('name');
        $phone = preg_replace('/[^\d+() -]/', '', $get('phone', 40));
        $cpf = substr(preg_replace('/\D+/', '', $get('cpf', 20)), 0, 14);
        if (!$lead_id) {
            $lead_id = substr(md5(uniqid((string) wp_rand(), true)), 0, 20);
        }
        if (!$name && !$phone && !$cpf && !$email) {
            wp_send_json_error(array('code' => 'empty'));
        }
        $now = current_time(WCF_CA_DATETIME_FORMAT);
        $cart = pm_wcar_cart_summary();
        if (!$cart) {
            $cart = $get('cart');
        }
        $row = array(
            'lead_id' => $lead_id,
            'email' => $email,
            'name' => $name,
            'phone' => $phone,
            'cpf' => $cpf,
            'unit' => $get('unit', 120),
            'city' => $get('city', 120),
            'state' => $get('state', 40),
            'page' => $get('page'),
            'cart' => $cart,
            'wc_session' => (function_exists('WC') && WC()->session) ? (string) WC()->session->get('wcf_session_id') : '',
            'user_id' => get_current_user_id(),
            'updated_at' => $now,
        );
        $existing = $wpdb->get_row($wpdb->prepare("SELECT id, email, name, phone, cpf, unit, city, state FROM {$table} WHERE lead_id = %s", $lead_id));
        if ($existing) {
            // Nunca apaga um dado já conhecido com um vazio.
            foreach (array('email', 'name', 'phone', 'cpf', 'unit', 'city', 'state') as $k) {
                if ($row[$k] === '' && !empty($existing->$k)) {
                    $row[$k] = $existing->$k;
                }
            }
            $wpdb->update($table, $row, array('id' => (int) $existing->id));
        } else {
            $row['created_at'] = $now;
            $wpdb->insert($table, $row);
        }
        // Limpeza: registros com mais de 30 dias.
        $wpdb->query($wpdb->prepare("DELETE FROM {$table} WHERE updated_at < DATE_SUB(%s, INTERVAL %d DAY)", $now, PM_WCAR_RETENTION_DAYS));
        wp_send_json_success(array('lead_id' => $lead_id));
    }
}
add_action('wp_ajax_pm_lead_save', 'pm_wcar_save_lead');
add_action('wp_ajax_nopriv_pm_lead_save', 'pm_wcar_save_lead');

// Lead convertido: pedido pago/em processamento com o mesmo e-mail ou telefone apaga o registro
// (mesmos status que encerram a sequência do plugin; o pedido aqui nasce fora do checkout nativo).
add_action('woocommerce_order_status_changed', function ($order_id, $old_status, $new_status) {
    global $wpdb;
    if (!in_array($new_status, array('processing', 'completed', 'on-hold'), true)) {
        return;
    }
    $order = wc_get_order($order_id);
    if (!$order) {
        return;
    }
    $table = pm_wcar_leads_table();
    $email = sanitize_email($order->get_billing_email());
    $phone = preg_replace('/\D+/', '', (string) $order->get_billing_phone());
    if ($email) {
        $wpdb->delete($table, array('email' => $email));
    }
    if (strlen($phone) >= 8) {
        $wpdb->query($wpdb->prepare("DELETE FROM {$table} WHERE REPLACE(REPLACE(REPLACE(REPLACE(phone,'(',''),')',''),'-',''),' ','') LIKE %s", '%' . $wpdb->esc_like(substr($phone, -8))));
    }
    // Carrinho ainda "normal" (não virou abandonado) com o mesmo e-mail: a compra aconteceu,
    // então a linha some antes de gerar sequência. O plugin só casa pedido × linha por sessão
    // (woocommerce_new_order) ou por e-mail em linhas já abandonadas/perdidas; como o pedido
    // aqui nasce fora do checkout nativo, a sessão pode não bater.
    if ($email) {
        $ca = $wpdb->prefix . CARTFLOWS_CA_CART_ABANDONMENT_TABLE;
        $wpdb->query($wpdb->prepare("DELETE FROM {$ca} WHERE email = %s AND order_status = %s", $email, 'normal'));
    }
}, 20, 3);

// Janela em que um pedido pago "recupera" uma linha abandonada do mesmo e-mail: 30 dias
// (padrão do plugin: 90). A sequência termina em 7 dias e a retenção dos leads é 30 dias,
// então casar pedidos mais antigos só poluiria a estatística de recuperação.
add_filter('cartflows_ca_recovery_match_window_days', function () {
    return 30;
});

// Tela WooCommerce → Leads do checkout (lista + CSV).
add_action('admin_menu', function () {
    add_submenu_page(
        'woocommerce',
        'Leads do checkout',
        'Leads do checkout',
        'manage_woocommerce',
        'pm-checkout-leads',
        'pm_wcar_leads_page'
    );
}, 60);
if (!function_exists('pm_wcar_leads_page')) {
    function pm_wcar_leads_page() {
        global $wpdb;
        if (!current_user_can('manage_woocommerce')) {
            return;
        }
        pm_wcar_ensure_leads_table();
        $table = pm_wcar_leads_table();
        $rows = $wpdb->get_results("SELECT * FROM {$table} ORDER BY updated_at DESC LIMIT 500");
        $csv = wp_nonce_url(admin_url('admin-post.php?action=pm_checkout_leads_csv'), 'pm_checkout_leads_csv');
        echo '<div class="wrap"><h1 class="wp-heading-inline">Leads do checkout</h1> ';
        echo '<a class="page-title-action" href="' . esc_url($csv) . '">Baixar CSV</a>';
        echo '<p>Quem começou a preencher o checkout (nome, telefone, CPF, unidade) nos últimos ' . (int) PM_WCAR_RETENTION_DAYS . ' dias e não fechou o pedido. Quem informou e-mail também recebe os lembretes automáticos; os demais são para contato pela equipe. Registros são apagados automaticamente após ' . (int) PM_WCAR_RETENTION_DAYS . ' dias ou quando o pedido é concluído.</p>';
        echo '<table class="widefat striped"><thead><tr><th>Atualizado</th><th>Nome</th><th>Telefone</th><th>CPF</th><th>E-mail</th><th>Unidade</th><th>Carrinho</th><th>Página</th></tr></thead><tbody>';
        if (!$rows) {
            echo '<tr><td colspan="8">Nenhum lead registrado ainda.</td></tr>';
        }
        foreach ($rows as $r) {
            $cpf = $r->cpf ? substr($r->cpf, 0, 3) . '.***.***-' . substr($r->cpf, -2) : '';
            echo '<tr>'
                . '<td>' . esc_html(mysql2date('d/m/Y H:i', $r->updated_at)) . '</td>'
                . '<td>' . esc_html($r->name) . '</td>'
                . '<td>' . esc_html($r->phone) . '</td>'
                . '<td>' . esc_html($cpf) . '</td>'
                . '<td>' . esc_html($r->email) . '</td>'
                . '<td>' . esc_html($r->unit) . '</td>'
                . '<td>' . esc_html($r->cart) . '</td>'
                . '<td>' . esc_html($r->page) . '</td>'
                . '</tr>';
        }
        echo '</tbody></table></div>';
    }
}
add_action('admin_post_pm_checkout_leads_csv', function () {
    global $wpdb;
    if (!current_user_can('manage_woocommerce')) {
        wp_die('Sem permissão.');
    }
    check_admin_referer('pm_checkout_leads_csv');
    pm_wcar_ensure_leads_table();
    $rows = $wpdb->get_results('SELECT * FROM ' . pm_wcar_leads_table() . ' ORDER BY updated_at DESC', ARRAY_A);
    nocache_headers();
    header('Content-Type: text/csv; charset=UTF-8');
    header('Content-Disposition: attachment; filename="leads-checkout-' . date('Y-m-d') . '.csv"');
    $out = fopen('php://output', 'w');
    fwrite($out, "\xEF\xBB\xBF");
    fputcsv($out, array('atualizado', 'criado', 'nome', 'telefone', 'cpf', 'email', 'unidade', 'cidade', 'uf', 'carrinho', 'pagina'), ';');
    foreach ($rows as $r) {
        fputcsv($out, array($r['updated_at'], $r['created_at'], $r['name'], $r['phone'], $r['cpf'], $r['email'], $r['unit'], $r['city'], $r['state'], $r['cart'], $r['page']), ';');
    }
    fclose($out);
    exit;
});

// ---------------------------------------------------------------------------
// 1) Configuração única (opções + 6 e-mails).
// ---------------------------------------------------------------------------
add_action('init', function () {
    if (!function_exists('wcf_ca') || get_option('pm_wcar_setup_version') === PM_WCAR_SETUP_VERSION) {
        return;
    }
    global $wpdb;
    $tpl_table = $wpdb->prefix . 'cartflows_ca_email_templates';
    $meta_table = $wpdb->prefix . 'cartflows_ca_email_templates_meta';
    if ($wpdb->get_var("SHOW TABLES LIKE '{$tpl_table}'") !== $tpl_table || $wpdb->get_var("SHOW TABLES LIKE '{$meta_table}'") !== $meta_table) {
        return;
    }

    $options = array(
        'wcf_ca_status' => 'on',
        'wcf_ca_cut_off_time' => 30,
        'wcf_ca_scheduler_engine' => 'wp_cron',
        'wcf_ca_from_name' => (string) get_option('woocommerce_email_from_name', 'Loja Pello Menos'),
        'wcf_ca_from_email' => (string) get_option('woocommerce_email_from_address', 'contato@pellomenos.com.br'),
        'wcf_ca_reply_email' => (string) get_option('woocommerce_email_from_address', 'contato@pellomenos.com.br'),
        'wcf_ca_excludes_orders' => array('processing', 'completed'),
        'wcf_ca_send_recovery_report_emails_to_admin' => 'off',
        'wcf_ca_send_oos_warning_emails_to_admin' => 'off',
        // Sem aviso/link "Não quero lembretes" no checkout (decisão 30/10); o descadastro fica no rodapé do e-mail.
        'wcf_ca_gdpr_status' => 'off',
        'wcf_ca_coupon_code_status' => 'off',
        'wcf_ca_auto_delete_coupons' => 'on',
        'wcf_ca_banner_status' => 'off',
        'wcf_ca_popup_status' => 'off',
        'cartflows_ca_use_new_ui' => true,
        'pm_wcar_logo_mode' => 'url',
    );
    foreach ($options as $key => $value) {
        update_option($key, $value);
    }

    $button = function ($label) {
        // color !important + span interno: o inliner de CSS dos e-mails do Woo força a cor dos links (roxo) e apagava o texto do botão.
        return '<p style="text-align:center;margin:28px 0;"><a href="{{cart.checkout_url}}" style="display:inline-block;background:#B3196F;color:#ffffff !important;text-decoration:none;font-weight:700;padding:14px 28px;border-radius:999px;"><span style="color:#ffffff;">' . $label . '</span></a></p>';
    };
    $signature = '<p>Qualquer dúvida é só responder este e-mail.<br>Equipe Pello Menos</p><p style="font-size:12px;color:#999999;">{{cart.unsubscribe}}</p>';
    $quote = function ($text, $name) {
        return '<p style="margin:0 0 10px;padding:12px 16px;border-left:3px solid #FFBB3A;background:#FFF8FB;color:#3A0A3C;font-style:italic;">“' . $text . '”<br><span style="font-style:normal;font-size:12px;color:#6A1043;">— ' . $name . '</span></p>';
    };
    $services_url = home_url('/servicos/');

    $templates = array(
        array(
            'template_name' => 'E1 — 1 hora: seu carrinho ficou guardado',
            'email_subject' => '{{customer.firstname}}, deixamos tudo guardado para você',
            'email_body' => '<p>Oi, {{customer.firstname}}!</p>'
                . '<p>Vimos que você começou uma compra na Pello Menos e parou no meio. Fique tranquila: seus itens continuam no carrinho, com o preço do site (já com 5% OFF em relação ao valor da unidade).</p>'
                . '{{cart.product.table}}'
                . $button('Voltar ao meu carrinho')
                . '<p>Depois de pagar, você recebe tudo por e-mail e agenda o horário direto na unidade Pello Menos que escolheu.</p>'
                . $signature,
            'frequency' => 1,
            'frequency_unit' => 'HOUR',
            'coupon' => false,
        ),
        array(
            'template_name' => 'E2 — 6 horas: ficou alguma dúvida?',
            'email_subject' => 'Ficou alguma dúvida, {{customer.firstname}}?',
            'email_body' => '<p>Oi, {{customer.firstname}}!</p>'
                . '<p>Antes de você decidir, respondemos as perguntas que mais recebemos:</p>'
                . '<p><strong>Como funciona depois da compra?</strong><br>Você recebe a confirmação por e-mail e agenda o atendimento na unidade escolhida, no dia e horário que preferir.</p>'
                . '<p><strong>Posso trocar a unidade ou o serviço?</strong><br>Pode. É só responder este e-mail que a equipe ajusta para você.</p>'
                . '<p><strong>Cera ou laser?</strong><br>A cera é avulsa e deixa a pele lisa no mesmo dia; o laser é em sessões e reduz os pelos de forma duradoura. As duas são feitas por profissionais treinadas da Pello Menos.</p>'
                . '{{cart.product.table}}'
                . $button('Continuar minha compra')
                . $signature,
            'frequency' => 6,
            'frequency_unit' => 'HOUR',
            'coupon' => false,
        ),
        array(
            'template_name' => 'E3 — 1 dia: o que as clientes dizem',
            'email_subject' => '{{customer.firstname}}, veja por que tanta gente escolhe a Pello Menos',
            'email_body' => '<p>Oi, {{customer.firstname}}!</p>'
                . '<p>Seu carrinho continua guardado. Enquanto você pensa, olha o que quem já passou pela Pello Menos conta:</p>'
                . $quote('Fiz axilas a laser e o resultado veio rápido. Atendimento impecável.', 'Camila R.')
                . $quote('Buço a cera perfeito. Já indiquei para as amigas.', 'Fernanda L.')
                . '<p>Profissionais treinadas, produtos próprios e unidades perto de você. É só escolher o horário.</p>'
                . '{{cart.product.table}}'
                . $button('Garantir meu horário')
                . $signature,
            'frequency' => 1,
            'frequency_unit' => 'DAY',
            'coupon' => false,
        ),
        array(
            'template_name' => 'E4 — 2 dias: guardado até amanhã',
            'email_subject' => 'Seu carrinho fica guardado até amanhã, {{customer.firstname}}',
            'email_body' => '<p>Oi, {{customer.firstname}}!</p>'
                . '<p>Guardamos seus itens, mas as agendas das unidades enchem rápido perto do fim de semana e os preços do site podem mudar nas campanhas. Vale fechar agora para garantir o valor de hoje.</p>'
                . '{{cart.product.table}}'
                . '<p style="text-align:center;color:#6A1043;">Pagamento no cartão, com parcelamento, em menos de 3 minutos.</p>'
                . $button('Finalizar agora')
                . $signature,
            'frequency' => 2,
            'frequency_unit' => 'DAY',
            'coupon' => false,
        ),
        array(
            'template_name' => 'E5 — 4 dias: ainda faz sentido?',
            'email_subject' => '{{customer.firstname}}, ainda faz sentido para você?',
            'email_body' => '<p>Oi, {{customer.firstname}}!</p>'
                . '<p>Faz alguns dias que seu carrinho está parado e a gente quer entender: mudou de ideia sobre o serviço, a unidade ou o momento?</p>'
                . '<p>Se for o serviço ou a unidade, é só escolher outro — o site tem cera, laser, linha e esfoliação para todas as áreas, e você escolhe a unidade na hora da compra: <a href="' . esc_url($services_url) . '" style="color:#B3196F;">ver todos os serviços</a>.</p>'
                . '<p>Se for o momento, sem problema: seus itens continuam aqui.</p>'
                . '{{cart.product.table}}'
                . $button('Ver meu carrinho')
                . $signature,
            'frequency' => 4,
            'frequency_unit' => 'DAY',
            'coupon' => false,
        ),
        array(
            'template_name' => 'E6 — 7 dias: presente para fechar (cupom 5%) — último',
            'email_subject' => 'Um presente para você, {{customer.firstname}}: 5% OFF para fechar',
            'email_body' => '<p>Oi, {{customer.firstname}}!</p>'
                . '<p>Este é o nosso último lembrete sobre este carrinho — e ele vem com um presente. Liberamos um cupom de <strong>5% de desconto</strong> só para você fechar esta compra:</p>'
                . '<p style="text-align:center;font-size:22px;letter-spacing:2px;font-weight:700;color:#B3196F;">{{cart.coupon_code}}</p>'
                . '<p style="text-align:center;font-size:13px;color:#666666;">Válido por 48 horas, uso único. Ao clicar no botão, o cupom já entra aplicado.</p>'
                . '{{cart.product.table}}'
                . $button('Finalizar com 5% OFF')
                . '<p>Depois deste e-mail não enviamos mais lembretes sobre este carrinho.</p>'
                . $signature,
            'frequency' => 7,
            'frequency_unit' => 'DAY',
            'coupon' => true,
        ),
    );

    $meta_defaults = array(
        'override_global_coupon' => false,
        'discount_type' => 'percent',
        'coupon_amount' => 5,
        'coupon_expiry_date' => '',
        'coupon_expiry_unit' => 'hours',
        'use_woo_email_style' => true,
        'auto_coupon' => false,
        'free_shipping_coupon' => false,
        'individual_use_only' => false,
        'modify_product_table' => true,
        'product_image_size' => 'medium',
        'show_prices_with_tax' => false,
        'visible_columns' => 'name,quantity,price', // sem imagem: os produtos do OficialTeste não têm thumbnail
        'admin_email_copy_status' => false,
        'admin_email_copy_type' => 'bcc',
        'admin_email_copy_address' => '',
    );

    // Começa do zero: remove os templates anteriores (exemplos do plugin ou versão 29/10).
    $wpdb->query("DELETE FROM {$meta_table}");
    $wpdb->query("DELETE FROM {$tpl_table}");

    foreach ($templates as $tpl) {
        $wpdb->insert(
            $tpl_table,
            array(
                'template_name' => $tpl['template_name'],
                'email_subject' => $tpl['email_subject'],
                'email_body' => $tpl['email_body'],
                'is_activated' => 1,
                'frequency' => (int) $tpl['frequency'],
                'frequency_unit' => $tpl['frequency_unit'],
            ),
            array('%s', '%s', '%s', '%d', '%d', '%s')
        );
        $tpl_id = (int) $wpdb->insert_id;
        if (!$tpl_id) {
            continue;
        }
        $meta = $meta_defaults;
        if ($tpl['coupon']) {
            $meta['override_global_coupon'] = true;
            $meta['auto_coupon'] = true;
            $meta['individual_use_only'] = true;
            $meta['coupon_expiry_date'] = 48;
            $meta['coupon_expiry_unit'] = 'hours';
        }
        foreach ($meta as $key => $value) {
            if (is_bool($value)) {
                $value = $value ? '1' : '';
            }
            $wpdb->insert(
                $meta_table,
                array(
                    'email_template_id' => $tpl_id,
                    'meta_key' => $key,
                    'meta_value' => (string) $value,
                ),
                array('%d', '%s', '%s')
            );
        }
    }

    update_option('pm_wcar_setup_version', PM_WCAR_SETUP_VERSION);
}, 99);
