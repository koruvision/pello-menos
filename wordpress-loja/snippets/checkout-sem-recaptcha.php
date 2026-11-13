// Hard-disable CF7 reCAPTCHA / spam during test battery
add_filter('wpcf7_recaptcha_available', '__return_false', 999);
add_filter('wpcf7_recaptcha_verify_response', '__return_true', 999);
add_filter('wpcf7_spam', '__return_false', 999);
add_filter('wpcf7_skip_spam_check', '__return_true', 999);
remove_action('wpcf7_init', 'wpcf7_recaptcha_register_service', 10);
add_action('wpcf7_init', function () {
    if (function_exists('wpcf7_recaptcha_register_service')) {
        remove_action('wpcf7_init', 'wpcf7_recaptcha_register_service', 10);
    }
}, 1);
add_filter('wpcf7_form_hidden_fields', function ($fields) {
    unset($fields['_wpcf7_recaptcha_response']);
    return $fields;
}, 999);
add_filter('wpcf7_posted_data', function ($posted) {
    if (is_array($posted)) {
        $posted['g-recaptcha-response'] = 'pm-test-bypass';
        $posted['_wpcf7_recaptcha_response'] = 'pm-test-bypass';
    }
    return $posted;
}, 999);
