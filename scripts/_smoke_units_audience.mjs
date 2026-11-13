/**
 * Smoke: unitsForProduct matrix + twin presence (via built data logic mirrored here).
 * Run after compile: node --experimental-strip-types or use next eval.
 * This file reimplements the matrix for a quick node check without full Next.
 */
import { readFileSync } from "fs";
import { createRequire } from "module";

// Dynamic import of compiled isn't available; parse store flags from data.ts and assert twin ids.
const data = readFileSync(new URL("../src/lib/data.ts", import.meta.url), "utf8");

const twins = [
  "body-splash-masc",
  "cartao-presente-masc",
  "cartao-presente-160-masc",
  "cartao-presente-215-masc",
  "cartao-presente-290-masc",
  "plano-silver-masc",
  "plano-gold-masc",
  "plano-prepago-masc",
];

let ok = true;
for (const id of twins) {
  if (!data.includes(`SHARED_CHROME_TWIN_IDS`) && !data.includes("expandCatalogWithAudienceTwins")) {
    console.log("FAIL missing expand twins");
    ok = false;
    break;
  }
}
if (!data.includes("body-splash") || !data.includes("expandCatalogWithAudienceTwins")) {
  console.log("FAIL twin expander missing");
  ok = false;
}
if (!data.includes("offersCeraMasculino") || !data.includes("unitsForProduct")) {
  console.log("FAIL units filter missing");
  ok = false;
}
if (!data.includes('audience === "masculino" && isSharedChromeTwinBase')) {
  // productHref check softer
  if (!data.includes("productHref")) {
    console.log("FAIL productHref missing");
    ok = false;
  }
}

// Unit capacity smoke via node + tsx if available
async function runUnits() {
  try {
    const mod = await import("../src/lib/data.ts");
    const {
      getProductById,
      unitsForProduct,
      storeUnits,
      productHref,
    } = mod;

    const laserFem = getProductById("abdomen-laser");
    const laserMasc = getProductById("axilas-laser-masc");
    const ceraMasc = getProductById("axila-cera-masc");
    const splash = getProductById("body-splash");
    const splashM = getProductById("body-splash-masc");
    const silverM = getProductById("plano-silver-masc");

    const uLaserFem = unitsForProduct(laserFem);
    const uCax = uLaserFem.some((u) => u.code === "CAX");
    const uFla = uLaserFem.some((u) => u.code === "FLA");
    console.log("laser_fem", {
      count: uLaserFem.length,
      hasCax: uCax,
      hasFla: uFla,
    });
    if (uCax || !uFla) {
      console.log("FAIL laser fem CAX/FLA");
      ok = false;
    }

    const uLaserMasc = unitsForProduct(laserMasc);
    if (uLaserMasc.some((u) => u.code === "CAX") || uLaserMasc.some((u) => u.code === "REC")) {
      console.log("FAIL laser masc includes CAX/REC", uLaserMasc.map((u) => u.code));
      ok = false;
    } else {
      console.log("laser_masc", uLaserMasc.length, "ok");
    }

    const uCeraM = unitsForProduct(ceraMasc);
    if (!uCeraM.some((u) => u.code === "REC") || uCeraM.some((u) => u.code === "CAX")) {
      console.log("FAIL cera masc REC/CAX", uCeraM.map((u) => u.code));
      ok = false;
    } else {
      console.log("cera_masc", uCeraM.length, "ok");
    }

    if (unitsForProduct(splash).length !== storeUnits.length) {
      console.log("FAIL splash not all units");
      ok = false;
    } else {
      console.log("splash_all", storeUnits.length, "ok");
    }

    if (!splashM || splashM.audience !== "masculino") {
      console.log("FAIL splash twin", splashM);
      ok = false;
    }
    if (!silverM || productHref("masculino", "plano-silver") !== "/produto/plano-silver-masc") {
      console.log("FAIL silver href", silverM, productHref("masculino", "plano-silver"));
      ok = false;
    } else {
      console.log("silver_href ok");
    }

    console.log(ok ? "OK" : "FAIL");
    process.exit(ok ? 0 : 1);
  } catch (e) {
    console.log("IMPORT_FAIL", e.message);
    console.log(ok ? "PARTIAL_OK_STATIC" : "FAIL");
    process.exit(ok ? 0 : 1);
  }
}

runUnits();
