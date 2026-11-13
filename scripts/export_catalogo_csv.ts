import { writeFileSync } from "node:fs";
import {
  categoryLabels,
  isSharedProduct,
  methodLabels,
  products,
} from "../src/lib/data.ts";

const SITE = "https://pellomenos.companygenesis.com.br";

const headers = [
  "id",
  "nome",
  "publico",
  "tipo",
  "categoria",
  "duracao",
  "preco",
  "sku",
  "codigo",
  "selo",
  "destaque",
  "descricao",
  "link_da_ficha",
  "imagem",
];

function cell(value: unknown) {
  const text = String(value ?? "");
  if (/[;"\n\r]/.test(text)) return `"${text.replace(/"/g, '""')}"`;
  return text;
}

function money(cents: number | undefined) {
  if (cents == null) return "";
  return (cents / 100).toFixed(2).replace(".", ",");
}

const rows = products.map((product) => {
  const publico = isSharedProduct(product)
    ? "Feminino e masculino"
    : product.audience === "masculino"
      ? "Masculino"
      : "Feminino";
  return [
    product.id,
    product.name,
    publico,
    methodLabels[product.method],
    categoryLabels[product.category],
    product.duration,
    money(product.oldPriceCents ?? product.priceCents),
    product.sku,
    product.code,
    product.badge ?? "",
    product.highlight ? "sim" : "",
    product.description,
    `${SITE}/produto/${product.id}/`,
    `${SITE}/wp-content/uploads/pm-home/media${product.image}`,
  ];
});

const csv =
  "\uFEFF" +
  [headers, ...rows].map((row) => row.map(cell).join(";")).join("\r\n") +
  "\r\n";
writeFileSync("catalogo-pello-menos.csv", csv, "utf8");
console.log("itens", rows.length);
console.log("ultima coluna", headers.at(-1));
console.log(rows[0][1], rows[0][6], rows[0].at(-1));
