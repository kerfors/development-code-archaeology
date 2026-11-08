---
title: "Two 2025 collections: harvest, review, Wikidata"
description: "Development codes for the 2025 FDA novel approvals and for big sellers: how many trials only the codes find, what was learned, and the first referenced codes on Wikidata."
date: 2026-11-08
covers: October – November 2026
order: 1
data: ta_20261016
batches: [top_sellers_fy2025_batch_20261107_1520.csv, fda_novel_2025_batch_20261107_1901.csv]
---

# Trials registered under a development code

Before a drug has an INN, it has a development code: AZD0914, BI 1015550, MK-3475. Many trials are
registered under the code, and some stay so. A ClinicalTrials.gov search on the INN alone does not find them.

This post covers October–November 2026, a follow-up of the [December 2025 holiday project](2026-11-08-before-the-repository.html):
harvest development codes from named sources, review them, count the trials they recover, and publish the
reviewed codes to Wikidata with references.

{{stats:2025}}

## One substance, three names

Zoliflodacin (Nuzolvence, approved 2025) was AZD0914 at AstraZeneca and ETX0914 at Entasis Therapeutics.
NIAID's 2018 news release says it in one line: "formerly known as ETX0914 and AZD0914".
The trials do not say it in the fields a search uses.

{{diagram:zoliflodacin}}

<p class="caption">AACT snapshot 2026-10-16. On Wikidata, neither code could be published under the rules:
AZD0914 has no trial with AstraZeneca as lead sponsor naming the code, and ETX0914 has web evidence only.
Both stay held, with the reason recorded.</p>

## What was done

| When | What | Outcome |
|------|------|---------|
| October 2026 | Code harvest from named sources with a checkable evidence rule; a second collection (top sellers); one shared matching rule | 184 candidates for 30 moieties; human review; 631 drug–trial pairs found only via a code |
| October 2026 | Wikidata property proposal; [P15001 "development code"](https://www.wikidata.org/wiki/Property:P15001) created 25 October | Codes become statements with company and reference, not only aliases |
| November 2026 | The December collection through the same harvest and review; both collections published under one set of documented decisions (D0–D13) | 41 statements published; 31 held with a reason; 23 without an acceptable reference |

## How

{{diagram:pipeline}}

No code enters without a source. A code is accepted when two independent lines of evidence agree
(sources, web publishers, registry trials). A person reviews each candidate's class. Trials are searched
with one matching rule for the INN and the accepted codes. Details: [Method](../method.html).

## Results

Drug–trial pairs found only via a code: the INN is not in the registered intervention name. For
165 of the 197 such pairs in the FDA collection, the INN is in neither trial title either.
26 of the 30 products have such trials.

<figure markdown="1">
<figcaption>FDA novel approvals 2025, drug–trial pairs per product, sorted by share found only via a code.</figcaption>

{{chart:per_drug fda_novel_2025}}

</figure>

<figure markdown="1">
<figcaption>FDA novel approvals 2025: share found only via a code, by phase.</figcaption>

{{chart:by_phase fda_novel_2025}}

</figure>

<figure markdown="1">
<figcaption>Top sellers FY2025: share found only via a code, by trial start year.</figcaption>

{{chart:by_start top_sellers_fy2025}}

</figure>

The pattern: the early and the old history of a drug is under its codes. For recent approvals that is
almost half of Phase 1. For big sellers with large INN-registered programmes the share is small overall, but it
is a fifth to a quarter of their trials started before 2015.

## What was learned

1. **AI can find codes; only sources can prove them.** In December, AI discovery produced plausible codes
   that no source had. Since October, every code has a named source, and a code found on the web cites the URL.
2. **No source is complete, and sources copy each other.** Some current codes exist only in the registry
   (tirzepatide LY3298176). Some trial records, NCI-sponsored and academic, appear to carry NCI Thesaurus
   synonym lists as other names, so for those codes the registry is not an independent witness.
3. **A code names a level.** Active moiety (AZD7986), salt (DS-6051b, of which DS-6051a is the free base),
   combination (LNZ101: aceclidine + brimonidine), or a development programme (Novo Nordisk's NN9535).
   Wikidata has items for the first three. ISO IDMP has no structural place for development codes, and no
   programme level.
4. **The hard part is not the drug, it is the company.** "Who assigned this code" meets subsidiaries,
   mergers, renames and company items that do not carry the names the registry uses.
   Details: [Identity findings](../identity.html).
5. **Linked Data shows these details early.** Each of them had to be decided before a statement could be
   made. Other approaches leave them to be handled in software later, or never.

## Why it matters

| For | Value |
|-----|-------|
| Trial search and evidence synthesis | Early-phase and older trials of a drug are found only with its codes. INN-only searches undercount them, most for recently approved drugs. |
| Master data and ISO IDMP | Development codes behave as identifiers with an assigner, a time span and a level. That is evidence for giving them a place in the model, and for a level above Product Family (the "Product Clan") that covers the whole R&D lifecycle. |
| Open data | P15001 makes a code verifiable (reference), attributable (conferred by) and correctable. An alias is none of these. |
| Method | An LLM writes the code and helps find sources; the pipeline itself is deterministic, every decision is in a file, and a person confirms what is published. |

## Open questions

- Who is "the company" across subsidiaries, joint ventures and acquisitions, and where should that be
  resolved: in Wikidata, in the registry, or in each sponsor's master data?
- Should registries record the development code as a typed identifier of the intervention, with its assigner?
- How should a development programme (one moiety, one formulation, one indication) be represented, when
  neither Wikidata nor IDMP has the level?

## Related work

Chris Southan, a friend and former colleague, and I have addressed this from two different perspectives:
his from chemistry and public compound databases, mine from clinical trials, data standards and identity.
Both meet the same issue: the names of a substance are spread over many sources and not linked.

- Southan C, Pawson AJ, Sharman JL, Benson HE, Faccenda E. [Resolving cryptic needles to molecular structures: the GtoPdb experience](https://www.slideshare.net/slideshow/southan-needles-acs/51539822).
  ACS CINF, 2015. Code chains across mergers (MK-8931, SCH 900931, verubecestat), format variants, and a
  proposal for a standard identifier format.
- Rujan R-M, Amaral M, Southan C, Dunlop I. [Resolving code names to structures from the medicinal chemistry literature: not as FAIR as it should be](https://cisrg.shef.ac.uk/shef2023/?p=771).
  Medicines Discovery Catapult, 2023 ([slides](https://cisrg.shef.ac.uk/shef2023/wp-content/uploads/2023/10/Resolving_Code_Names_Rujan.pdf)).
  Code mining from J. Med. Chem. abstracts, false positives, and recommendations for code formats.

## Data for this post

Trial search: AACT snapshot 2026-10-16, runs 20261016_1010 (FDA novel approvals 2025) and 20261016_1046
(top sellers FY2025), reduced to [`site/data/ta_20261016/`](repo:site/data/ta_20261016). Wikidata: batches
sent 2026-11-07 ([`wikidata/batches/`](repo:wikidata/batches)). The figures in this post do not change
when later runs come.
