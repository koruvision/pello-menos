# -*- coding: utf-8 -*-
"""Inject document links into plan long descriptions in product-copy.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COPY = ROOT / "src" / "lib" / "product-copy.json"

# Under /images/docs so Next + export WP (ASSET media) keep the same path.
DOC = "/images/docs"

BLOCKS = {
    "plano-silver": f"""CONSULTA E ANÁLISE

Antes de concluir a compra, leia os documentos oficiais:

• Contrato dos Planos de Assinatura VIP: {DOC}/contrato-planos-assinaturas-vip.html
• Termo de Consentimento para Tratamento de Dados Pessoais: {DOC}/termo-consentimento-dados-pessoais.pdf
• Termos e Condições de Uso: {DOC}/termo-termos-e-condicoes-de-uso-pello-menos.pdf

REGRAS DE COMPRA""",
    "plano-gold": f"""CONSULTA E ANÁLISE

Antes de concluir a compra, leia os documentos oficiais:

• Contrato dos Planos de Assinatura VIP: {DOC}/contrato-planos-assinaturas-vip.html
• Termo de Consentimento para Tratamento de Dados Pessoais: {DOC}/termo-consentimento-dados-pessoais.pdf
• Termos e Condições de Uso: {DOC}/termo-termos-e-condicoes-de-uso-pello-menos.pdf

REGRAS DE COMPRA""",
    "plano-clube-laser": f"""CONSULTA E ANÁLISE

Antes de concluir a compra, leia os documentos oficiais:

• Contrato Clube do Laser: {DOC}/contrato-clube-do-laser.html
• Arquivo do contrato (DOCX): {DOC}/contrato-clube-do-laser.docx
• Contrato Laser Serviço Avulso: {DOC}/contrato-laser-servico-avulso.html
• Termo de Consentimento para Tratamento de Dados Pessoais: {DOC}/termo-consentimento-dados-pessoais.pdf
• Termos e Condições de Uso: {DOC}/termo-termos-e-condicoes-de-uso-pello-menos.pdf

REGRAS DE COMPRA""",
    "plano-prepago": f"""CONSULTA E ANÁLISE

Antes de concluir a compra, leia os documentos oficiais:

• Pacote de serviços cera – Pagamento antecipado: {DOC}/pacote-servicos-cera-pagamento-antecipado.html
• Termo de Consentimento para Tratamento de Dados Pessoais: {DOC}/termo-consentimento-dados-pessoais.pdf
• Termos e Condições de Uso: {DOC}/termo-termos-e-condicoes-de-uso-pello-menos.pdf

REGRAS DE COMPRA""",
}


def replace_consulta(long: str, block: str) -> str:
    start = long.find("CONSULTA E ANÁLISE")
    end = long.find("REGRAS DE COMPRA")
    if start < 0 or end < 0 or end <= start:
        raise SystemExit("markers not found")
    return long[:start] + block + long[end + len("REGRAS DE COMPRA") :]


def main() -> None:
    data = json.loads(COPY.read_text(encoding="utf-8"))
    for key, block in BLOCKS.items():
        if key not in data:
            raise SystemExit(f"missing {key}")
        data[key]["long"] = replace_consulta(data[key]["long"], block)
        print("updated", key)
    COPY.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
