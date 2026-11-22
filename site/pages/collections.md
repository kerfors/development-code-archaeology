---
title: Collections
description: "The drug collections traced so far, and where each one stands."
---

# Collections

A collection is a list of marketed products, or later of pipeline compounds, traced through their
development codes. Provenance of each collection and its codes:
[`collections/README.md`](repo:collections/README.md).

| Collection | Content | Search unit | Codes | Trial search | Wikidata |
|------------|---------|-------------|-------|--------------|----------|
| `fda_novel_2025` | FDA novel drug approvals 2025, 30 products | product | December 2025 discovery, verified; harvested and reviewed 2026-11-07 (54 confirmed, 7 held) | 2026-10-16, December codes | batch 2026-11-07 |
| `top_sellers_fy2025` | Top three selling medicines of 12 companies with FY2025 revenue USD 41–65 B, 30 active moieties | active moiety | Harvested and reviewed October 2026 | 2026-10-16 | batch 2026-11-07 |
| `hassle_h_inns` | Substances with an INN that carry an H code from Hässle, Mölndal: 17 INNs, 18 codes | active moiety | Harvested and reviewed November 2026 (29 review rows confirmed, 1 open) | not counted: a historical collection | batch 2026-11-22 |

Beside `hassle_h_inns` there is a historical list of every H code found, 138 codes with sources, earliest date
and status ([`collections/hassle_h_codes_all.csv`](repo:collections/hassle_h_codes_all.csv);
[field note 4](notes/04-hassle-what-we-learned.html)).

## Planned

- FDA novel drug approvals 2026, and top sellers FY2026, when the year's summaries are out.
- A company pipeline (AstraZeneca). Many pipeline compounds have no INN yet, so this collection will start
  from the code rather than the INN.

## Change log

- 2026-11-08: page created.
- 2026-11-22: Hässle INN codes and the historical H-code list.
