---
title: "What the codes find in the trial registry"
description: "How many trials of the 2025 FDA novel approvals and of big sellers can only be found by a development code, and where in a drug's history they are."
written: 2026-11-08
covers: October 2026
number: 2
data: ta_20261016
---

# What the codes find in the trial registry

With the codes harvested and reviewed ([previous note](01-harvesting-codes.html)), I searched
ClinicalTrials.gov, through AACT, with the INN and with the accepted codes, using one matching rule for both.
A trial counts as found only via a code when the INN is not in its registered intervention name.

{{stats:trials_2025}}

## One substance, three names

Zoliflodacin (Nuzolvence, approved 2025) was AZD0914 at AstraZeneca and ETX0914 at Entasis Therapeutics.
NIAID's 2018 news release says it in one line: "formerly known as ETX0914 and AZD0914". The trials do not say
it in the fields a search uses.

{{diagram:zoliflodacin}}

## Per drug

For 165 of the 197 drug–trial pairs found only via a code in the FDA collection, the INN is in neither trial
title either. 26 of the 30 products have such trials.

<figure markdown="1">
<figcaption>FDA novel approvals 2025, drug–trial pairs per product, sorted by share found only via a code.</figcaption>

{{chart:per_drug fda_novel_2025}}

</figure>

## Where in a drug's history

<figure markdown="1">
<figcaption>FDA novel approvals 2025: share found only via a code, by phase.</figcaption>

{{chart:by_phase fda_novel_2025}}

</figure>

<figure markdown="1">
<figcaption>Top sellers FY2025: share found only via a code, by trial start year.</figcaption>

{{chart:by_start top_sellers_fy2025}}

</figure>

The early and the old history of a drug is under its codes. For recent approvals that is almost half of
Phase 1. For big sellers with large INN-registered programmes the share is small overall, but it is a fifth to
a quarter of their trials started before 2015.

## Why it matters

Anyone who searches trials by drug name, for a systematic review, a safety question, real-world evidence, or
a competitor overview, misses the early and the older trials unless the codes are in the search. Most for
recently approved drugs, where the INN came late.

## Data for this note

AACT snapshot 2026-10-16, runs 20261016_1010 (FDA novel approvals 2025) and 20261016_1046 (top sellers
FY2025), reduced to [`site/data/ta_20261016/`](repo:site/data/ta_20261016). The FDA collection was searched with
the December codes; the reviewed harvest codes differ in a few places. The figures in this note do not change
when later runs come.

Next: [Development codes on Wikidata](03-codes-on-wikidata.html).
