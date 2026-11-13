# -*- coding: utf-8 -*-
"""Testa a validacao do CF7 #1831 sem cobrar.

Envia o formulario pela API de feedback do CF7 com um erro proposital (e-mail invalido),
para que a validacao falhe ANTES do hook de pagamento. A resposta lista os campos
invalidos — assim sabemos se os selects de parcelas vazios sao rejeitados.
"""
from __future__ import annotations

import json
import sys
import urllib.request
import uuid

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://pellomenosoficialteste.companygenesis.com.br"


def build(fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = "----pm" + uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n"
        )
    parts.append(f"--{boundary}--\r\n")
    return "".join(parts).encode("utf-8"), f"multipart/form-data; boundary={boundary}"


def run(label: str, extra: dict[str, str]) -> None:
    base_fields = {
        "_wpcf7": "1831",
        "_wpcf7_version": "6.1.1",
        "_wpcf7_locale": "pt_BR",
        "_wpcf7_unit_tag": "wpcf7-f1831-o1",
        "_wpcf7_container_post": "0",
        "your-name": "Teste Validacao",
        "your-email": "EMAIL-INVALIDO-@@@",  # erro proposital: falha antes do pagamento
        "your-phone": "21999998888",
        "cpf": "123.456.789-01",
        "cep": "01310-100",
        "endereco": "Rua Teste",
        "numero": "100",
        "bairro": "Centro",
        "cidade": "Rio de Janeiro",
        "estado": "RJ",
        "unit": "RJ - Bangu",
        "cart": "34186",
        "cartqtd": "1",
        "totalamount": "836.00",
        "cupom": "",
        "cupomamount": "0.00",
        "fullvalue": "836.00",
        "category": "Serviços de Depilação a Laser",
        "subscribemode": "",
        "siteinstallment": "1",
        "declaracao": "1",
        "cart-number": "4000000000000002",
        "holder": "TESTE",
        "expiration": "12/2030",
        "securityCode": "123",
    }
    base_fields.update(extra)
    body, ctype = build(base_fields)
    req = urllib.request.Request(
        BASE + "/wp-json/contact-form-7/v1/contact-forms/1831/feedback",
        data=body,
        method="POST",
        headers={"Content-Type": ctype, "User-Agent": "pm-validate", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        print(label, "HTTP", e.code, e.read().decode("utf-8", "replace")[:300])
        return
    status = data.get("status")
    invalid = [f.get("field") for f in (data.get("invalid_fields") or [])]
    print(f"{label}: status={status} | invalidos={invalid}")
    if data.get("message"):
        print("   msg:", str(data["message"])[:160])


print("alvo:", BASE)
run("A) parcelas preenchidas (installments=1x)", {"installments": "1x"})
run("B) installments vazio, allinstallments=10x", {"installments": "", "allinstallments": "10x"})
run("C) todos vazios", {"installments": "", "cerainstallments": "", "allinstallments": ""})