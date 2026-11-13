/**
 * pm-accesstage-order-total-sync
 *
 * Após payment_CF7 (Accesstage) criar o pedido Woo com preços de catálogo,
 * alinha LINHAS + total ao totalamount cobrado no cartão (hidden CF7 #1831).
 *
 * Hook priority 20 — depois do payment_CF7 do child theme (priority 10).
 */

if (!defined('ABSPATH')) {
	return;
}

add_action('wpcf7_before_send_mail', 'pm_accesstage_sync_order_total', 20);

/**
 * @param WPCF7_ContactForm $wpcf7
 */
function pm_accesstage_sync_order_total($wpcf7) {
	if (!is_object($wpcf7) || (int) $wpcf7->id() !== 1831) {
		return;
	}
	if (!function_exists('wc_get_orders')) {
		return;
	}

	$submission = class_exists('WPCF7_Submission') ? WPCF7_Submission::get_instance() : null;
	if (!$submission) {
		return;
	}

	$posted = $submission->get_posted_data();
	if (!is_array($posted)) {
		return;
	}

	$raw = isset($posted['totalamount']) ? $posted['totalamount'] : '';
	if (is_array($raw)) {
		$raw = reset($raw);
	}
	$charged = round((float) str_replace(',', '.', (string) $raw), 2);
	if ($charged < 0) {
		return;
	}

	$email = isset($posted['your-email']) ? sanitize_email((string) $posted['your-email']) : '';
	if ($email === '') {
		return;
	}

	$orders = wc_get_orders(
		array(
			'billing_email' => $email,
			'limit'         => 5,
			'orderby'       => 'date',
			'order'         => 'DESC',
			'status'        => array('processing', 'pending', 'on-hold', 'completed'),
		)
	);

	$order = null;
	foreach ($orders as $candidate) {
		if (!$candidate instanceof WC_Order) {
			continue;
		}
		$meta = $candidate->get_meta('Pedido Accesstage');
		if ($meta === '' || $meta === null) {
			continue;
		}
		$created = $candidate->get_date_created();
		if ($created && (time() - $created->getTimestamp()) > 180) {
			continue;
		}
		$order = $candidate;
		break;
	}

	if (!$order) {
		return;
	}

	$items = array_values($order->get_items(array('line_item')));
	$weights = array();
	$weight_sum = 0.0;
	foreach ($items as $item) {
		$w = round((float) $item->get_total(), 2);
		if ($w <= 0) {
			$w = round((float) $item->get_subtotal(), 2);
		}
		if ($w <= 0) {
			$w = 1.0;
		}
		$weights[] = $w;
		$weight_sum += $w;
	}

	if ($weight_sum <= 0) {
		$weight_sum = 1.0;
		if ($items) {
			$weights = array_fill(0, count($items), 1.0);
		}
	}

	$remaining = $charged;
	$count = count($items);
	foreach ($items as $i => $item) {
		if ($i === $count - 1) {
			$share = round($remaining, 2);
		} else {
			$share = round($charged * ($weights[$i] / $weight_sum), 2);
			$remaining = round($remaining - $share, 2);
		}
		$qty = max(1, (int) $item->get_quantity());
		$item->set_subtotal($share);
		$item->set_total($share);
		if (method_exists($item, 'set_subtotal_tax')) {
			$item->set_subtotal_tax(0);
		}
		if (method_exists($item, 'set_total_tax')) {
			$item->set_total_tax(0);
		}
		// unit price visible in admin when qty>1
		if (method_exists($item, 'set_props')) {
			$item->set_props(
				array(
					'subtotal' => $share,
					'total'    => $share,
				)
			);
		}
		$item->save();
	}

	// Recibo = valor debitado: sem desconto/shipping/tax a mais
	if (method_exists($order, 'set_discount_total')) {
		$order->set_discount_total(0);
	}
	if (method_exists($order, 'set_discount_tax')) {
		$order->set_discount_tax(0);
	}
	if (method_exists($order, 'set_shipping_total')) {
		$order->set_shipping_total(0);
	}
	if (method_exists($order, 'set_cart_tax')) {
		$order->set_cart_tax(0);
	}
	if (method_exists($order, 'set_shipping_tax')) {
		$order->set_shipping_tax(0);
	}

	$order->set_total($charged);
	$order->update_meta_data('_pm_cf7_totalamount', wc_format_decimal($charged, 2));
	$order->update_meta_data('_pm_accesstage_lines_synced', '1');
	$order->update_meta_data(
		'_pm_accesstage_amount_cents',
		(string) (int) round($charged * 100)
	);

	if (function_exists('wc_get_logger')) {
		// no-op friendly; order note is enough for OT audit
	}
	$order->add_order_note(
		sprintf(
			'PM Accesstage sync: linhas+total alinhados a totalamount CF7 = %s (centavos %d).',
			wc_format_decimal($charged, 2),
			(int) round($charged * 100)
		)
	);

	$order->save();
}
