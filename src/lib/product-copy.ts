import copy from "@/lib/product-copy.json";

export type ProductCopy = {
  short: string;
  long: string;
};

const copies = copy as Record<string, ProductCopy>;

export function productCopy(id: string): ProductCopy {
  if (copies[id]) return copies[id];
  if (id.endsWith("-masc")) {
    const base = id.slice(0, -5);
    if (copies[base]) return copies[base];
  }
  return { short: "", long: "" };
}
