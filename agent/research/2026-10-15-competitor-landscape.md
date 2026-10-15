# Competitor & adjacent-software landscape — first pass (2026-10-15)

**Question:** Who already serves green-coffee sourcing for roasters, importers/exporters and cafes,
what do they charge, and where is the open ground for a free, intelligence-first platform?

**Method:** Web search plus reading the vendors' own pages and trade-press coverage (Daily Coffee
News, Sprudge, Fresh Cup, BeanScene). Paraphrased; prices as listed on the date above. Rows are
summarised in [`agent/COMPETITORS.md`](../COMPETITORS.md).

## The market splits into five groups

### 1. Green-coffee marketplaces (buy-side discovery and transactions)
- **Algrano** (Switzerland, since 2015). Producers and roasters get verified profiles and talk
  directly. Algrano runs the logistics, with exporters/importers paid on commission. Shared
  shipments let small roasters buy from one 60-kg bag. US launch in 2023 covered shipments from
  Colombia, Brazil, Ethiopia, Guatemala and Rwanda, with shipment tracking and transparent prices.
  [DCN 2023](https://dailycoffeenews.com/2023/04/10/direct-trade-green-coffee-platform-algrano-makes-us-launch) ·
  [Fresh Cup](https://freshcup.com/online-green-coffee-sourcing/)
- **Cropster Hub.** A marketplace listing importer, exporter, mill and co-op lots, including
  coffee in transit and at origin. Search by flavour, score, variety, process and certification,
  with remote origin auctions. It acts as a virtual broker: sellers handle invoicing and shipping.
  [Fresh Cup](https://freshcup.com/online-green-coffee-sourcing/)
- **Beanstock.** Aggregates US-warehouse spot lists from importers, updated daily, with
  multi-importer sample requests. It covers spot stock only.
  [Fresh Cup](https://freshcup.com/online-green-coffee-sourcing/) ·
  [DCN 2016](https://dailycoffeenews.com/2016/06/02/green-coffee-aggregator-beanstock-makes-official-launch-following-scaa-success)
- **greensquare** (Australia). A roaster-side portal across many traders: spot and forward
  listings, sample and quote requests, digital contracts, drawdown tracking and consumption
  insights. Its founding survey found roasters juggling 6–8 traders in different formats.
  [BeanScene](https://www.beanscenemag.com.au/how-greensquare-is-a-digitalised-solution-for-roasting-businesses)

### 2. Trader back-office (importer/exporter operations)
- **CropConex.** Launched an Ethiopia-first marketplace in 2023, then a tiered-subscription suite
  for US importers and roasters: lot inventory and location, curated offers to segmented buyers,
  digital contracts, order and sample fulfilment, and sales analytics. Its pitch is replacing
  "checking in with spreadsheets".
  [Sprudge](https://sprudge.com/cropconex-unveils-new-suite-of-tools-for-coffee-traders-224294.html)

### 3. Origin / quality-lab software
- **Cropster Origin.** For producers and mills: lot inventory and processing, storage, sales and
  CRM-like workflows, a smartphone cupping app with custom forms, and sample traceability. The
  Professional plan covers up to 5 facilities. Pricing is a base monthly fee plus usage, with no
  public figures; Enterprise is quote-only.
  [Cropster Origin](https://www.cropster.com/products/origin/) ·
  [pricing](https://www.cropster.com/packages/origin-pricing/)
- **Cupping apps.** Catador CVA (iOS) follows the new SCA CVA scoresheet in Affective,
  Descriptive and Combined formats, with flights, locking, PDF share links and cloud sync. It is
  free with a $4.99/month or $49.99/year unlimited tier, and the listing doesn't state offline
  support. [App Store](https://apps.apple.com/app/id6447788662). Sustainable Harvest's older
  RITS cupping app is a free, offline training tool for co-ops.
  [SH](https://www.sustainableharvest.com/blog/introducing-sustainable-harvests-cupping-app)

### 4. Roastery operations (downstream of sourcing)
- **RoasterTools.** Green inventory is deducted automatically as you roast, alongside
  production planning, a wholesale portal, QuickBooks sync and green/profitability reports.
  Paid, with a free trial. [RoasterTools](https://roastertools.com/features/manage-inventory)
- Cropster Roast and Typica (free, open-source roasting logger,
  [typica.us](https://code.typica.us/neal/Typica/)) are also in this group.

### 5. Market intelligence and price data
- **StoneX Coffee Differential Insights.** Weekly FOB differential indications across major
  arabica and robusta origins, plus Brazil internal-price differentials. $200/month or
  $2,040/year. This is exactly the data our implied-price tool asks the user to type in.
  [StoneX](https://shop.stonex.com/products/coffee-differential-insight)
- **Specialty Coffee Transaction Guide (SCTG, Emory Goizueta).** Free. Anonymised FOB contract
  prices from more than 100k contracts (about 2 bn lb, 123 contributing companies), broken down by
  quality score, lot size and origin. 2024-edition medians: 80–83.9 points rose from $2.23 to
  $2.93/lb and 84+ from $3.43 to $4.18/lb between the 2018/19–20/21 and 2021/22–23/24 windows.
  License terms not stated in coverage; check before ingesting.
  [DCN 2025](https://dailycoffeenews.com/2025/02/18/the-2024-specialty-coffee-transaction-guide-is-here) ·
  [Sprudge](https://sprudge.com/tracking-coffee-prices-with-the-specialty-coffee-transaction-guide-283787.html)
- **Traceability apps** (iFinca, farmer connect/IBM "Thank My Farmer"): consumer-facing
  provenance and blockchain stories, not buyer workflow tools.
  [DCN](https://dailycoffeenews.com/2020/04/09/blockchain-backed-trading-platform-ifinca-promises-to-verify-farmgate-prices) ·
  [Startupticker](https://www.startupticker.ch/en/news/farmer-connect-and-ibm-launch-coffee-tracebility-app)

## What we see

1. **Everyone is a transaction or operations tool; nobody is the buyer's independent brain.**
   Marketplaces show *their own* listings, and back-office tools show *your own* inventory.
   None of them combines market context (C price, FX, weather, positioning, news) with the
   buyer's own supplier relationships, visits and cuppings in one place. That join is our
   opening.
2. **Price context is paywalled or annual.** Weekly differentials cost about $2k/year (StoneX).
   The free SCTG gives quality- and origin-level FOB benchmarks, but as an annual report.
   Turning SCTG plus our live C/FX feeds into "is this offer fair?" is a free, defensible feature.
3. **Supplier CRM is a gap for buyers.** Cropster Origin has CRM-like features for *producers*.
   greensquare and CropConex manage *traders'* catalogues. A neutral CRM for a buyer or broker
   (producers, mills, exporters, buyers, samples, follow-ups) across many counterparties is
   missing. The "6–8 traders in different formats" pain from greensquare's survey is the same pain.
4. **Cupping tools are siloed.** Cupping apps don't know the lot, supplier, price or visit. A
   CVA-compatible cupping log tied to a CRM supplier and an offer price is a natural join.
5. **Offline field use is under-served.** Only an old training app explicitly claims offline
   use. Farm visits during harvest (Z, Jan 4–17) need offline-first capture.

## Implications for us (→ proposals)

- **Sourcing CRM v1**: suppliers, contacts, interactions, samples, follow-ups. It is the shared
  core for every segment (Z's broker work, importers, roasters). → proposal
- **Field visit & cupping log**: offline-first, CVA-style scores, linked to CRM records. → proposal
- **Offer fairness check**: SCTG medians by quality tier/origin next to the live implied price,
  replacing a blank differential box with a sourced benchmark. → proposal (license check first)
- **Strategy draft**: position as "the independent sourcing workspace with built-in market
  intelligence", which avoids competing on marketplace liquidity. → proposal for `docs/STRATEGY.md`
- **Would improve quality (paid, not wired in):** StoneX weekly differentials ($200/mo).

## Open follow-ups for later research
- Pricing pages for Cropster Hub, CropConex and RoasterTools (not public or not checked).
- Algrano's current fee schedule and origin list for 2026.
- SCTG data format and license (CSV? CC?) before any ingestion.
- Free hosting options for a pre-trip deployment (Cloud Run free tier vs. alternatives).
