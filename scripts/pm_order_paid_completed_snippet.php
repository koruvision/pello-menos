<?php
/**
 * Pedido pago (Accesstage) → status Concluído.
 * O payment_CF7 ainda grava processing; este snippet corrige assim que
 * a meta Pedido Accesstage existe. Não reenvia e-mail de concluído
 * (o tema já dispara WC_Email_Customer_Completed_Order na criação).
 */

if (!function_exists('pm_accesstage_mark_completed')) {
	function pm_accesstage_mark_completed($order_id) {
		static $busy = false;
		if ($busy || !$order_id || !function_exists('wc_get_order')) {
			return;
		}
		$order = wc_get_order($order_id);
		if (!$order || $order->get_status() !== 'processing') {
			return;
		}
		$acc = $order->get_meta('Pedido Accesstage');
		if ($acc === '' || $acc === null) {
			$acc = get_post_meta($order_id, 'Pedido Accesstage', true);
		}
		if (!$acc) {
			return;
		}
		$busy = true;
		add_filter('woocommerce_email_enabled_customer_completed_order', '__return_false', 999);
		$order->update_status('completed', 'Pagamento Accesstage confirmado.');
		remove_filter('woocommerce_email_enabled_customer_completed_order', '__return_false', 999);
		$busy = false;
	}
}

add_action('added_post_meta', function ($mid, $object_id, $meta_key, $meta_value) {
	if ($meta_key !== 'Pedido Accesstage' || !$meta_value) {
		return;
	}
	pm_accesstage_mark_completed((int) $object_id);
}, 10, 4);

add_action('updated_post_meta', function ($mid, $object_id, $meta_key, $meta_value) {
	if ($meta_key !== 'Pedido Accesstage' || !$meta_value) {
		return;
	}
	pm_accesstage_mark_completed((int) $object_id);
}, 10, 4);

add_action('woocommerce_thankyou', function ($order_id) {
	pm_accesstage_mark_completed((int) $order_id);
}, 5);

// Backfill em lotes: processing + Pedido Accesstage → completed (sem e-mail).
add_action('init', function () {
	if (get_option('pm_accesstage_completed_backfill_v1') || !function_exists('wc_get_orders')) {
		return;
	}
	add_filter('woocommerce_email_enabled_customer_completed_order', '__return_false', 999);
	$orders = wc_get_orders(array(
		'status' => 'processing',
		'limit' => 80,
		'orderby' => 'ID',
		'order' => 'ASC',
		'meta_query' => array(
			array(
				'key' => 'Pedido Accesstage',
				'compare' => 'EXISTS',
			),
		),
	));
	foreach ($orders as $order) {
		$order->update_status('completed', 'Ajuste: pagamento Accesstage já confirmado.');
	}
	remove_filter('woocommerce_email_enabled_customer_completed_order', '__return_false', 999);
	if (count($orders) < 80) {
		update_option('pm_accesstage_completed_backfill_v1', 1, true);
	}
}, 30);
