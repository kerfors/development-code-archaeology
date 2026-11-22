---
title: Publication decisions
description: "Rules and decisions for publishing development codes to Wikidata with property P15001, and the outcome per batch."
---

# Publication decisions

The approach is conservative: nothing is published that depends on an assumption. Each open question ends in
hold, with the reason recorded. A held code stays an alias and remains usable for search.

## Rules

- **Which codes.** Only codes confirmed by a person in review, accepted by the evidence rule and used in search.
- **Which item.** The item of the level the code names: active moiety, salt (only where the evidence names
  the salt) or fixed combination. Items are found by UNII.
- **Which reference.** A ClinicalTrials.gov record (NCT ID) with the assigning company as lead sponsor;
  otherwise NCI Thesaurus if it is a source; otherwise not published. PubChem and Wikipedia are not used as
  references.
  For codes older than the trial registries (the Hässle codes): a PubMed record whose title or abstract
  contains the code, checked against the record text; MeSH or NCI Thesaurus only where no PubMed record names
  the code. An aggregated synonym list is not a reference, also when it is a PubMed record (LactMed).
- **Which company.** Qualifier P1027 "conferred by", the company that assigned the code, only where a
  reference shows it. For the Hässle codes that is a PubMed record with a Hässle or Astra/AstraZeneca Mölndal
  affiliation; otherwise the statement goes without a company (D14).

## Outcome per batch

{{table:outcome}}

Query the published statements live:
[all P15001 statements in the Wikidata Query Service](https://query.wikidata.org/#SELECT%20%3Fitem%20%3FitemLabel%20%3Fcode%20%3FcompanyLabel%20WHERE%20%7B%0A%20%20%3Fitem%20p%3AP15001%20%3Fs%20.%20%3Fs%20ps%3AP15001%20%3Fcode%20.%0A%20%20OPTIONAL%20%7B%20%3Fs%20pq%3AP1027%20%3Fcompany%20%7D%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%2Cmul%22%20%7D%0A%7D%20ORDER%20BY%20%3FitemLabel).

## Decisions

Read from [`wikidata/README.md`](repo:wikidata/README.md), where each decision is recorded first.

{{table:decisions}}
