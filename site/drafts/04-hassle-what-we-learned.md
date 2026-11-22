---
title: "The Hässle codes: what an old company's codes taught me"
description: "138 H codes from Hässle in Mölndal, two lists, 17 statements on Wikidata, and what changes when the codes are older than the trial registries."
written: 2026-12-XX
covers: November 2026
number: 4
---

# The Hässle codes

At AstraZeneca I worked on a product list for clinical trials. Now semi-retired, I am still fascinated by the
topic, and I came to think about the old H numbers from Hässle in Mölndal, outside Göteborg. Most of all about
Losec. Before omeprazole had a name it was **H 168/68**. As I remember it, the number was taken from the page
numbers in the lab notebook. That is a memory, not a finding, and this note is not about it.

It is about the codes of older compounds. Metoprolol was H 93/26, felodipine H 154/82, ximelagatran H 376/95.
The first collections in this work were recent drugs: FDA novel approvals 2025 and top sellers. Their codes are
in ClinicalTrials.gov, with a sponsor. Most Hässle codes are older than the trial registries. So the question
changed: what can the public record say about a code from 1968?

## What was done

I collected H codes from the same sources as before: MeSH, ChEMBL, GSRS, NCI Thesaurus, PubMed and Wikidata
([Method](../method.html)). I added two more: AB Hässle's US patents, and the published history of the
omeprazole programme (Olbe, Carlsson and Lindberg 2003; Sjöstrand, Olbe and Fellenius 1999).

The collection gives two outcomes, not one:

- **A large historical list**: every H code found, 138 codes, each with its sources and its earliest date.
- **A small Wikidata list**: only the codes of substances with an INN, 18 codes. 17 of them are now on Wikidata
  as development code statements ([field note 3](03-codes-on-wikidata.html)). Only 3 say who conferred the
  code. More on that below.

I did not count trials. For a historical collection the archaeology is the product, not the trial count.

| Hässle status | Codes |
|---|---|
| established | 17 |
| established (published history, not re-checked) | 5 |
| not established | 33 |
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

**5. Old codes have few affiliations.** Only 19 of the 137 harvested codes have any PubMed record with an
affiliation. Records from the 1960s and 70s mostly have none. For the oldest codes, attribution rests on the
published history or on patents. Omeprazole is the clearest case. Four PubMed records name H 168/68, from
1983, 1984, 1986 and 2015. The first three have no affiliation. The 2015 review, from Karolinska, says that
H168/68 was synthesized in 1979 and given the name omeprazole, but it does not name Hässle.

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

**9. A harvest misses what it does not spell.** D961H was missed because no source offered it as a candidate.
Six of its ten trials name only "D961H" as the intervention, without esomeprazole, so a search by the INN does
not find them. Melagatran's H 319/68 was missed too. The only candidate was
the Wikidata alias "H-319-68", and PubMed reads that as "319 68". Searched as "H 319/68", PubMed has two
records from 2002, one with an AstraZeneca R&D Mölndal affiliation. That made H 319/68 established. And a
code no source offers is never a candidate at all. The same 2015 review names H77/67, a step on the way from
the first compound, CMN 131, to the benzimidazoles. It is the only PubMed record with that code. It has no INN,
no patent in my set and no PubChem entry. I added it to the large list by hand.

**10. Some decisions are per trial, not per code.** Omeprazole is a probe drug in an NCI trial
(NCT01218620). I skipped it in review, but the harvest still counts it, because the review can only exclude a
code. The harvest now has an exclusion per trial.

## What went to Wikidata

On 22 November I sent 17 development code statements to Wikidata (property P15001), one per code. Tazolol,
H 110/38, stays out: one MeSH line, and the originator code is not settled.

For recent drugs the reference was a ClinicalTrials.gov record, with the company as lead sponsor. For Hässle
codes that does not work. So the references are:

- a PubMed record, but only if its title or abstract contains the code. I checked every one against the
  record text. A search hit is not enough;
- MeSH or NCI Thesaurus only where no PubMed record names the code;
- no aggregated synonym lists. Felodipine's earliest PubMed record is a LactMed book chapter, where H 154/82
  sits in a list of synonyms. I used MeSH instead.

14 statements have a PubMed reference, 2 MeSH and 1 NCI Thesaurus.

**Only 3 of the 17 say "conferred by Hässle AB".** These are almokalant H 234/09, melagatran H 319/68 and
ximelagatran H 376/95. Their PubMed records have an Astra Hässle or AstraZeneca R&D Mölndal affiliation. For
the other 14 I could not show the company from a record anyone can check. That includes omeprazole, H 168/68.
For it, and for H 83/69 and H 149/94, the link between code and company is in the published history
(Olbe 2003). But there it sits in a figure behind a paywall, and the abstract names no code. So in the
large list these codes are now "established (published history, not re-checked)", together with two more
codes from the same kind of source. The list and Wikidata say the same thing.

This is a new bar. All earlier statements from this work have a company. Here I publish the code and leave
the company out where it is not shown. The statement still says what is shown: this is a development code of
this substance, and here is a record that names it. The company can be added later, if the evidence turns up.

The code of Losec, the best-known Hässle product, cannot be tied to Hässle from open records without patents.
I did not expect that. It is the next thing to dig into.

## The numbers themselves

How the H numbers were built is not settled here. My memory of the lab notebook is one reading. The public
record cannot confirm it, and I set the question aside to follow the codes instead. I have asked Riksarkivet in
Göteborg (Hässle AB:s, Mölndal, arkiv, GLA/C0126) and AstraZeneca.

If you worked at Hässle, or know how the codes were given, I would very much like to hear from you.

The lists and their inputs are in the repository: `collections/hassle_h_codes_all.csv`,
`collections/hassle_h_codes_wikidata.csv` and `hassle_codes/inputs/`, with a source for every value.
