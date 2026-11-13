/**
 * Cupons do e-commerce (reunião 29/10 com a diretoria).
 * O cupom existe no Woo (Marketing → Cupons) — aqui ficam só código e textos de vitrine.
 */

/** Primeira compra: 5% sobre o total do carrinho, 1 uso por cliente, não acumula com Black. */
export const FIRST_PURCHASE_COUPON = "PRIMEIRACOMPRA5";
export const FIRST_PURCHASE_PERCENT = 5;

/** Texto exigido por Adriana/Regina no lugar do genérico "Não foi possível aplicar este cupom." */
export const FIRST_PURCHASE_USED_MESSAGE =
  "Este cupom vale só para a primeira compra. Você já comprou na Pello Menos, então ele não se aplica.";

export const COUPON_GENERIC_ERROR = "Não foi possível aplicar este cupom.";

type WooError = { payload?: { code?: string; message?: string } };

/** Traduz o erro da Store API do Woo em frase para a cliente. */
export function couponErrorMessage(error: unknown, code: string): string {
  const payload = (error as WooError | null)?.payload;
  const raw = String(payload?.message ?? "");
  const isFirstPurchase = code.trim().toUpperCase() === FIRST_PURCHASE_COUPON;
  if (isFirstPurchase && /limite|limit|já (foi )?(usad|utilizad)|already/i.test(raw)) {
    return FIRST_PURCHASE_USED_MESSAGE;
  }
  if (/não existe|does not exist|inválido|invalid/i.test(raw)) {
    return "Cupom não encontrado. Confira o código e tente de novo.";
  }
  return raw || COUPON_GENERIC_ERROR;
}
