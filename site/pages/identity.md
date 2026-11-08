---
title: Identity findings
description: "Company and level identity questions met when publishing development codes to Wikidata."
---

# Identity findings

Publishing a code with "conferred by" requires knowing which company assigned it, and finding that company
in the trial registry and on Wikidata. These findings are recorded, not resolved: who "the company" is across
subsidiaries, joint ventures, mergers and renames is a general question. Source file:
[`wikidata/company_identity_findings.md`](repo:wikidata/company_identity_findings.md).

## Registry names that are not the company item

| Code | Company item | Lead sponsor in the registry |
|------|--------------|------------------------------|
| LEE011, AIN457, LOU064 | Novartis | Novartis Pharmaceuticals (2,717 trials as lead) rather than Novartis (714) |
| RG6013, RG7716 | Hoffmann-La Roche | Genentech, Inc., a Roche company with its own item |
| JNJ54767414 | Johnson & Johnson | Janssen Research & Development, LLC |
| GSK1349572 | GSK | ViiV Healthcare, a joint venture, for most trials |
| INS1007, VX548 | Insmed; Vertex Pharmaceuticals | … Incorporated |
| MTP131, DCC3014 | Stealth BioTherapeutics (United States); Deciphera Pharmaceuticals (United States) | … Inc.; … LLC |

## Prefixes that outlive their company

| Codes | Prefix | Trials today |
|-------|--------|--------------|
| GW685698, GW642444 | GW (Glaxo Wellcome) | GlaxoSmithKline |
| ABT494, ABT-627 | ABT (Abbott) | AbbVie; Novartis |
| PD-0325901 | PD (Parke-Davis) | Pfizer; SpringWorks |
| CGP48933 | CGP (Ciba-Geigy) | Novartis |

## Successor sponsors

The registry holds the record as it is today. ONC201 (Oncoceutics) is in Jazz Pharmaceuticals' trials,
NT-814 (NeRRe) in Bayer's, CNSA-001 (Censa) in PTC Therapeutics'. Dapagliflozin's BMS-512148 trials from 2005
have AstraZeneca as lead sponsor; whether the records were transferred is not visible.

## Company items on Wikidata

Several smaller companies exist only as items labelled "&lt;name&gt; (&lt;country&gt;)", described as
"company in &lt;city&gt;", apparently imported from an organisation register. Some companies have no item
(Milestone Pharmaceuticals, Censa Pharmaceuticals, AnHeart Therapeutics). One item carries another company's
current label: MedImmune is now labelled "AstraZeneca (United States)", so a "conferred by" pointing to it
displays the later name.

## Codes for programmes, not substances

Novo Nordisk's NN codes for semaglutide each follow one formulation × indication programme: NN9535
subcutaneous for type 2 diabetes, NN9924 tablets, NN9536 obesity. The compound code is NNC0113-0217. The level
sits between active moiety and product. Neither Wikidata nor ISO IDMP has it.

## Change log

- 2026-11-08: page created, from findings recorded 2026-11-07.
