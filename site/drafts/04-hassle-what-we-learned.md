---
title: "The Hässle codes: what an old company's codes taught me"
description: "137 H codes from Hässle in Mölndal, two lists, and what changes when the codes are older than the trial registries."
written: 2026-12-XX
covers: November 2026
number: 4
---

# The Hässle codes

Omeprazole, the first proton pump inhibitor, was developed at Hässle in Mölndal, outside Göteborg. Before it
had a name it was **H 168/68**. Metoprolol was H 93/26, felodipine H 154/82, ximelagatran H 376/95.

The first collections in this work were recent drugs: FDA novel approvals 2025 and top sellers. Their codes are
in ClinicalTrials.gov, with a sponsor. Most Hässle codes are older than the trial registries. So the question
changed: what can the public record say about a code from 1968?

## What was done

I collected H codes from the same sources as before: MeSH, ChEMBL, GSRS, NCI Thesaurus, PubMed and Wikidata
([Method](../method.html)). I added two more: AB Hässle's US patents, and the published history of the
omeprazole programme (Olbe, Carlsson and Lindberg 2003; Sjöstrand, Olbe and Fellenius 1999).

The collection gives two outcomes, not one:

- **A large historical list**: every H code found, 137 codes, each with its sources and its earliest date.
- **A small Wikidata list**: only the codes of substances with an INN, 18 codes. These get a development code
  statement ([field note 3](03-codes-on-wikidata.html)), with "conferred by AB Hässle" only where that is
  established.

I did not count trials. For a historical collection the archaeology is the product, not the trial count.

| Hässle status | Codes |
|---|---|
| established | 22 |
| not established | 32 |
| known only from patents | 81 |
| not Hässle | 2 |

## What I learned

**1. Looking across sources finds odd things, most of all for older compounds.** Each source froze a
different moment. GSRS keeps the salt. MeSH keeps an entry term from the 1980s. A patent has the
dihydrochloride as first isolated. A company register has a study code from 1998. Side by side, the gaps show.

**2. "Linked" is not "names the code".** The harvest listed what the sources link to the substance through the
UNII: parents, moieties, class concepts. NCIt C29576 came up on three different beta blockers. Only three NCIt
concepts in the INN list actually carry an H code as a synonym (C716, C72727, C87630). A reference must be a
record that names the code. The rest is context.

**3. A review must not feed the evidence it reviews.** I found two circular paths. First, the review rationale
was used as a basis for Hässle status. Later, the word "AstraZeneca" in one rationale silently changed the
status of esomeprazole's H 199/18. Both are removed. The rule now: status reads evidence files only.

**4. Who used a code is not who conferred it.** Hässle, Astra Hässle and AstraZeneca R&D Mölndal is one line:
the same site and the same numbering. The highest code found is H 510/45. So an AstraZeneca Mölndal
affiliation counts. But H codes also appear with Astra Läkemedel and Astra Alab in Södertälje (zimelidine
H 102/09, H 75/12, H 77/77). "Astra" alone does not mean Hässle. The site matters.

**5. Old codes have few affiliations.** Only 19 of the 137 codes have any PubMed record with an affiliation.
Records from the 1960s and 70s mostly have none. For the oldest codes, attribution rests on the published
history or on patents.

**6. Patents carry most of the early record, and I chose not to count them.** 81 codes are known only from
patents: two Hässle patent tables of 1968 and 1969 (Brändström and Carlsson), and the zimelidine patents of
1971. Patents are a new domain for me. I keep them visible, with dates and structures, but no conclusion rests
on a patent alone. The effect is large. With patents, felodipine's earliest date is 1978. Without them it is
2006.

**7. A company code has layers.** From my AstraZeneca years: in a study code like SH-QBE-0020, QBE is the
compound. In D961H, D961 is the compound and the last letter the indication, so D961H is a *project* code. The
study IDs, such as D9617C00001, carry the project again. So one substance can have a substance code, a project
code and study codes. In ClinicalTrials.gov, D961H is in 10 AstraZeneca trials from 2007 to 2018. Another
letter, another project: D961S appears in a study with esomeprazole and buffered aspirin.

**8. The company trial register is a source I lacked.** astrazenecaclinicaltrials.com keeps studies from
before the US registration law that never reached ClinicalTrials.gov. SH-QBE-0020, started in 1998, names
H 199/18 together with omeprazole. It links the old H code, the study code and, through QBE, the later D code.

**9. A harvest misses what it does not spell.** D961H was missed, likely because the code sits in brackets in
the intervention name: "Esomeprazole (D961H)". Melagatran's H 319/68 was missed too. The only candidate was
the Wikidata alias "H-319-68", and PubMed reads that as "319 68". Searched as "H 319/68", PubMed has two
records from 2002, one with an AstraZeneca R&D Mölndal affiliation. That made H 319/68 established.

**10. Some decisions are per trial, not per code.** Omeprazole is a probe drug in an NCI trial
(NCT01218620). I skipped it in review, but the harvest still counts it, because the review can only exclude a
code. The next version needs an exclusion per trial.

## The references for Wikidata

For recent drugs the reference was a ClinicalTrials.gov record or NCI Thesaurus. For Hässle codes that does
not work. So the rule for the small list is:

- the Hässle source (the published history, or PubMed records with a Hässle or Mölndal affiliation) wherever
  "conferred by" is set, because it is what supports the company;
- the earliest PubMed record naming the code, on every row that has one;
- MeSH or NCI Thesaurus only where no PubMed record names the code;
- ChEMBL and GSRS as context only. There the code often sits on the salt record, not on the substance.

17 of the 18 codes are ready. Tazolol, H 110/38, is open: one MeSH line, and the originator code is not
settled.

## What is parked

Why is omeprazole H 168/68? Two readings still stand: lab notebook and page, or compound register and line.
The public record can narrow that question but not answer it, and most of the evidence for it comes from
patents. I have asked Riksarkivet in Göteborg (Hässle AB:s, Mölndal, arkiv, GLA/C0126) and AstraZeneca. That will be a later note.

If you worked at Hässle, or know how the codes were given, I would very much like to hear from you.

The lists and their inputs are in the repository: `collections/hassle_h_codes_all.csv`,
`collections/hassle_h_codes_wikidata.csv` and `hassle_codes/inputs/`, with a source for every value.
