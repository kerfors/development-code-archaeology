---
title: "Development codes on Wikidata: why, what was done, what I learned"
description: "A new Wikidata property for development codes, the first 41 referenced statements, and why most of the hard questions were about identity."
written: 2026-11-08
covers: October – November 2026
number: 3
batches: [top_sellers_fy2025_batch_20261107_1520.csv, fda_novel_2025_batch_20261107_1901.csv]
---

# Development codes on Wikidata

The second question from the [first field note](00-where-it-started.html): can an open data community
hold development codes?

## Wikidata

Wikidata is the open knowledge graph of the Wikimedia projects. Anyone can read it, query it and edit it, and
every statement can carry a reference. It is Linked Data in practice: each thing has an identifier, and
statements link things to other things. As a Linked Data and open data advocate I have followed Wikidata for
years, used it, and made some minor updates myself.

## Why

On Wikidata, development codes were aliases. An alias has no reference, no company, and no way to say it is
wrong without deleting it. Some aliases repeated errors of the sources they came from. On abatacept, the aliases
RG-2077 and CTLA4-IgG4m name a different construct, an IgG4 fusion protein in two NIAID trials. On ocrelizumab,
the alias PR-070769 is a typo of the Genentech code PRO70769; NCI Thesaurus has the same typo.

None of the existing properties fitted. So I proposed a new one, and in October 2026 the community created
[P15001 "development code"](https://www.wikidata.org/wiki/Property:P15001)
([proposal](https://www.wikidata.org/wiki/Wikidata:Property_proposal/development_code)). A code is now a
statement, with the company that assigned it ("conferred by") and a reference.

## What was done

The rules are conservative: nothing is published that depends on an assumption.

- **Which codes.** Only codes I confirmed in review, accepted by the evidence rule and used in search.
- **Which item.** The item of the level the code names: active moiety, salt (only where the evidence names the
  salt) or fixed combination. Items are found by UNII.
- **Which reference.** A ClinicalTrials.gov record with the assigning company as lead sponsor; otherwise NCI
  Thesaurus if it is a source; otherwise not published. PubChem and Wikipedia are not used as references.

On 7 November 2026 I sent two batches:

{{table:outcome}}

Every held code has a recorded reason, decisions D0 to D13 on the [Publication decisions](../decisions.html)
page. A held code stays an alias and is still used for search.



## See it live

[This query](https://query.wikidata.org/#%23%20Development%20codes%20on%20Wikidata%20%28P15001%29%2C%20with%20company%20and%20reference%0ASELECT%20%3Fitem%20%3FitemLabel%20%3Fcode%20%3FcompanyLabel%20%3Fnct_id%20%3Fncit_id%20WHERE%20%7B%0A%20%20%3Fitem%20p%3AP15001%20%3Fs%20.%20%3Fs%20ps%3AP15001%20%3Fcode%20.%0A%20%20OPTIONAL%20%7B%20%3Fs%20pq%3AP1027%20%3Fcompany%20%7D%0A%20%20OPTIONAL%20%7B%20%3Fs%20prov%3AwasDerivedFrom%20%3Fr%20.%0A%20%20%20%20%20%20%20%20%20%20%20%20%20OPTIONAL%20%7B%20%3Fr%20pr%3AP3098%20%3Fnct_id%20%7D%20OPTIONAL%20%7B%20%3Fr%20pr%3AP1748%20%3Fncit_id%20%7D%20%7D%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%2Cmul%22%20%7D%0A%7D%0AORDER%20BY%20%3FitemLabel%20%3Fcode) lists every development code on Wikidata, with the company that assigned it and the
reference: a ClinicalTrials.gov NCT ID or an NCI Thesaurus code. On 8 November 2026 it returned 49 statements
on 39 items: the 41 from the two batches, my four test statements from October, and four examples added by
the property creator. As others add codes, the list will grow beyond this work.

## What I learned

1. **A code names a level.** Active moiety (AZD7986), salt (DS-6051b, of which DS-6051a is the free base),
   combination (LNZ101: aceclidine + brimonidine), or a development programme (Novo Nordisk's NN9535).
   Wikidata has items for the first three. ISO IDMP has no structural place for development codes, and no
   programme level.
2. **A company is another case of what to identify.** "Conferred by" needs the company that assigned the code
   as one thing, across subsidiaries, joint ventures, mergers and renames, and company items do not always carry
   the names the registry uses. The same question as for the drug: what exactly is it we identify?
   Details: [Identity findings](../identity.html).
3. **Most holds are about identity, not about the code.** In 27 of the 31 holds the code is confirmed; what is
   open is which item, which company, which level, or which spelling.
4. **Linked Data shows these details early.** Each of them had to be decided before a statement could be made.
   Other approaches leave them to be handled in software later, or never.

## Why it matters

| For | Value |
|-----|-------|
| Open data | P15001 makes a code verifiable (reference), attributable (conferred by) and correctable. An alias is none of these. |
| Master data and ISO IDMP | Development codes behave as identifiers with an assigner, a time span and a level. That is evidence for giving them a place in the model, and for a level above Product Family (the "Product Clan") that covers the whole R&D lifecycle. |
| Method | An LLM writes the code and helps find sources; the pipeline itself is deterministic, every decision is in a file, and a person confirms what is published. |

## Open questions

- Who is "the company" across subsidiaries, joint ventures and acquisitions, and where should that be
  resolved: in Wikidata, in the registry, or in each sponsor's master data?
- Should registries record the development code as a typed identifier of the intervention, with its assigner?
- How should a development programme (one moiety, one formulation, one indication) be represented, when
  neither Wikidata nor IDMP has the level?
