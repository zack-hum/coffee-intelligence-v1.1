# Costa Rica sourcing specifics — how coffee is bought, priced and moved (2026-10-17)

Focus: what Z needs to understand on the ground in January 2027 (peak harvest) to scout supply,
talk price with micro-mills and broker lots to roasters — and what that means for the product.
Paraphrased; figures are as reported by the linked sources.

## 1. Market snapshot going into the 2026/27 harvest

- **Volume is small and shrinking structurally.** USDA FAS (via Daily Coffee News, Jun 2026)
  forecasts MY2026/27 at ~1.2 M 60-kg bags (+3.5%, "on" year of the biennial cycle) after
  1.16 M in 2025/26; exports ~1.06 M bags, the US taking ~40% of green exports. Grower count
  fell to 24,653 (≈ half of a decade earlier); planted area ~83 kha. [DCN, 2026-06-03]
- **Prices fell hard through the 2025/26 season.** NY arabica dropped from ~$440 to ~$290 per
  quintal between Oct 2025 and Apr 2026; ICAFE's average export price for 2025/26 was
  ~$340/quintal. Projection for 2026/27: $240–280/quintal. [CRHoy, 2026-05-08]
- **The colón is the story for producers.** Average harvest exchange rate went from ₡650/USD
  (2021/22) to ₡460 (2025/26), with ₡440–460 projected for 2026/27. Growers sell in dollars
  and are paid in colones, so local revenue is down ~30% since 2021/22. [CRHoy; DCN]
- **Farmgate (ICAFE liquidación):** ₡115,754 per fanega for 2025/26; ICAFE projects
  ₡83,000–99,000 for 2026/27 — below its own example production cost of ~₡114,700/fanega at
  18 fanegas/ha. Producer groups call 2026/27 a "perfect storm". [CRHoy]
- **Weather risk:** IMN expects El Niño in H2 2026, possibly 10–30% less rain in some areas. [DCN]
- **Labour:** most picking is done by Ngäbe-Buglé workers from Panama; ~78,500 direct jobs at
  the Dec–Jan peak; migration paperwork delays are a recurring risk. [DCN; CRHoy]

**Our arithmetic (approximate, for intuition only):** ₡115,754 ÷ ₡459.65 ≈ $252 per fanega.
One fanega of cherry yields roughly one 46-kg quintal of green (the convention already in
`app.js`), so ≈ $2.48/lb green-equivalent at farmgate vs ≈ $3.35/lb average export price —
a producer share of ~74% of export value before the mill's and exporter's costs.

## 2. How the system works (what a buyer needs to know)

- **ICAFE (Law 2762) regulates the producer–mill–exporter chain.** It sets/approves the
  minimum final price mills must pay producers, caps mill (beneficio) margins at ~9% of
  sale value, and collects ~1.5% on every export; exporters typically charge 1.5–2.5%.
  The rule of thumb is that ~80% of the net sale price goes to the farmer. [Royal NY, 2025-04-28;
  Cafe Imports, 2023-05-08]
- **Payment timing:** cherry is delivered to collection centres that post a price per fanega;
  farmers get an advance quickly (often next day) and a **liquidación** (final settlement)
  after the mill sells, based on grade, costs and NY prices. [Royal NY; CRHoy]
- **Who you buy from:** cooperatives (~40% of production), large private beneficios, and
  **micro-mills** (one opened roughly every month since 2016; the smallest, <1,000
  fanegas/year, now ~3% of volume). Micro-mills sell directly or through exporters/agents and
  carry quality risk themselves; many still use a co-op or large mill for dry milling and
  export paperwork. Most specialty microlots imported to the US come from this channel.
  [Royal NY; Cafe Imports]
- **What this means for a foreign buyer:** you normally contract with a **registered
  exporter** (which may be the micro-mill itself if registered, or a dry mill/exporter acting
  for it); the contract is registered with ICAFE and the export levy applies. Exact
  registration steps were not found in a free English source this run — worth asking
  exporters and ICAFE directly on the trip (see "On-the-ground questions").
- **Processing as a price lever:** naturals and honeys earn premiums and need less water and
  space, so many micro-mills favour them; anaerobic/experimental lots are common. [Royal NY]
- **EUDR:** Costa Rica is seen as well-placed (detailed land-use records, strong environmental
  protection) but traceability work is still ongoing; it is not one of the countries with an
  Enveritas territorial agreement. EU application dates have moved more than once — as far as we
  know the current timetable starts with large/medium operators from 30 Dec 2026 and micro/small from 30 Jun 2027 (see our 2026-10-16 segment note);
  re-check before relying on it. Relevant mainly if Z brokers to EU roasters. [StoneX, 2026-07-28;
  Algrano, 2024-04-24; DCN]

## 3. On-the-ground questions for Z's January visits

1. Are you a registered exporter, or who exports for you? Who does your dry milling?
2. What did you pay/receive per fanega this season (advance vs expected liquidación)?
3. FOB price per lb for this lot, minimum lot size, and when is it ready to ship (Puerto Limón / Caldera)?
4. Processing, altitude, variety, picking dates, moisture/water activity of parchment?
5. Can you provide farm polygons/geolocation (EUDR) and ICAFE registration numbers?
6. Pre-shipment and arrival samples — how many grams, sent how, and at whose cost?

## Implications for us

- **Offer check (#9) should show the farmgate side too.** Add the ICAFE liquidación
  (₡/fanega, dated, with exchange rate) next to the FOB/implied price so Z can see the spread a
  micro-mill is working with — a unique, hard-to-copy join (ICAFE + FX + C price). Commented on #9
  rather than opening a new proposal (5 proposals already open).
- **Costa Rica page:** the colón/USD rate is as decisive as the C price for CR producers; the CR
  page should chart CRC/USD against C (FX series is free from BCCR/ECB-type sources — to verify in a
  data-sources run).
- **CRM v1 (#8) fields:** "exporter of record", "dry mill", "ICAFE registered (y/n)",
  "processing", "liquidación per fanega", "EUDR geolocation on file" — cheap to add, directly
  useful for the questions above.
- **Field mode (#10):** ship the question list above as the default visit template.
- Paid sources that would improve quality (not to be wired in): ICAFE's detailed liquidación
  tables by beneficio, if not freely published; commercial EUDR platforms.

## Sources

- [Costa Rica coffee report: production up but growers struggle to find profit — Daily Coffee News, 2026-06-03](https://dailycoffeenews.com/2026/06/03/costa-rica-coffee-report-production-up-but-growers-struggle-to-find-profit/)
- [Tipo de cambio y precios internacionales deterioran ingresos de los cafetaleros — CRHoy, 2026-05-08](https://crhoy.com/economia/tipo-de-cambio-y-precios-internacionales-deterioran-ingresos-de-los-cafetaleros)
- [Micro-mills of Costa Rica — Royal NY, 2025-04-28](https://www.royalny.com/?p=135974)
- [Costa Rica 101 Trip: A Recap — Cafe Imports, 2023-05-08](https://cafeimports.com/europe/blog/?p=51220)
- [EUDR is reshaping the global coffee trade — StoneX, 2026-07-28](https://www.stonex.com/en/insights/eudr-is-reshaping-the-global-coffee-trade-which-origins-are-best-positioned-to-meet-europe-s-new-requirements/)
- [EUDR coffee: territorial approach — Algrano, 2024-04-24](https://algrano.com/es/learn/eudr-coffee-territorial-approach-transition-period)
