# How each segment sources green coffee — and the shared core

Date: 2026-10-16 · Topic rotation: specialty-coffee domain knowledge (input for `docs/STRATEGY.md`, proposal #11)

## Question

CLAUDE.md asks us to find the **common core** of sourcing work across specialty roasters (small → enterprise),
independent importers/exporters and cafes, then build segment layers on top. What does each segment
actually do when it sources, and where do the workflows overlap?

## What each segment does (paraphrased from sources below)

### Small / growing roasters
- Buy **spot from importers' warehouses** in small increments, typically holding about **2–3 months** of
  inventory; overbuying ties up cash and ages stock (Royal Coffee via PDG; Atlas/Café Imports via Fresh Cup).
- Rarely hedge — it needs capital and expertise. Importers can aggregate small clients' hedges, and give
  more price flexibility to roasters who **repeat-buy from the same producer** (Balzac Brothers via PDG).
- Price shocks hit spot buyers immediately (C hit record highs Feb 2025; US tariffs of 10–46 % on some
  origins in 2025). Coping tactics: watch origin-level prices and harvest timing, **switch to origins with
  similar flavour profiles** when one gets expensive, build importer relationships (PDG 2025).
- An academic interview study of small roasters found **company strategy** (business model) drives
  procurement more than size or age; size mainly affects whether they forward-contract and which
  certifications they buy (Rosenbaum, UMN 2016).

### Established / larger roasters
- Mostly **forward** (one head of coffee at a large specialty roaster reports ~99 % forward), because spot
  price and availability became volatile. Forecasting is done **per blend component in spreadsheets**
  from historical usage; positions are kept lean ("usually short") (Roast Magazine roundtable).
- Repeat relationships with the same producers; **cup every sample and send feedback** — many roasters
  skip feedback and producers are left guessing (Roast Magazine).
- Contracts are typically "subject to approval of sample" — no approval, no sale (Fresh Cup Supply Chain 101).
- **EU-facing buyers:** EUDR (as amended by Reg. 2025/2650) applies from **30 Dec 2026** for large/medium
  operators and **30 Jun 2027** for micro/small. Importing roasters need plot geolocation, a due-diligence
  statement in TRACES and a per-supplier risk assessment; downstream buyers keep the upstream DDS reference
  for 5 years (TraceX summary — verify against the official text; not legal advice).

### Importers (and exporters)
- Coordinate the whole chain: issue the contract to producer/exporter, **approve pre-shipment samples**,
  pay invoice and freight, hold the bill of lading, insure in transit, **cup the landed sample**, warehouse
  and deliver (Fresh Cup Supply Chain 101).
- Carry **spot position risk** — a coffee that sits unsold on the offer list "dies"; they bring in spot lots
  they expect customers to forward-book later, and publish daily offer lists (Fresh Cup; Café Imports).
- Tracking contracts and **release schedules** is a stated headache for roasters and importers — missed
  releases cost fees (Atlas via Fresh Cup).
- Exporters/co-ops cup their own lots, send pre-ship samples, invoice ~10 days after shipment (Fresh Cup).

### Cafes
- Most cafes buy **roasted** coffee; the sourcing work is choosing and managing **roaster partners**.
  Multi-roaster cafes rotate 4–5 roasters, place **standing weekly orders** so roasters can forecast,
  keep orders small for freshness, and find >5 roasters hard to manage (Fresh Cup, Cognoscenti case, 2014).
- A cafe that roasts its own coffee is, for sourcing purposes, a small roaster.

## The shared core (where the workflows overlap)

| Job | Small roaster | Large roaster | Importer / exporter | Cafe | Z on the trip |
|---|---|---|---|---|---|
| Find & vet suppliers (producer, mill, importer, roaster) | ✔ | ✔ | ✔ | ✔ (roasters) | ✔ |
| Samples: request → cup → decide → **feedback** | ✔ | ✔ | ✔ (pre-ship + landed) | light | ✔ |
| Know a fair price (C + differential + FX + quality) | ✔ | ✔ | ✔ | — | ✔ |
| Relationship history: who, what was bought, at what price | ✔ | ✔ | ✔ | ✔ | ✔ |
| Track commitments: contracts, releases, follow-ups | light | ✔ | ✔ | standing orders | follow-ups |
| Watch market & origin risk (price, harvest, weather, tariffs) | ✔ | ✔ | ✔ | light | ✔ |
| Forecast need / position | light | ✔ | ✔ | — | — |
| Compliance / traceability (EUDR, certs) | if EU | ✔ | ✔ | — | ask producers |

**The core is: supplier records + sample/cupping log + price context + follow-ups, with market/origin
monitoring around it.** That is exactly what proposals #8 (Sourcing CRM), #9 (Offer check) and #10 (Field
mode) cover — good evidence they are the right first bets, and that they serve every segment, not just Z.
Contract/release tracking and forecasting are the first **segment layer** (larger roasters, importers).
Cafes are a weak fit for green sourcing; they're a later segment (roaster-partner management).

## Implications for us

1. **First target segment: small-to-mid specialty roasters (and Z as broker/importer-in-waiting).** They
   share the full core, have the least tooling (spreadsheets, importer offer lists), and are most exposed to
   price shocks. Feed this into the STRATEGY.md draft (#11).
2. **Sample feedback loop is an underserved, differentiating feature.** Roasters say feedback to producers
   is often skipped; a one-tap "send feedback" from a cupping record (#10) to the supplier record (#8) is
   cheap to build and valued on both sides.
3. **"Substitute origin" view.** When one origin's implied price jumps, show origins with similar cup
   profile and harvest timing that are cheaper now — joins our existing price/FX/origin data. Candidate
   proposal once the proposal queue has room.
4. **Contract & release tracker** (dates, volumes, release deadlines) is the natural next layer after the
   CRM for larger roasters/importers. Keep for later.
5. **EUDR fields on the supplier/lot record** (plot geolocation, DDS reference) would make the CRM useful
   to EU buyers from 30 Dec 2026 / 30 Jun 2027 — and are worth asking Costa Rican producers about on the
   trip. Small schema addition to #8 rather than a separate feature.
6. Paid data that would improve quality (never wired in): importer offer-list feeds, StoneX differentials.

## Sources

- Perfect Daily Grind, "How smaller coffee roasters can mitigate risk" (2025-04): https://perfectdailygrind.com/2025/04/how-smaller-coffee-roasters-can-mitigate-risk/
- Roast Magazine, "Roaster Roundtable — Rethinking coffee sourcing": https://www.roastmagazine.com/stories/rethinking-coffee-sourcing
- Fresh Cup, "Supply Chain 101": https://freshcup.com/supply-chain-101/
- Fresh Cup, "Big time changes: redefining spot coffee": https://freshcup.com/the-new-spot
- Fresh Cup, "The multi-roaster line-up": https://freshcup.com/the-multi-roaster-line-up/
- Café Imports, "Working with us": https://www.cafeimports.com/working-with-us
- Rosenbaum (2016), "Wake up and smell the coffee: procurement decisions at small specialty coffee roasters", UMN: https://conservancy.umn.edu/items/171ab2c4-ecaf-41a5-9742-5203c8c6cb0a
- TraceX, "EUDR for coffee roasters": https://tracextech.com/eudr-coffee-roasters/
