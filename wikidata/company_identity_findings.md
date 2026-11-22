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

## fda_novel_2025 (2026-11-07): sponsor names that D6 does not match

D6 is applied as written; these are recorded, not fixed. Sponsor names from ClinicalTrials.gov, 2026-11-07.

| Code | Company item | Lead sponsor name | Why D6 does not match |
|------|--------------|-------------------|-----------------------|
| INS1007 | Insmed (Q30281842) | Insmed Incorporated | "Incorporated" is not in the legal-suffix list |
| VX548 | Vertex Pharmaceuticals (Q2744099) | Vertex Pharmaceuticals Incorporated | as above |
| AVX012 | Avizorex Pharma (Q30268756) | Avizorex Pharma, S.L. | "S.L." is not in the legal-suffix list |
| MTP131 | Stealth BioTherapeutics (United States) (Q30269327) | Stealth BioTherapeutics Inc. | item label carries a country |
| DCC3014 | Deciphera Pharmaceuticals (United States) (Q104480282) | Deciphera Pharmaceuticals, LLC | as above |
| LOU064 | Novartis (Q507154) | Novartis Pharmaceuticals | as for the top_sellers Novartis codes |

Several smaller companies exist on Wikidata only as items labelled "<name> (<country>)", described as
"company in <city>, <country>"; they look like imports from an organisation register. Oncoceutics, NeRRe
Therapeutics and Principia Biopharma are of this kind as well.

Companies without an item found: Milestone Pharmaceuticals (MSP2017), Censa Pharmaceuticals (CNSA001), AnHeart
Therapeutics (AB106), KaNDy Therapeutics.

Successor sponsors (D1): ONC201 (Oncoceutics code; trials now under Jazz Pharmaceuticals), NT814 (NeRRe code;
trials under Bayer), CNSA001 (Censa code; trials under PTC Therapeutics), AZD0914 (AstraZeneca code; trials under
NIAID and Entasis).

## hassle_h_inns (2026-11-22): an older company line

Hässle AB has an item (Q105106991): instance of business, country Sweden, one sitelink (sv.wikipedia
"Hässle AB"), nothing more. Used as P1027 on 3 statements (D14). Q10531804 "Hässle" is a manor house in
Enköping, not the company.

One company line under three names: Hässle, Astra Hässle and AstraZeneca R&D Mölndal (same site, same
numbering). A Mölndal affiliation counts for the line; Astra in Södertälje or Lund does not (zimelidine H 102/09
has an Astra Läkemedel, Södertälje affiliation). The site decides, not the name.

GSRS ACTIVE MOIETY is not the regulatory moiety for prodrugs and activated drugs: for ximelagatran it gives
melagatran, for omeprazole and esomeprazole the acid-activated sulfenamide. The collection uses the INN's own
GSRS record (`collections/README.md`, hassle_h_inns.csv).

Two items carry felodipine's UNII OL961R6O2C: Q420644 (with P2275, 23 sitelinks) and Q72478142 (neither). The
statement went on Q420644 by the lookup rule; Q72478142 is not reported on its talk page yet.
