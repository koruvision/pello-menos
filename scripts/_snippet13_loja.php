/**
 * Corrige CF7 #1831 → Accesstage / ERP:
 * - selects unit/easyunit: label→slug
 * - installments: "1x" → int
 * - estado: nome completo → UF 2 letras
 * - your-name: rejeitar e-mail (autofill)
 */
add_filter('wpcf7_posted_data', function ($posted) {
    if (!is_array($posted)) {
        return $posted;
    }
    $map = array(
        'RJ - Largo do Bicão' => 'largobicao',
        'RJ - Bangu' => 'bangu',
        'RJ - Botafogo' => 'botafogo',
        'RJ - Humaitá' => 'humaita',
        'RJ - Ipanema' => 'ipanema',
        'RJ - Flamengo' => 'flamengo',
        'RJ - Barra da Tijuca - Av. Olegário Maciel' => 'olegario',
        'RJ - Ilha do Governador II - Estrada do Galeão' => 'ilhagovernador2',
        'RJ - Tijuca - Rua Uruguai' => 'uruguai',
        'RJ - Madureira' => 'madureira',
        'RJ - Nilópolis' => 'nilopolis',
        'RJ - Nilopolis' => 'nilopolis',
        'RJ - Jacarepaguá - Largo da Freguesia' => 'freguesia',
        'RJ - Largo do Machado' => 'largomachado',
        'RJ - Copacabana I - Av. Barata Ribeiro' => 'copacabana1',
        'RJ - Copacabana II - Av. N. S. Copacabana' => 'copacabana2',
        'SP - Capital - Av. Paulista' => 'paulista',
        'RJ - Centro - Rua São José' => 'saojose',
        'RJ - Niterói - Icaraí' => 'icarai',
        'RJ - Campo Grande' => 'campogrande',
        'RJ - Região Serra - Petrópolis' => 'petropolis',
        'RJ - Centro - Rua Gonçalves Dias' => 'goncalvesdias',
        'RJ - Méier' => 'meier',
        'RJ - Bonsucesso' => 'bonsucesso',
        'DF - Asa Sul' => 'asasul',
        'DF - Asa Norte' => 'asanorte',
        'RJ - Recreio' => 'recreio',
        'RJ - Nova Iguaçu' => 'novaiguacu',
        'RJ - Cabo Frio' => 'cabofrio',
        'RJ - Duque de Caxias' => 'caxias',
        'SP - Interior - Jundiaí' => 'jundiai',
        'RJ - São João de Meriti' => 'saojoaomeriti',
        'RJ - Leblon' => 'leblon2',
        'DF - ParkShopping' => 'parkshopping',
        'RJ - Estrada Bandeirantes - Map Band' => 'estradabandeirantes',
        'RJ - Niterói - Afonso Pena' => 'afonsopena',
        'RJ - Tijuca - Rua Conde de Bonfim' => 'trezemaio',
        'botafogo' => 'botafogo',
        'ipanema' => 'ipanema',
        'largomachado' => 'largomachado',
        'largobicao' => 'largobicao',
        'nilopolis' => 'nilopolis',
    );
    foreach (array('unit', 'easyunit') as $field) {
        if (!isset($posted[$field])) {
            continue;
        }
        $vals = is_array($posted[$field]) ? $posted[$field] : array($posted[$field]);
        foreach ($vals as $i => $raw) {
            if (!is_string($raw)) {
                continue;
            }
            $key = trim($raw);
            if ($key !== '' && isset($map[$key])) {
                $vals[$i] = $map[$key];
            }
        }
        $posted[$field] = $vals;
    }
    foreach (array('installments', 'cerainstallments', 'allinstallments') as $field) {
        if (!isset($posted[$field])) {
            continue;
        }
        $vals = is_array($posted[$field]) ? $posted[$field] : array($posted[$field]);
        foreach ($vals as $i => $raw) {
            if (is_string($raw) && preg_match('/(\d+)/', $raw, $m)) {
                $vals[$i] = intval($m[1]);
            } elseif (is_numeric($raw)) {
                $vals[$i] = intval($raw);
            }
        }
        $posted[$field] = $vals;
    }

    $uf_map = array(
        'acre' => 'AC', 'alagoas' => 'AL', 'amapa' => 'AP', 'amapá' => 'AP', 'amazonas' => 'AM',
        'bahia' => 'BA', 'ceara' => 'CE', 'ceará' => 'CE', 'distrito federal' => 'DF',
        'espirito santo' => 'ES', 'espírito santo' => 'ES', 'goias' => 'GO', 'goiás' => 'GO',
        'maranhao' => 'MA', 'maranhão' => 'MA', 'mato grosso' => 'MT', 'mato grosso do sul' => 'MS',
        'minas gerais' => 'MG', 'para' => 'PA', 'pará' => 'PA', 'paraiba' => 'PB', 'paraíba' => 'PB',
        'parana' => 'PR', 'paraná' => 'PR', 'pernambuco' => 'PE', 'piaui' => 'PI', 'piauí' => 'PI',
        'rio de janeiro' => 'RJ', 'rio grande do norte' => 'RN', 'rio grande do sul' => 'RS',
        'rondonia' => 'RO', 'rondônia' => 'RO', 'roraima' => 'RR', 'santa catarina' => 'SC',
        'sao paulo' => 'SP', 'são paulo' => 'SP', 'sergipe' => 'SE', 'tocantins' => 'TO',
    );
    if (isset($posted['estado'])) {
        $raw = is_array($posted['estado']) ? (string) reset($posted['estado']) : (string) $posted['estado'];
        $raw = trim($raw);
        if (strlen($raw) === 2) {
            $posted['estado'] = strtoupper($raw);
        } else {
            $key = function_exists('mb_strtolower') ? mb_strtolower($raw, 'UTF-8') : strtolower($raw);
            if (isset($uf_map[$key])) {
                $posted['estado'] = $uf_map[$key];
            }
        }
    }
    return $posted;
}, 5);

/** Laser: Nilópolis vende laser no catálogo mas faltava no select easyunit do CF7. */
add_filter('wpcf7_form_tag', function ($tag) {
    if (!is_array($tag) || ($tag['name'] ?? '') !== 'easyunit') {
        return $tag;
    }
    $values = isset($tag['values']) && is_array($tag['values']) ? $tag['values'] : array();
    $labels = isset($tag['labels']) && is_array($tag['labels']) ? $tag['labels'] : array();
    $blob = strtolower(implode(' ', array_merge($values, $labels)));
    if (strpos($blob, 'nilopolis') !== false) {
        return $tag;
    }
    $values[] = 'nilopolis';
    $labels[] = 'RJ - Nilópolis';
    $tag['values'] = $values;
    $tag['labels'] = $labels;
    if (isset($tag['raw_values']) && is_array($tag['raw_values'])) {
        $tag['raw_values'][] = 'RJ - Nilópolis|nilopolis';
    }
    return $tag;
}, 20);

add_filter('wpcf7_form_elements', function ($html) {
    if (!is_string($html) || stripos($html, 'name="easyunit"') === false) {
        return $html;
    }
    if (stripos($html, 'nilopolis') !== false) {
        return $html;
    }
    $opt = '<option value="nilopolis">RJ - Nilópolis</option>';
    // Insere antes do fechamento do select easyunit.
    return preg_replace(
        '/(<select[^>]*name=("|\')easyunit\2[^>]*>)([\s\S]*?)(<\/select>)/i',
        '$1$3' . $opt . '$4',
        $html,
        1
    );
}, 20);

add_filter('wpcf7_validate_text', 'pm_cf7_reject_email_as_name', 20, 2);
add_filter('wpcf7_validate_text*', 'pm_cf7_reject_email_as_name', 20, 2);
function pm_cf7_reject_email_as_name($result, $tag) {
    $name = isset($tag->name) ? $tag->name : '';
    if ($name !== 'your-name') {
        return $result;
    }
    $value = isset($_POST['your-name']) ? trim((string) $_POST['your-name']) : '';
    if ($value !== '' && strpos($value, '@') !== false) {
        $result->invalidate($tag, 'Informe seu nome completo (não use e-mail no campo Nome).');
    }
    return $result;
}

/** Estado/UF: só aceita sigla cadastrada (AC…TO). */
add_filter('wpcf7_validate_text', 'pm_cf7_validate_estado_uf', 21, 2);
add_filter('wpcf7_validate_text*', 'pm_cf7_validate_estado_uf', 21, 2);
function pm_cf7_validate_estado_uf($result, $tag) {
    $name = isset($tag->name) ? $tag->name : '';
    if ($name !== 'estado') {
        return $result;
    }
    $value = isset($_POST['estado']) ? strtoupper(trim((string) $_POST['estado'])) : '';
    $ufs = array(
        'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
        'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO',
    );
    if ($value === '' || !in_array($value, $ufs, true)) {
        $result->invalidate($tag, 'Selecione a UF na lista (ex.: RJ).');
    }
    return $result;
}

/** Pedidos (CF7/Accesstage): UF billing/shipping sempre 2 letras. */
add_action('woocommerce_order_status_processing', 'pm_normalize_order_state_uf', 5, 1);
add_action('woocommerce_order_status_completed', 'pm_normalize_order_state_uf', 5, 1);
add_action('woocommerce_new_order', 'pm_normalize_order_state_uf', 40, 1);
function pm_normalize_order_state_uf($order_id) {
    static $busy = array();
    $order_id = intval($order_id);
    if ($order_id <= 0 || isset($busy[$order_id])) {
        return;
    }
    $order = wc_get_order($order_id);
    if (!$order) {
        return;
    }
    $uf_map = array(
        'acre' => 'AC', 'alagoas' => 'AL', 'amapa' => 'AP', 'amapá' => 'AP', 'amazonas' => 'AM',
        'bahia' => 'BA', 'ceara' => 'CE', 'ceará' => 'CE', 'distrito federal' => 'DF',
        'espirito santo' => 'ES', 'espírito santo' => 'ES', 'goias' => 'GO', 'goiás' => 'GO',
        'maranhao' => 'MA', 'maranhão' => 'MA', 'mato grosso' => 'MT', 'mato grosso do sul' => 'MS',
        'minas gerais' => 'MG', 'para' => 'PA', 'pará' => 'PA', 'paraiba' => 'PB', 'paraíba' => 'PB',
        'parana' => 'PR', 'paraná' => 'PR', 'pernambuco' => 'PE', 'piaui' => 'PI', 'piauí' => 'PI',
        'rio de janeiro' => 'RJ', 'rio grande do norte' => 'RN', 'rio grande do sul' => 'RS',
        'rondonia' => 'RO', 'rondônia' => 'RO', 'roraima' => 'RR', 'santa catarina' => 'SC',
        'sao paulo' => 'SP', 'são paulo' => 'SP', 'sergipe' => 'SE', 'tocantins' => 'TO',
    );
    $changed = false;
    foreach (array('billing', 'shipping') as $side) {
        $getter = "get_{$side}_state";
        $setter = "set_{$side}_state";
        if (!method_exists($order, $getter)) {
            continue;
        }
        $state = trim((string) $order->$getter());
        if ($state === '') {
            continue;
        }
        if (strlen($state) === 2) {
            $up = strtoupper($state);
            if ($up !== $state) {
                $order->$setter($up);
                $changed = true;
            }
            continue;
        }
        $key = function_exists('mb_strtolower') ? mb_strtolower($state, 'UTF-8') : strtolower($state);
        if (isset($uf_map[$key])) {
            $order->$setter($uf_map[$key]);
            $changed = true;
        }
    }
    // Nome = e-mail no billing: limpar first_name (não inventar nome).
    $fn = trim((string) $order->get_billing_first_name());
    if ($fn !== '' && strpos($fn, '@') !== false) {
        $order->set_billing_first_name('');
        $changed = true;
    }
    if ($changed) {
        $busy[$order_id] = true;
        $order->save();
        unset($busy[$order_id]);
    }
}

/** Cliente criado sem display_name: copiar nome válido do pedido mais recente. */
add_action('woocommerce_created_customer', function ($customer_id) {
    $user = get_user_by('id', $customer_id);
    if (!$user) {
        return;
    }
    $login = (string) $user->user_login;
    $email = (string) $user->user_email;
    $orders = wc_get_orders(array(
        'customer' => $customer_id,
        'limit' => 1,
        'orderby' => 'date',
        'order' => 'DESC',
        'return' => 'objects',
    ));
    $name = '';
    if ($orders) {
        $name = trim((string) $orders[0]->get_billing_first_name());
    }
    if ($name === '' || strpos($name, '@') !== false) {
        return;
    }
    if ($user->first_name === '' || $user->first_name === $email || strpos((string) $user->first_name, '@') !== false) {
        wp_update_user(array(
            'ID' => $customer_id,
            'first_name' => $name,
            'display_name' => $name,
        ));
    }
}, 20, 1);

add_action('user_register', function ($user_id) {
    $user = get_user_by('id', $user_id);
    if (!$user) {
        return;
    }
    $email = (string) $user->user_email;
    if ($user->display_name && $user->display_name !== $email && strpos((string) $user->display_name, '@') === false) {
        return;
    }
    // Sem nome válido no registro CF7: display_name fica e-mail; pedido corrige via hook acima.
}, 20, 1);
