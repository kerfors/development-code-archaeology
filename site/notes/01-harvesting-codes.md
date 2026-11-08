---
title: "Harvesting development codes from named sources"
description: "Instead of asking an AI to remember codes: collect them where they are written down, with an evidence rule I can check and a review where a person decides."
written: 2026-11-08
covers: October – November 2026
number: 1
---

# Harvesting development codes from named sources

The [first field note](00-where-it-started.html) ended with two questions. This note is about the first:
can development codes be harvested programmatically, from named sources?

In December I asked an AI to find the codes, and then checked them by hand. That worked, but it does not
scale, and the AI produced codes that no source had. So in October I turned it around: collect candidate
codes from sources that can be named and queried, and let the AI help write the code and look for web
sources, not remember the answer.

{{diagram:pipeline}}

## Sources

| Source | Gives | Known weakness |
|--------|-------|----------------|
| NCI Thesaurus | Curated synonyms, tagged as drug study codes | Merges biosimilar codes into the originator; typos (PR070769 for PRO70769) |
| PubChem synonyms | Depositor synonyms | Vendor numbers, depositor typos (GSK685968 next to GSK685698) |
| ClinicalTrials.gov (AACT) other names | What sponsors registered | Codes of combination partners and other products in the same record |
| ClinicalTrials.gov intervention names | Codes with a suffix (ONO-4538HSC) | Other formulations |
| Web, AI-assisted | Originator, partner and combination codes | Every code must cite the URL where it was seen |

## A rule I can check, and a person who decides

I am not a domain expert for judging individual development codes. So the first filter is a rule anyone can
check: a code is accepted when two independent lines of evidence agree, a source, a distinct web publisher, or
trials in the registry. Codes found only in PubChem, with no trials, are set aside.

Then each candidate gets a class in review: current code, legacy code, partner code, or one of the classes
that are not searched: another product, another drug, a biosimilar, a typo, not a code. The AI proposes a
class; it is marked as proposed until I confirm it. Where the rule and the review disagree, the row goes to an
exception list. Where a question stays open, the code is held, and the reason is written down.

## What the harvest gave

Two collections: the top-selling medicines of 12 large companies (FY2025), and the 2025 FDA novel approvals
from December, now put through the same harvest.

| Class | Top sellers FY2025 | FDA novel approvals 2025 |
|-------|-------------------:|-------------------------:|
| current | 29 | 27 |
| legacy | 50 | 25 |
| partner | 4 | 0 |
| other product | 15 | 3 |
| other drug | 35 | 4 |
| biosimilar | 10 | 0 |
| typo | 16 | 1 |
| not a code | 13 | 1 |
| set aside (PubChem only) | 12 | 20 |
| **candidates** | **184** | **81** |

<p class="caption">Review files of 2026-11-07, <a href="https://github.com/kerfors/development-code-archaeology/blob/main/collections/README.md"><code>collections/</code></a>.
In the FDA collection, the December codes that no source of the harvest had were added as web candidates with a cited URL.</p>

About half of the candidates are not codes of the drug at all. That is the main reason for the review.

## What I learned

- **AI can find codes; only sources can prove them.** Now every code has a named source, and a code found on
  the web cites the URL.
- **No source is complete.** Some current codes exist only in the registry (tirzepatide LY3298176). Some only
  on the web and in trial records (elinzanetant GSK1144814).
- **Sources copy each other.** Some trial records, NCI-sponsored and academic, appear to carry NCI Thesaurus
  synonym lists as other names. For those codes the registry is not an independent witness.
- **Sources have typos.** NCI Thesaurus lists PR070769 next to PRO70769, the letter O read as a zero. The same
  typo is on Wikidata as an alias.
- **A trial record lists more than the drug.** Combination partners, co-formulations and other products sit
  in the same "other names" field. Without review they would inflate the count of hidden trials.

Details: [Method](../method.html).

Next: [What the codes find in the trial registry](02-trials-under-codes.html).
