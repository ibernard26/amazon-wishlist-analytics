# Project Memory: Saved Clothing Cart for Later Ordering

- Captured: October 4, 2026.
- User instruction: save/update the project now; retrieve it only when asked in a
  week or two (roughly October 11–18, 2026). No scheduled reminder or order.
- Preserve every one of the 23 stable `CART-001`–`CART-023` functional rows.
- Historical original-request budget: $862.74 USD before tax/shipping, not a
  current quote. No replacement price has been confirmed.
- Database: `./data/wishlist.db` (local only; do not commit it or browser sessions).

## Canonical retrieval

Read `cart.json`, `amazon_asin_matches.json`, and
`amazon-shopping-cart-deployment.json` from the same GitHub revision. Run
`python run.py saved-cart --json` to validate and retrieve the full plan without
touching Amazon. Use stable cart IDs to connect the original request and selected
variant; package count is not order quantity.

## Formerly blocked rows — keep all ten in the plan

| Row | Saved decision | Constraint or pending check |
| --- | --- | --- |
| CART-001 | NELEUS `B078N5CCB5`, XXL black 3-pack | Workout tank substitute; different fabric/fit from Ekkovision |
| CART-002 | NELEUS `B0B42F61DT`, XXL white 3-pack | Workout tank substitute; different fabric/fit from Ekkovision |
| CART-003 | Hanes `B086KYKR6Q`, XL Black/Gray 6-pack | Color assortment/style differs from requested Performance Stretch pack |
| CART-004 | Hanes `B086KSDTQ4`, Large Black/Gray 6-pack | Same tradeoff; keep XL and Large as separate intentional rows |
| CART-005 | PUMA `B07NNTCV5K`, black 8-pack, size 10–13 | Low-cut synthetic replaces bamboo crew; review height/material preference |
| CART-006 | Uporee `B0D833JK8F`, White/Large/6 pairs | Manual US offer/child check; keep ankle-sock use |
| CART-007 | Pure Champ `B09ZCDYPR6`, Large/Set 1/3-pack | Regional exact identity; manual current US offer check |
| CART-014 | True Classic `B0F4JH1CBS`, Curved Hem/Military Green/Large | Original identity matched in prior variation research |
| CART-015 | Retain VEIISAR T3 Coffee/Large, purchase ASIN unresolved | `B0C7L5HH9Y` is a color-only candidate; `B0C7L73TR4` has conflicting Grey/Black 3XL evidence and must not be ordered as Coffee/Large |
| CART-018 | True Classic `B0GP4GBSFX`, Large Black/Grove/White 3-pack | Different fit and Grove replaces Navy; retain original oversized request for review |

The other 13 original rows retain their previously identified ASINs. Total:
14 original identities, 6 selected substitute identities, 3 manual-review rows.
All 23 still need fresh price/stock/seller/delivery review before staging.

## Next-session purchase review

1. Retrieve the latest three files and verify the 23-row consistency checks.
2. Recheck every Amazon.com child ASIN, size, color, pack, quantity, seller,
   return policy, current USD price, stock, and delivery.
3. Resolve CART-006, CART-007, and CART-015 without silently omitting them.
4. Review the six substitutes' tradeoffs with the user if any preference changed.
5. Recalculate the full total including tax/shipping and respect the existing
   $500 single-order safety budget. Do not automatically raise or bypass it.
6. Ask for explicit confirmation of final items/total/address/payment before
   any order submission. This saved plan authorizes no purchase.
