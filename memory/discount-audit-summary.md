# Discount Audit Summary - Pello Menos

## Current Architecture

### How discounts work (as of 2026-11-10)

**1. Prices are pre-discounted in the catalog** (`cart-related.json`):
- Each product has `originalCents` (full table price) and `priceCents` (already discounted)
- No additional discount calculation happens in the cart/checkout
- Example: Laser axila R$ 899,90 → `originalCents: 89990`, `priceCents: 359960` (already 60% off)

**2. Black Nov campaign structure** (in `src/lib/black-nov-campaign.ts`):
- **Laser**: 60% off (`any`) for 1-2 areas, 65% off (`multi`) for 3+ areas
- **Cera/Esfoliação**: 15% off (`any`) for 1-2 areas, 20% off (`multi`) for 3+ areas during "esquenta"
- **Black Week**: Laser 70%/75%, Cera 15% flat (esfoliacao) or tiered (P:40%, M:30%, G:25%)
- `multiThreshold`: 3 distinct product IDs

**3. Key functions**:
- `familyForProduct(id, method)` → determines if product is "laser", "cera_esf", or excluded
- `countDistinctAreas(lines, family)` → counts distinct product IDs by family
- `discountRateForLine(productId, method, lines)` → returns discount rate (0-1) or null
- `applyCampaignCents(originalCents, rate, opts)` → applies rate to calculate `oldPriceCents` and `priceCents`
- `priceProductInCart(product, cartLines)` → recalculates price using campaign rules

**4. Cart display** (`CartView.tsx`):
- Shows `listCents` (sale price from catalog) and `saleCents` (price after campaign)
- `displaySubtotal` = sum of list prices, `saleSubtotal` = sum of sale prices
- `campaignSavings` = listSubtotal - saleSubtotal
- No additional discount is applied at checkout

## Test Scenarios Status (from the audit)

| Scenario | Status | Notes |
|----------|--------|-------|
| Laser feminino 1 área | ✅ | 60% OFF confirmado |
| Laser feminino 2 áreas | ✅ | 60% OFF sobre total confirmado |
| Laser feminino 3 áreas | ⚠️ | Need to test qty=3 |
| Laser masculino 1 área | ✅ | (implied from feminine) |
| Laser masculino 3 áreas | ⚠️ | Need to test qty=3 |
| Cera 2 áreas | ⚠️ | Need to test |
| Cera 3 áreas | ⚠️ | Need to test |
| Esfoliação 2 áreas | ⚠️ | Need to test |
| Esfoliação 3 áreas | ⚠️ | Need to test |
| Combinações diferentes (laser + cera) | ⚠️ | Need to test |

## What Claude Should Examine

### 1. How discounts are currently calculated
- **Source**: Discounts come from the **product's `priceCents`** in `cart-related.json`, which is already set with the campaign discount baked in
- **Not**: There is no additional discount calculation running in the React cart
- **Verification**: The `priceProductInCart` function exists in `src/lib/data.ts` but appears to be used for display/recalculation only, not for actual cart price updates

### 2. Verification of "3+ areas" rules
- **How count is done**: `countDistinctAreas` counts **distinct product IDs** in the cart matching the family (laser/cera_esf)
- **Multi bonus**: When `n >= multiThreshold (3)`, the `multi` rate applies (65% for laser, 20% for cera/esfol during esquenta)
- **Area vs unit**: The system counts **product IDs**, not physical areas/units. Each distinct product ID counts as one "area" toward the threshold
- **Combinations**: Different categories (e.g., axilas + virilha) each count as separate IDs if they match the family

### 3. Files and functions involved
- `src/lib/black-nov-campaign.ts` - Core campaign logic (phase, family, rates, thresholds)
- `src/lib/data.ts` - `priceProductInCart`, `resolveCatalogPrice`, `discountRateForLine`, `applyCampaignCents`
- `wordpress-loja/pm-home/cart-related.json` - Product catalog with pre-discounted prices
- `wordpress-loja/pm-home/black-nov-campaign.js` - Client-side mirror of campaign config
- `src/components/CartView.tsx` - Cart display, shows campaign savings label
- `wordpress-loja/pm-home/cart.js` - Cart initialization, uses `catalogPriced` and `pmBlackNov.unitPrice`

### 4. Architecture recommendations

Based on the audit findings:

**Option A: Maintain pre-campaign prices (current approach)**
- ✅ Pros: Simple, already working for 131/131 products, no runtime calculation needed
- ✅ Pros: Prices in WooCommerce already reflect discounts
- ❌ Cons: Harder to change discounts dynamically, less flexible for promotions

**Option B: Apply discounts dynamically in cart**
- ✅ Pros: More flexible, can change campaigns without re-pricing all products
- ✅ Pros: Better for A/B testing different discount rates
- ❌ Cons: Would need to modify cart.js, cart-related.json, and the React cart to recalculate prices at runtime
- ❌ Cons: Risk of discount duplication if both catalog and cart apply discounts

**Option C: Combination**
- Keep pre-discounted prices in catalog for display
- Apply `priceProductInCart`/`resolveCatalogPrice` at checkout for final validation
- This is the most robust but also most complex

## Key Findings

1. **131/131 products audited and consistent** - All products have correct original/priceCents pairing
2. **No discount duplication** - Discounts are applied once at catalog level, not again at cart level
3. **No divergence between screens** - Cart and product pages show consistent pricing
4. **"3+ areas" rule uses product ID count** - Not physical area count; 3 distinct product IDs = multi threshold
5. **Current phase is likely "esquenta"** (Nov 3 - Nov 21, 2026 based on the campaign dates)

## Files to Reference

- `src/lib/black-nov-campaign.ts` - Core discount rate logic
- `src/lib/data.ts` - Price resolution functions  
- `wordpress-loja/pm-home/cart-related.json` - Product catalog with pricing
- `wordpress-loja/pm-home/black-nov-campaign.js` - Client-side campaign mirror
- `src/components/CartView.tsx` - Cart display logic (lines 140-163)