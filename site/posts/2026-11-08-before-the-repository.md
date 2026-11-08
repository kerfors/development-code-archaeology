---
title: "Where it started: a holiday project and a detour into chemistry"
description: "December 2025: how many trials of last year's new drugs can only be found by their development codes? February 2026: can the codes be found in PubChem? What I learned, and the two questions I took further."
date: 2026-11-08
covers: December 2025 – February 2026
order: 0
---

# Where it started

## December 2025: a holiday project

Between Christmas and New Year, my "mellandagsprojekt", I took the drugs FDA approved as novel small
molecules in 2025 and asked a simple question. How much of their history in ClinicalTrials.gov can I find by
the INN, and how much only by their development codes?

I asked Claude and Gemini to find the codes: the sponsor's code at approval, and older codes from originators,
licensors and companies that had been acquired. Then I checked each code by web search against company,
regulator and reference sources. That check mattered. For elamipretide the AI gave me "SBT-31" and "SPI-31".
They look right, and no source has them.

Then I searched AACT, the database copy of ClinicalTrials.gov, with the INN and with the codes. Short codes
need care: "SS-31" matched "COMPASS31", and "WS-12" matched "AEWS1221".

The result surprised me. Of 572 trials, 191 (33%) could only be found by a development code. 24 of the 29
drugs had such trials. I wrote it up in two articles on 30 December:
[Data Archaeology: Tracing Drug Development Codes Through Name Changes, Mergers, and Licensing Deals](https://www.linkedin.com/pulse/data-archaeology-tracing-drug-development-codes-through-forsberg-89t1e/)
and [Searching AACT for Development Codes: A Practical Guide](https://www.linkedin.com/pulse/searching-aact-development-codes-practical-guide-kerstin-forsberg-2rhze/).

When I reran the same collection in October 2026, with a stricter matching rule and a newer AACT snapshot,
the share was 29% (197 of 679 drug–trial pairs). Lower, but the same picture.

## February 2026: a detour into chemistry

In February it was nice to catch up with Chris Southan, a friend and former colleague, and we talked about
what more could be done beyond what I first did. Chris has worked on code names from the chemistry side for
years, so I tried that side: from code to structure, in PubChem. All 29 INNs resolved. Most codes did too, but three
things went wrong in instructive ways:

- **The code names a salt.** DS-6051b resolves to a salt, the INN to the free base. Same active moiety,
  different record.
- **The code is there, but not connected.** GSK1144814 sits on a substance record that is not linked to the
  elinzanetant compound, so a name search does not find it.
- **The code was never deposited.** SAR444671, Sanofi's code for rilzabrutinib after it bought Principia,
  is not in PubChem at all. The older code PRN1008 is.

Structure coverage is Chris's question, and I left it with him. But two things stayed with me: the active
moiety is the unit to count by, and PubChem is a source of codes, not proof of them.

### Chris's work on code names

Chris and I have addressed this from two different perspectives:
his from chemistry and public compound databases, mine from clinical trials, data standards and identity.
Both meet the same issue: the names of a substance are spread over many sources and not linked.

- Southan C, Pawson AJ, Sharman JL, Benson HE, Faccenda E. [Resolving cryptic needles to molecular structures: the GtoPdb experience](https://www.slideshare.net/slideshow/southan-needles-acs/51539822).
  ACS CINF, 2015. Code chains across mergers (MK-8931, SCH 900931, verubecestat), format variants, and a
  proposal for a standard identifier format.
- Rujan R-M, Amaral M, Southan C, Dunlop I. [Resolving code names to structures from the medicinal chemistry literature: not as FAIR as it should be](https://cisrg.shef.ac.uk/shef2023/?p=771).
  Medicines Discovery Catapult, 2023 ([slides](https://cisrg.shef.ac.uk/shef2023/wp-content/uploads/2023/10/Resolving_Code_Names_Rujan.pdf)).
  Code mining from J. Med. Chem. abstracts, false positives, and recommendations for code formats.

## What I took further

The articles ended with open questions. Two of them became the repository, from October 2026:

- **Can development codes be harvested programmatically, from named sources?** Not by asking an AI to
  remember them, but by collecting them where they are written down, with a rule I can check.
- **Can an open data community hold them?** On Wikidata, codes were only aliases, with no source and no
  company. That led to a property proposal, and to the next post.

Next: [Two 2025 collections: harvest, review, Wikidata](2026-11-08-two-2025-collections.html).

<details markdown="1">
<summary>Appendix: the discovery prompt I used in December 2025</summary>

```markdown
# Drug Development Code Discovery

## Your Role
Data archaeologist finding historical development codes for approved drugs.

## Input
[Drug list with INN and Brand names]

## Task
For each drug, find:

1. **Current development code** - The sponsor's code at time of approval
2. **Legacy codes** - Earlier codes from:
   - Original discoverer (before licensing)
   - Previous corporate owner (before acquisition)
   - Academic/government origin (NIH, NCI codes if applicable)

## Search Strategy
- Phase 1 trial titles (often code-only, before INN assigned)
- "Drug X licensed from Company Y" announcements
- Patent assignee history
- Wikipedia "List of pharmaceutical compound number prefixes" for sponsor attribution

## Output Format
| INN | Current Code | Legacy Codes | Company Transitions | Confidence | Source Type |

## Critical Rules
- Mark uncertain codes as "VERIFY: [code]"
- Never invent codes - if you can't find it, say "None found"
- Distinguish code TYPES: development code (compound) vs protocol code (study)
- Note format variations you encountered (AZD-0914 vs AZD0914)
```

</details>
