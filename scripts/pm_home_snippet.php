add_action('rest_api_init', function () {
    register_rest_route('pm-home/v1', '/bundle', array(
        'methods' => 'POST',
        'permission_callback' => function () {
            return current_user_can('edit_pages');
        },
        'callback' => 'pm_home_save_bundle',
    ));
    register_rest_route('pm-home/v1', '/purge-media', array(
        'methods' => 'POST',
        'permission_callback' => function () {
            return current_user_can('edit_pages');
        },
        'callback' => 'pm_home_purge_media',
    ));
});

if (!function_exists('pm_home_save_bundle')) {
function pm_home_save_bundle(WP_REST_Request $request) {
    $dir = wp_upload_dir();
    $base = $dir['basedir'] . '/pm-home';
    wp_mkdir_p($base);
    $zip_path = $base . '/bundle.zip';
    $raw = $request->get_body();
    if (strlen($raw) < 1000) {
        return new WP_Error('pm_empty', 'empty body', array('status' => 400));
    }
    file_put_contents($zip_path, $raw);
    if (!class_exists('ZipArchive')) {
        return new WP_Error('pm_zip', 'ZipArchive missing', array('status' => 500));
    }
    $zip = new ZipArchive();
    $open = $zip->open($zip_path);
    if ($open !== true) {
        return new WP_Error('pm_zip', 'open failed', array('status' => 500));
    }
    $zip->extractTo($base);
    $zip->close();
    @unlink($zip_path);
    return array(
        'ok' => true,
        'html' => is_readable($base . '/home.html'),
        'css' => is_readable($base . '/home.css'),
    );
}
}

if (!function_exists('pm_home_purge_media')) {
function pm_home_purge_media(WP_REST_Request $request) {
    $params = $request->get_json_params();
    if (!is_array($params)) {
        $params = array();
    }
    $paths = isset($params['paths']) && is_array($params['paths']) ? $params['paths'] : array();
    if (!$paths) {
        return new WP_Error('pm_purge_empty', 'paths required', array('status' => 400));
    }
    if (count($paths) > 500) {
        return new WP_Error('pm_purge_limit', 'max 500 paths', array('status' => 400));
    }
    $dir = wp_upload_dir();
    $base = wp_normalize_path($dir['basedir'] . '/pm-home');
    $media_root = $base . '/media';
    $deleted = array();
    $missing = array();
    $rejected = array();
    foreach ($paths as $raw_path) {
        $rel = str_replace('\\', '/', (string) $raw_path);
        $rel = ltrim($rel, '/');
        if ($rel === '' || strpos($rel, '..') !== false || preg_match('#^[a-zA-Z]:#', $rel)) {
            $rejected[] = $rel;
            continue;
        }
        // Only under pm-home/media/
        if (strpos($rel, 'media/') !== 0) {
            $rel = 'media/' . $rel;
        }
        $full = wp_normalize_path($base . '/' . $rel);
        if (strpos($full, $media_root) !== 0) {
            $rejected[] = $rel;
            continue;
        }
        if (!is_file($full)) {
            $missing[] = $rel;
            continue;
        }
        if (@unlink($full)) {
            $deleted[] = $rel;
        } else {
            $rejected[] = $rel;
        }
    }
    return array(
        'ok' => true,
        'deleted' => count($deleted),
        'missing' => count($missing),
        'rejected' => count($rejected),
        'deleted_paths' => $deleted,
        'missing_paths' => $missing,
        'rejected_paths' => $rejected,
    );
}
}

/**
 * CF7 #1831 na loja às vezes fica com additional_settings `demo_mode: on`
 * (REST grava off/vazio e a leitura volta para on). Em demo mode o formulário
 * “processa” sem concluir o fluxo real de pagamento — relato Beatriz.
 * Remove demo_mode em runtime só no form 1831.
 */
add_filter('wpcf7_contact_form_properties', function ($properties, $contact_form) {
    if (!is_array($properties) || !is_object($contact_form) || !method_exists($contact_form, 'id')) {
        return $properties;
    }
    if ((int) $contact_form->id() !== 1831) {
        return $properties;
    }
    $raw = isset($properties['additional_settings']) ? (string) $properties['additional_settings'] : '';
    if ($raw === '' || stripos($raw, 'demo_mode') === false) {
        return $properties;
    }
    $keep = array();
    foreach (preg_split("/\r\n|\n|\r/", $raw) as $line) {
        if (preg_match('/^\s*demo_mode\s*:/i', $line)) {
            continue;
        }
        $keep[] = $line;
    }
    $properties['additional_settings'] = implode("\n", $keep);
    return $properties;
}, 999, 2);

/**
 * ERP interno: coupon_lines[].code no maximo 20 caracteres.
 * So no save (nao no apply) — evita quebrar lookup de cupons legados.
 */
add_action('woocommerce_before_coupon_object_save', function ($coupon) {
    if (!is_object($coupon) || !method_exists($coupon, 'get_code') || !method_exists($coupon, 'set_code')) {
        return;
    }
    $code = (string) $coupon->get_code();
    if (strlen($code) > 20) {
        $coupon->set_code(substr($code, 0, 20));
    }
}, 5);

/**
 * Cupom de teste interno (_pm_linha_1real): ao aplicar, so buço feminino linha fica R$ 1,00.
 * Nao altera preco sem o cupom no carrinho.
 */
if (!function_exists('pm_linha_1real_cart_has_coupon')) {
function pm_linha_1real_cart_has_coupon($cart) {
    if (!$cart || !is_object($cart) || !method_exists($cart, 'get_applied_coupons')) {
        return false;
    }
    foreach ($cart->get_applied_coupons() as $code) {
        $coupon = new WC_Coupon($code);
        if ((string) $coupon->get_meta('_pm_linha_1real', true) === '1') {
            return true;
        }
    }
    return false;
}
}

add_action('woocommerce_before_calculate_totals', function ($cart) {
    if (is_admin() && !defined('DOING_AJAX')) {
        return;
    }
    if (!pm_linha_1real_cart_has_coupon($cart)) {
        return;
    }
    // productId Woo (bridge): so buco-linha (buço feminino linha)
    $linha_ids = array(16394);
    foreach ($cart->get_cart() as $item) {
        if (empty($item['data']) || !is_object($item['data'])) {
            continue;
        }
        $product = $item['data'];
        $id = method_exists($product, 'get_id') ? (int) $product->get_id() : 0;
        $parent = method_exists($product, 'get_parent_id') ? (int) $product->get_parent_id() : 0;
        $match = in_array($id, $linha_ids, true) || in_array($parent, $linha_ids, true);
        if (!$match) {
            continue;
        }
        // 1.01 - cupom fixed_product R$0,01 = liquido R$1,00
        $product->set_price(1.01);
    }
}, 20);

if (!function_exists('pm_home_route_on')) {
function pm_home_route_on($route) {
    // Sem a constante, tudo liga (comportamento do clone). Com ela, sÃ³ os ramos listados:
    // home, masculino, produto, carrinho, conta, shell, loja.
    if (!defined('PM_HOME_ROUTES')) {
        return true;
    }
    $list = array_map('trim', explode(',', (string) PM_HOME_ROUTES));
    return in_array($route, $list, true);
}
}

add_action('init', function () {
    if (!pm_home_route_on('conta')) {
        return;
    }
    $dir = wp_upload_dir();
    $file = $dir['basedir'] . '/pm-home/account.php';
    if (is_readable($file)) {
        include_once $file;
    }
}, 1);

if (!function_exists('pm_home_lost_password_body')) {
function pm_home_lost_password_body() {
    $sent = isset($_GET['reset-link-sent']);
    $show_reset = isset($_GET['show-reset-form']) || (isset($_GET['key']) && (isset($_GET['id']) || isset($_GET['login'])));
    $back = '<a class="mt-6 inline-block text-sm font-semibold underline" href="/minha-conta/">Voltar para entrar</a>';

    if ($sent) {
        return '<div class="pm-account-card p-6">'
            . '<p class="text-xs uppercase tracking-[0.18em] text-[#e8b86d]">Minha conta</p>'
            . '<h1 class="mt-2 font-[family-name:var(--font-display)] text-3xl text-white">E-mail enviado</h1>'
            . '<p class="mt-3 text-sm text-white/70">Enviamos o link de redefinição de senha para o e-mail da sua conta. Pode levar alguns minutos para chegar.</p>'
            . '<p class="mt-3 text-sm text-white/70">Aguarde pelo menos 10 minutos antes de tentar de novo, e confira a caixa de spam.</p>'
            . $back
            . '</div>';
    }

    if ($show_reset) {
        $rp_key = isset($_GET['key']) ? sanitize_text_field(wp_unslash($_GET['key'])) : '';
        $rp_login = '';
        if (isset($_GET['login'])) {
            $rp_login = sanitize_user(wp_unslash($_GET['login']));
        } elseif (isset($_GET['id'])) {
            $user = get_user_by('id', absint($_GET['id']));
            $rp_login = $user ? $user->user_login : '';
        }
        ob_start();
        wp_nonce_field('reset_password', 'woocommerce-reset-password-nonce');
        $nonce = ob_get_clean();
        return '<div class="pm-account-card p-6">'
            . '<p class="text-xs uppercase tracking-[0.18em] text-[#e8b86d]">Minha conta</p>'
            . '<h1 class="mt-2 font-[family-name:var(--font-display)] text-3xl text-white">Nova senha</h1>'
            . '<p class="mt-1 text-sm text-white/70">Defina uma nova senha para a sua conta.</p>'
            . '<form method="post" class="mt-6 space-y-4" action="' . esc_url(wc_lostpassword_url()) . '">'
            . '<label class="block text-sm">Nova senha'
            . '<input class="mt-1 w-full rounded-2xl border px-4 py-3" type="password" name="password_1" autocomplete="new-password" required />'
            . '</label>'
            . '<label class="block text-sm">Confirmar nova senha'
            . '<input class="mt-1 w-full rounded-2xl border px-4 py-3" type="password" name="password_2" autocomplete="new-password" required />'
            . '</label>'
            . '<input type="hidden" name="reset_key" value="' . esc_attr($rp_key) . '" />'
            . '<input type="hidden" name="reset_login" value="' . esc_attr($rp_login) . '" />'
            . '<input type="hidden" name="wc_reset_password" value="true" />'
            . $nonce
            . '<button type="submit" class="btn-lux btn-lux-primary mt-2 inline-flex w-full items-center justify-center rounded-full px-6 py-3 text-sm font-semibold text-on-primary">Salvar senha</button>'
            . '</form>'
            . $back
            . '</div>';
    }

    ob_start();
    wp_nonce_field('lost_password', 'woocommerce-lost-password-nonce');
    $nonce = ob_get_clean();
    return '<div class="pm-account-card p-6">'
        . '<p class="text-xs uppercase tracking-[0.18em] text-[#e8b86d]">Minha conta</p>'
        . '<h1 class="mt-2 font-[family-name:var(--font-display)] text-3xl text-white">Perdeu sua senha?</h1>'
        . '<p class="mt-1 text-sm text-white/70">Digite seu nome de usuário ou e-mail. Você recebe um link para criar uma nova senha.</p>'
        . '<form method="post" class="mt-6 space-y-4" action="' . esc_url(wc_lostpassword_url()) . '">'
        . '<label class="block text-sm">Nome de usuário ou e-mail'
        . '<input class="mt-1 w-full rounded-2xl border px-4 py-3" type="text" name="user_login" autocomplete="username" required />'
        . '</label>'
        . '<input type="hidden" name="wc_reset_password" value="true" />'
        . $nonce
        . '<button type="submit" class="btn-lux btn-lux-primary mt-2 inline-flex w-full items-center justify-center rounded-full px-6 py-3 text-sm font-semibold text-on-primary">Redefinir senha</button>'
        . '</form>'
        . $back
        . '</div>';
}
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

if (!function_exists('pm_home_gtm_id')) {
function pm_home_gtm_id() {
    return 'GTM-52G8XVQ8';
}
}

if (!function_exists('pm_home_print_gtm_head')) {
function pm_home_print_gtm_head() {
    $id = pm_home_gtm_id();
    echo "<!-- Google Tag Manager -->\n<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':\nnew Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],\nj=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=\n'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);\n})(window,document,'script','dataLayer','" . esc_js($id) . "');</script>\n<!-- End Google Tag Manager -->\n";
}
}

if (!function_exists('pm_home_print_gtm_body')) {
function pm_home_print_gtm_body() {
    $id = pm_home_gtm_id();
    echo '<!-- Google Tag Manager (noscript) -->' . "\n"
        . '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=' . esc_attr($id) . '"' . "\n"
        . 'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>' . "\n"
        . '<!-- End Google Tag Manager (noscript) -->' . "\n";
}
}

if (!function_exists('pm_home_inject_gtm_html')) {
function pm_home_inject_gtm_html($html) {
    $id = pm_home_gtm_id();
    if (strpos($html, $id) !== false) {
        return $html;
    }
    $head = "<!-- Google Tag Manager -->\n<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':\nnew Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],\nj=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=\n'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);\n})(window,document,'script','dataLayer','" . $id . "');</script>\n<!-- End Google Tag Manager -->\n";
    $body = '<!-- Google Tag Manager (noscript) -->' . "\n"
        . '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=' . $id . '"' . "\n"
        . 'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>' . "\n"
        . '<!-- End Google Tag Manager (noscript) -->' . "\n";
    if (stripos($html, '<head>') !== false) {
        $html = preg_replace('/<head>/i', '<head>' . "\n" . $head, $html, 1);
    }
    if (preg_match('/<body\b[^>]*>/i', $html, $m, PREG_OFFSET_CAPTURE)) {
        $tag = $m[0][0];
        $pos = $m[0][1] + strlen($tag);
        $html = substr($html, 0, $pos) . "\n" . $body . substr($html, $pos);
    }
    return $html;
}
}

if (!function_exists('pm_home_enqueue_shell')) {
function pm_home_enqueue_shell($upload) {
    $src = $upload['baseurl'] . '/pm-home/checkout-shell-c24.js?v=c46';
    $loading = $upload['baseurl'] . '/pm-home/checkout-loading.js?v=load6';
    $brand = $upload['baseurl'] . '/pm-home/checkout-brand.css?v=brand47';
    $black = $upload['baseurl'] . '/pm-home/black-nov-campaign.js?v=black2';
    add_action('wp_head', 'pm_home_print_gtm_head', 1);
    add_action('wp_body_open', 'pm_home_print_gtm_body', 1);
    // GSAP sob demanda no clique Finalizar (checkout-loading.js) — fora do first paint.
    add_action('wp_enqueue_scripts', function () use ($src, $loading, $brand, $black) {
        wp_enqueue_style('pm-checkout-brand', $brand, array(), null);
        wp_enqueue_script('pm-checkout-loading', $loading, array(), null, true);
        wp_enqueue_script('pm-black-nov', $black, array(), null, true);
        // OficialTeste / smoke: alinha UI ao PHP FORCE esquenta até a virada 03/11.
        // Na loja em GO, remover esta linha (calendário do JSON manda).
        if (defined('PM_BLACK_NOV_FORCE') && PM_BLACK_NOV_FORCE) {
            wp_add_inline_script(
                'pm-black-nov',
                'window.__PM_BLACK_PHASE__=' . wp_json_encode(strtolower((string) PM_BLACK_NOV_FORCE)) . ';',
                'before'
            );
        }
        wp_enqueue_script('pm-checkout-shell', $src, array('pm-checkout-loading', 'pm-black-nov'), null, true);
        wp_register_style('pm-checkout-hide', false);
        wp_enqueue_style('pm-checkout-hide');
        wp_add_inline_style(
            'pm-checkout-hide',
            'header.header_wrap,footer.footer_dark,.section.bg_default,.breadcrumb_section,.page-title-light,.page-title{display:none!important}' .
            'html,body,.main_content,.section,.container,#content,.content-area,.bg_default,.bg_light{background:#fff!important;background-image:none!important}' .
            '.main_content{margin-top:176px}' .
            '#pm-shell-header,#pm-shell-footer{position:relative;z-index:80}' .
            'a.scrollup{position:fixed;right:18px;bottom:22px;z-index:90;display:flex!important;align-items:center;justify-content:center;' .
            'width:48px;height:48px;border-radius:999px;overflow:hidden;text-decoration:none;' .
            'background:linear-gradient(145deg,#b3196f 0%,#91135a 55%,#700053 100%);' .
            'color:#fff;box-shadow:0 10px 24px rgba(179,25,111,.38)}' .
            'a.scrollup i{display:none!important}' .
            'a.scrollup::before{content:"";position:absolute;inset:0;background:linear-gradient(105deg,transparent 35%,rgba(255,255,255,.45) 50%,transparent 65%);' .
            'transform:translateX(-130%);animation:pm-scroll-shine 6.4s ease-in-out infinite;pointer-events:none}' .
            'a.scrollup::after{content:"";position:relative;z-index:1;width:14px;height:14px;' .
            'background:center/contain no-repeat url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'%23ffffff\' stroke-width=\'2.2\' stroke-linecap=\'round\' stroke-linejoin=\'round\'%3E%3Cpath d=\'m18 15-6-6-6 6\'/%3E%3C/svg%3E")}' .
            '@keyframes pm-scroll-shine{0%,8%{transform:translateX(-130%)}22%,100%{transform:translateX(130%)}}'
        );
    });
}
}

add_action('template_redirect', function () {
    if (is_admin() || wp_doing_ajax() || isset($_GET['wc-ajax'])) {
        return;
    }
    $method = isset($_SERVER['REQUEST_METHOD']) ? $_SERVER['REQUEST_METHOD'] : 'GET';
    if ($method !== 'GET') {
        return;
    }
    $upload = wp_upload_dir();
    $base = $upload['basedir'] . '/pm-home';
    $path = isset($_SERVER['REQUEST_URI']) ? wp_parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH) : '/';
    $path = rawurldecode(is_string($path) ? $path : '/');
    $path = rtrim($path, '/');
    if ($path === '') {
        $path = '/';
    }
    if ($path === '/wp-login.php' || strpos($path, '/wp-admin') === 0) {
        return;
    }
    $file = '';
    $pm_order_id = 0;
    $pm_lost_password = false;
    if (preg_match('#^/(?:finaliza-compra|finalizar-pagamento|checkout)/order-received/([0-9]+)$#', $path, $pm_order_match)) {
        if (!pm_home_route_on('shell')) {
            return;
        }
        $pm_order_id = (int) $pm_order_match[1];
        $file = $base . '/pedido-recebido.html';
    } elseif (
        $path === '/compra-nao-realizada'
        || $path === '/finalizar-pagamento/undefined'
        || $path === '/finaliza-compra/undefined'
        || $path === '/checkout/undefined'
    ) {
        if (!pm_home_route_on('shell')) {
            return;
        }
        $file = $base . '/compra-nao-realizada.html';
    } elseif ($path === '/minha-conta/lost-password') {
        if (!pm_home_route_on('conta')) {
            return;
        }
        $file = $base . '/lost-password.html';
        $pm_lost_password = true;
    } elseif ($path === '/minha-conta' || strpos($path, '/minha-conta/') === 0) {
        if (!pm_home_route_on('conta')) {
            return;
        }
        $file = $base . '/conta.html';
    } elseif (is_front_page() || $path === '/') {
        if (!pm_home_route_on('home')) {
            return;
        }
        $file = $base . '/home.html';
    } elseif (is_page('masculino') || $path === '/masculino') {
        if (!pm_home_route_on('masculino')) {
            return;
        }
        $file = $base . '/masculino.html';
    } elseif ($path === '/carrinho') {
        if (!pm_home_route_on('carrinho')) {
            return;
        }
        $file = $base . '/carrinho.html';
    } elseif ($path === '/busca') {
        if (!pm_home_route_on('loja')) {
            return;
        }
        $file = $base . '/busca.html';
    } elseif (preg_match('#^/produto/([^/]+)$#', $path, $matches)) {
        if (!pm_home_route_on('produto')) {
            return;
        }
        $key = $matches[1];
        $routes = array();
        $map = $base . '/routes.json';
        if (is_readable($map)) {
            $decoded = json_decode(file_get_contents($map), true);
            if (is_array($decoded)) {
                $routes = $decoded;
            }
        }
        if (isset($routes[$key])) {
            $file = $base . '/' . ltrim(str_replace('\\', '/', $routes[$key]), '/');
        } else {
            $file = $base . '/products/' . $key . '.html';
        }
    } else {
        $pages = array();
        $pages_file = $base . '/pages.json';
        if (pm_home_route_on('loja') && is_readable($pages_file)) {
            $decoded = json_decode(file_get_contents($pages_file), true);
            if (is_array($decoded) && isset($decoded[$path]) && is_string($decoded[$path])) {
                $file = $base . '/' . ltrim(str_replace('\\', '/', $decoded[$path]), '/');
            }
        }
        if ($file === '') {
            if (pm_home_route_on('shell')) {
                pm_home_enqueue_shell($upload);
            }
            return;
        }
    }
    if (!is_readable($file)) {
        return;
    }
    while (ob_get_level() > 0) {
        ob_end_clean();
    }
    status_header(200);
    header('Content-Type: text/html; charset=UTF-8');
    $private = is_user_logged_in();
    foreach ($_COOKIE as $name => $value) {
        if (strpos($name, 'wordpress_logged_in') === 0 || strpos($name, 'woocommerce_items_in_cart') === 0 || strpos($name, 'wp_woocommerce_session') === 0) {
            $private = true;
        }
    }
    // Carrinho/conta: nunca cache público (mesmo anônimo).
    $always_private = $pm_lost_password
        || $pm_order_id
        || $path === '/carrinho'
        || $path === '/minha-conta'
        || strpos($path, '/minha-conta/') === 0;
    if ($private || $always_private) {
        header('Cache-Control: private, no-store');
    } else {
        // Vitrine (home/PDP/masc/busca): TTL maior — menos PHP sob browsing.
        header('Cache-Control: public, max-age=300, s-maxage=600');
        header('Vary: Cookie');
    }
    if ($pm_order_id) {
        $html = file_get_contents($file);
        $html = str_replace('<!--PM_ORDER_BODY-->', pm_home_order_body($pm_order_id), $html);
        echo pm_home_inject_gtm_html($html);
        exit;
    }
    if ($pm_lost_password) {
        $html = file_get_contents($file);
        $html = str_replace('<!--PM_LOST_BODY-->', pm_home_lost_password_body(), $html);
        echo pm_home_inject_gtm_html($html);
        exit;
    }
    $html = file_get_contents($file);
    echo pm_home_inject_gtm_html($html);
    exit;
}, 0);
