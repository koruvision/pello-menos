<?php
/**
 * pm-ecommerce-maintenance
 * Público: só página "E-commerce em Manutenção" + link /wp-admin.
 * Admin (manage_options): bypass para QA do front.
 * Não altera Accesstage/CF7.
 */
if (!defined('ABSPATH')) {
    exit;
}

add_action(
    'template_redirect',
    static function () {
        if (defined('WP_CLI') && WP_CLI) {
            return;
        }
        if (wp_doing_ajax() || wp_doing_cron()) {
            return;
        }
        if (defined('REST_REQUEST') && REST_REQUEST) {
            return;
        }
        if (is_admin()) {
            return;
        }
        if (function_exists('current_user_can') && current_user_can('manage_options')) {
            return;
        }

        $uri = isset($_SERVER['REQUEST_URI']) ? (string) $_SERVER['REQUEST_URI'] : '/';
        $path = wp_parse_url($uri, PHP_URL_PATH);
        $path = is_string($path) ? rawurldecode($path) : '/';
        if ($path === '') {
            $path = '/';
        }

        if ($path === '/wp-login.php' || strpos($path, '/wp-admin') === 0) {
            return;
        }
        if (strpos($path, '/wp-json') === 0 || strpos($path, '/?rest_route=') === 0) {
            return;
        }
        if (isset($_GET['wc-ajax']) || isset($_GET['rest_route'])) {
            return;
        }

        // Store/front APIs usadas por bots ou residual do tema — bloquear UX pública.
        status_header(503);
        if (!headers_sent()) {
            header('Retry-After: 3600');
            header('Content-Type: text/html; charset=UTF-8');
            header('X-Robots-Tag: noindex, nofollow');
            nocache_headers();
        }

        $admin = esc_url(admin_url());
        echo '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">'
            . '<meta name="viewport" content="width=device-width, initial-scale=1">'
            . '<meta name="robots" content="noindex,nofollow">'
            . '<title>E-commerce em Manutenção — Pello Menos</title>'
            . '<style>'
            . 'html,body{margin:0;min-height:100%;font-family:Georgia,"Times New Roman",serif;'
            . 'background:linear-gradient(160deg,#2a0a22 0%,#4a1540 45%,#1a0816 100%);'
            . 'color:#f7eef5}'
            . '.wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}'
            . '.box{max-width:28rem;text-align:center}'
            . 'h1{font-size:clamp(1.6rem,4vw,2.1rem);font-weight:600;letter-spacing:.02em;margin:0 0 .75rem}'
            . 'p{margin:0 0 1.5rem;line-height:1.5;opacity:.92;font-family:system-ui,-apple-system,sans-serif;font-size:1rem}'
            . 'a.leave{display:inline-block;color:#2a0a22;background:#e8c96a;text-decoration:none;'
            . 'padding:.85rem 1.25rem;border-radius:2px;font-family:system-ui,-apple-system,sans-serif;'
            . 'font-weight:600;font-size:.95rem}'
            . 'a.leave:hover{filter:brightness(1.05)}'
            . 'a.admin{display:block;margin-top:1.1rem;color:rgba(247,238,245,.55);background:transparent;'
            . 'padding:0;font-family:system-ui,-apple-system,sans-serif;font-weight:400;'
            . 'font-size:.7rem;letter-spacing:.04em;text-decoration:none}'
            . 'a.admin:hover{color:rgba(247,238,245,.85);text-decoration:underline}'
            . '</style></head><body><div class="wrap"><div class="box">'
            . '<h1>E-commerce em Manutenção</h1>'
            . '<p>Estamos atualizando a loja. Em breve você volta a comprar normalmente.</p>'
            . '<a class="leave" href="https://www.google.com/">Sair do site</a>'
            . '<a class="admin" href="' . $admin . '">administrativo</a>'
            . '</div></div></body></html>';
        exit;
    },
    0
);
