# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "wordpress-loja" / "pm-home" / "compra-nao-realizada.html"
t = p.read_text(encoding="utf-8")

old = """  <div class="mt-8 flex flex-wrap gap-3">
    <a class="btn-lux btn-lux-primary inline-flex rounded-full px-6 py-3 text-sm font-semibold text-on-primary" href="/finalizar-pagamento/">Tentar novamente</a>
    <a class="inline-flex rounded-full border border-primary/30 px-6 py-3 text-sm font-semibold text-primary" href="/carrinho/">Voltar ao carrinho</a>
    <a class="inline-flex rounded-full border border-primary/30 px-6 py-3 text-sm font-semibold text-primary" href="https://wa.me/552125494265?text=Ol%C3%A1!%20Tive%20problema%20no%20pagamento%20da%20loja." target="_blank" rel="noreferrer">Falar no WhatsApp</a>
  </div>"""

new = """  <div class="mt-8 flex flex-wrap gap-3">
    <a class="btn-lux btn-lux-primary inline-flex items-center gap-2 rounded-full px-6 py-3 text-sm font-semibold text-on-primary" href="/finalizar-pagamento/"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg><span>Tentar novamente</span></a>
    <a class="inline-flex items-center gap-2 rounded-full border border-primary/30 px-6 py-3 text-sm font-semibold text-primary" href="/carrinho/"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg><span>Voltar ao carrinho</span></a>
    <a class="inline-flex items-center gap-2 rounded-full border border-primary/30 px-6 py-3 text-sm font-semibold text-primary" href="https://wa.me/552125494265?text=Ol%C3%A1!%20Tive%20problema%20no%20pagamento%20da%20loja." target="_blank" rel="noreferrer"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.435 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/></svg><span>Falar no WhatsApp</span></a>
  </div>"""

if old not in t:
    raise SystemExit("old block missing")
p.write_text(t.replace(old, new), encoding="utf-8")
print("patched", p.stat().st_size)
