/** Paths where cart/checkout chrome stays feminine and audience switch is hidden. */
export function isCheckoutFunnelPath(pathname: string) {
  return (
    pathname.startsWith("/carrinho") ||
    pathname.startsWith("/checkout") ||
    pathname.startsWith("/finalizar-pagamento") ||
    pathname.startsWith("/finaliza-compra")
  );
}
