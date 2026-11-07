# Identity findings: companies and programmes

Observed while mapping development codes to the company that assigned them (P1027 "conferred by") and
picking a trial with that company as lead sponsor (`README.md`, decisions D1–D6). Recorded, not resolved:
who "the company" is across subsidiaries, joint ventures, mergers and renames is a general question, not one
this repository can settle. Under D6 a sponsor name counts only if it matches the label or an alias of the
company's Wikidata item. Sources: AACT snapshot 2026-11-07 (lead sponsors), Wikidata 2026-11-07.

## Registry names that are not the company item

| Code | Assigning company (item) | Lead sponsor names in AACT | Observation |
|------|--------------------------|----------------------------|-------------|
| LEE011, AHU377, AIN457, AIN457A, VAL489 | Novartis (Q507154) | Novartis Pharmaceuticals; Novartis | Most Novartis trials are registered under "Novartis Pharmaceuticals" (2,717 as lead) rather than "Novartis" (714). Neither the label nor the aliases of Q507154 include "Novartis Pharmaceuticals". |
| RG6013, RG7716 | Hoffmann-La Roche (Q212646) | Hoffmann-La Roche; Genentech, Inc. | Genentech is a Roche company with its own item (Q899140). |
| JNJ54767414 | Johnson & Johnson (Q333718) | Janssen Research & Development, LLC | The JNJ prefix names the parent; trials are by Janssen R&D, an alias of Janssen Pharmaceutica (Q903523). |
| GSK1349572 | GSK (Q212322) | ViiV Healthcare; GlaxoSmithKline | ViiV Healthcare (Q7929051), a joint venture, is lead sponsor of most trials. |
| CNTO1959, CNTO1275 | Centocor (Q1053653) | Centocor, Inc.; Centocor Research & Development, Inc.; Centocor Ortho Biotech Services, L.L.C. | Only "Centocor, Inc." matches an alias. |

## Items whose current label is another company

| Company | Item | Current label | Alias |
|---------|------|---------------|-------|
| MedImmune | Q1335294 | AstraZeneca (United States) | MedImmune |
| Centocor | Q1053653 | Janssen Biotech | Centocor |

A P1027 qualifier pointing to these items displays the current label, not the name of the company that
assigned the code.

## Prefixes that outlive their company

| Codes | Prefix | Observation |
|-------|--------|-------------|
| GW685698, GW685698X, GW642444 | GW (Glaxo Wellcome) | Trials are by GlaxoSmithKline; whether GW numbers were still assigned after the merger is not known here. |
| ABT494 | ABT (Abbott) | Trials are by AbbVie. |
| GR109714X | GR (Glaxo) | No AACT lead sponsor named Glaxo. |
| CGP48933 | CGP (Ciba-Geigy) | Not an AACT lead sponsor; valsartan trials are Novartis's. |

## Companies without an item, or without trials

| Codes | Company | Observation |
|-------|---------|-------------|
| FX1006, FX1006A | FoldRx | No Wikidata item; not an AACT lead sponsor. Tafamidis trials are Pfizer's. |
| BCH189 | BioChem Pharma | No Wikidata item; not an AACT lead sponsor. |
| MDX1106 | Medarex (Q6805152) | Not an AACT lead sponsor. |

## Sponsor recorded today, not at the start

BMS512148 (dapagliflozin): all 24 company trials have AstraZeneca as lead sponsor, including trials that
started in 2005. Bristol-Myers Squibb is lead sponsor of none. AACT holds the current record; whether the
records were transferred is not visible there.

## Codes for programmes, not substances

Novo Nordisk's NN codes for semaglutide appear as prefixes of its study IDs (AACT `id_information`), and each
follows one formulation × indication programme. Trials with Novo Nordisk A/S as lead sponsor, AACT 2026-11-07:

| Code | Trials | Start dates | Programme, from trial titles |
|------|--------|-------------|------------------------------|
| NN9535 | 70 | 2007–2026 | subcutaneous semaglutide, type 2 diabetes; the 2007 trial uses NN9535 as the drug name |
| NN9924 | 69 | 2009–2027 | semaglutide tablets, type 2 diabetes and cardiovascular |
| NN9536 | 43 | 2015–2026 | obesity, including Wegovy post-marketing studies |
| NN9931 | 5 | 2016–2026 | liver: NASH and fibrosis |
| NN9932 | 6 | 2021–2026 | semaglutide tablets, obesity |

The compound code is NNC0113-0217. The programme level sits between active moiety and product (one moiety,
several programmes; two of them tablets for different indications). Wikidata has no items for it, and ISO IDMP
has no concept for it either. Held under D8.
