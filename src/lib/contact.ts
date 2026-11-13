/**
 * Contato oficial Pello Menos — mesmos canais do rodapé da loja.
 * O número é da consultora de laser (Mariana): a mensagem pré-preenchida fala só de laser;
 * cera, linha e esfoliação se compram pelo site. Aguardando aprovação da Adriana (29/10).
 */
export const WHATSAPP_TEXT =
  "Olá! Quero tirar dúvidas sobre a depilação a laser da Pello Menos. (Cera, linha e esfoliação eu compro direto no site.)";

/** Mensagem pré-preenchida dos links de SAC (rodapé e ícone social). */
export const WHATSAPP_SAC_TEXT =
  "Olá! Gostaria de falar com o SAC Pello Menos.";

/** Número exibido no rodapé. */
export const WHATSAPP_DISPLAY = "(21) 2549-4265";

/** E.164 sem + — Brasil 55 + DDD 21 + 2549-4265. */
export const WHATSAPP_E164 = "552125494265";

export function whatsappHref(text = WHATSAPP_TEXT) {
  const encoded = encodeURIComponent(text);
  if (WHATSAPP_E164) {
    return `https://wa.me/${WHATSAPP_E164}?text=${encoded}`;
  }
  return `https://wa.me/?text=${encoded}`;
}
