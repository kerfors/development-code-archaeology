---
title: "The Hässle codes: what an old company's codes taught me"
description: "138 H codes from Hässle in Mölndal, two lists, 17 statements on Wikidata, and what changes when the codes are older than the trial registries."
written: 2026-11-22
covers: November 2026
number: 4
---

# The Hässle codes

This site follows development codes, the names a drug carries before it gets an INN: collecting them from
named sources, checking each against the record, counting the trials they bring back, and publishing them to
Wikidata with references. The first collections were recent drugs, the FDA novel approvals of 2025 and top
sellers. Their codes are in ClinicalTrials.gov, with a sponsor ([field notes 1–3](01-harvesting-codes.html)).
This note goes back in time, to the codes of one Swedish company.

When I met [Chris Southan](https://www.linkedin.com/in/cdsouthan/) recently, he asked if I used MeSH. I did
not. He said in passing that it could be useful for old codes. That sent me looking.

At AstraZeneca I worked on a product list for clinical trials. Now semi-retired, I am still fascinated by the
topic, so the old codes I thought of were the H numbers from Hässle in Mölndal, outside Göteborg. Most of all
Losec. Before omeprazole had a name it was **H 168/68**. As I remember it, the number was taken from the page
numbers in the lab notebook. That is a memory, not a finding, and this note is not about it.

It is about the codes of older compounds. Metoprolol was H 93/26, felodipine H 154/82, ximelagatran H 376/95.
Most Hässle codes are older than the trial registries. So the question changed: what can the public record say
about a code from 1968?

## What was done

I collected H codes from MeSH, ChEMBL, GSRS, NCI Thesaurus, PubMed and Wikidata ([Method](../method.html)).
MeSH, ChEMBL and GSRS were not in the harvester before (learning 2). I also used AB Hässle's US patents, and
the published history of the omeprazole programme (Olbe, Carlsson and Lindberg 2003; Sjöstrand, Olbe and
Fellenius 1999).

The collection gives two outcomes, not one:

- **A large historical list**: every H code found, 138 codes, each with its sources and its earliest date
  ([`hassle_h_codes_all.csv`](repo:collections/hassle_h_codes_all.csv)).
- **A small Wikidata list**: only the codes of substances with an INN, 18 codes. 17 of them are now on Wikidata
  as development code statements ([field note 3](03-codes-on-wikidata.html)). Only 3 say who conferred the
  code. More on that below.

I did not count trials. For a historical collection the archaeology is the product, not the trial count.

## What I learned

**1. Looking across sources finds odd things, most of all for older compounds.** Each source froze a
different moment. GSRS keeps the salt. MeSH keeps an entry term from the 1980s. A patent has the
dihydrochloride as first isolated. A company register has a study code from 1998. Side by side, the gaps show.

**2. The old codes changed the harvester.** I first harvested the H codes in a separate notebook. It showed
what the shared harvester lacked. Chris was right: MeSH carries most of the H codes, 43 of the 53 harvested
codes have a MeSH record. But MeSH was not a source. And many codes sit only on a salt record, such as
H 168/68 SODIUM, or esomeprazole's H 199/18, found only on its sodium and magnesium salts. The same happens with
recent drugs: GSK573719A sits on umeclidinium bromide. So the shared harvester got three more sources: GSRS,
ChEMBL and MeSH. Each is reached from the substance's UNII and followed to its salt records. Codes written with
a slash now count as codes. It is still one notebook, and it grows with each collection. Run again on the two earlier
collections, it changed no accepted code, but it brought new candidates to review.

**3. The rules changed too.** The most important new rule: a separator inside the number is part of the code.
Written without it, "H 234/09" becomes "H-23409", and in ClinicalTrials.gov that is a Baylor IRB number
(NCT00831480), not almokalant. Recent codes such as BMS-562247-01 keep their separator in the trial records
too, so the rule now holds for all collections.

**4. "Linked" is not "names the code".** The harvest listed what the sources link to the substance through the
UNII: parents, moieties, class concepts. NCIt C29576 came up on three different beta blockers. Only three NCIt
concepts in the INN list actually carry an H code as a synonym (C716, C72727, C87630). A reference must be a
record that names the code. The rest is context.

**5. A review must not feed the evidence it reviews.** I found two circular paths. First, the review rationale
was used as a basis for Hässle status. Later, the word "AstraZeneca" in one rationale silently changed the
status of esomeprazole's H 199/18. Both are removed. The rule now: status reads evidence files only.

**6. Who used a code is not who conferred it.** Hässle, Astra Hässle and AstraZeneca R&D Mölndal is one line:
the same site and the same numbering. The highest code found is H 510/45. So an AstraZeneca Mölndal
affiliation counts. But H codes also appear with Astra Läkemedel and Astra Alab in Södertälje (zimelidine
H 102/09, H 75/12, H 77/77). "Astra" alone does not mean Hässle. The site matters.

**7. Old codes have few affiliations.** Only 19 of the 53 harvested codes have any PubMed record with an
affiliation. Records from the 1960s and 70s mostly have none. For the oldest codes, attribution rests on the
published history or on patents. Omeprazole is the clearest case. Four PubMed records name H 168/68, from
1983, 1984, 1986 and 2015. The first three have no affiliation. The 2015 review, from Karolinska, says that
H168/68 was synthesized in 1979 and given the name omeprazole, but it does not name Hässle.

**8. Patents carry most of the early record, and I chose not to count them.** 81 codes are known only from
patents: two Hässle patent tables of 1968 and 1969 (Brändström and Carlsson), and the zimelidine patents of
1971. Patents are a new domain for me. I keep them visible, with dates and structures, but no conclusion rests
on a patent alone. The effect is large. With patents, felodipine's earliest date is 1978. Without them it is
2006.

**9. A company's own register reaches further back than the shared registries.** astrazenecaclinicaltrials.com
keeps studies from before the US registration law. SH-QBE-0020, started in 1998, names H 199/18 together with
omeprazole, and it never reached ClinicalTrials.gov.

**10. A harvest misses what it does not spell.** Melagatran's H 319/68 was missed: its only candidate was the
Wikidata alias "H-319-68", which PubMed reads as "319 68". Searched as "H 319/68", PubMed has two records from
2002. And a code no source offers is never a candidate. H77/67 is named only in the 2015 review, as a step from
the first compound, CMN 131, to the benzimidazoles. I added it to the large list by hand.

**11. Some decisions are per trial, not per code.** Omeprazole is a probe drug in an NCI trial
(NCT01218620). I skipped it in review, but the harvest still counts it, because the review can only exclude a
code. The harvest now has an exclusion per trial.

## What went to Wikidata

On 22 November I sent 17 development code statements to Wikidata (property P15001). Each has a reference that
names the code: a PubMed record whose title or abstract contains it, checked against the record text, or MeSH
or NCI Thesaurus where no PubMed record names it. Only 3 say who conferred the code: those whose PubMed record
has an Astra Hässle or AstraZeneca R&D Mölndal affiliation.

| Code | Substance on Wikidata | Reference | Conferred by |
|---|---|---|---|
| H 56/28 | [alprenolol](https://www.wikidata.org/wiki/Q201370) | PubMed [4164926](https://pubmed.ncbi.nlm.nih.gov/4164926/) |  |
| H 80/62 | [prenalterol](https://www.wikidata.org/wiki/Q7240518) | PubMed [21260](https://pubmed.ncbi.nlm.nih.gov/21260/) |  |
| H 83/69 | [timoprazole](https://www.wikidata.org/wiki/Q27271790) | PubMed [6293317](https://pubmed.ncbi.nlm.nih.gov/6293317/) |  |
| H 93/26 | [metoprolol](https://www.wikidata.org/wiki/Q409468) | PubMed [4148794](https://pubmed.ncbi.nlm.nih.gov/4148794/) |  |
| H 102/09 | [zimelidine](https://www.wikidata.org/wiki/Q203483) | PubMed [19604909](https://pubmed.ncbi.nlm.nih.gov/19604909/) |  |
| H 104/08 | [pamatolol](https://www.wikidata.org/wiki/Q15634002) | PubMed [6204505](https://pubmed.ncbi.nlm.nih.gov/6204505/) |  |
| H 113/75 | [nebidrazine](https://www.wikidata.org/wiki/Q27289460) | NCI Thesaurus C87630 |  |
| H 133/22 | [prenalterol](https://www.wikidata.org/wiki/Q7240518) | PubMed [25100](https://pubmed.ncbi.nlm.nih.gov/25100/) |  |
| H 149/94 | [picoprazole](https://www.wikidata.org/wiki/Q27289045) | PubMed [6259537](https://pubmed.ncbi.nlm.nih.gov/6259537/) |  |
| H 154/82 | [felodipine](https://www.wikidata.org/wiki/Q420644) | MeSH D015736 |  |
| H 168/68 | [omeprazole](https://www.wikidata.org/wiki/Q422210) | PubMed [6307064](https://pubmed.ncbi.nlm.nih.gov/6307064/) |  |
| H 199/18 | [esomeprazole](https://www.wikidata.org/wiki/Q553223) | PubMed [11918517](https://pubmed.ncbi.nlm.nih.gov/11918517/) |  |
| H 234/09 | [almokalant](https://www.wikidata.org/wiki/Q1426422) | PubMed [1725902](https://pubmed.ncbi.nlm.nih.gov/1725902/) | Hässle AB |
| H 314/27 | [inogatran](https://www.wikidata.org/wiki/Q6036513) | MeSH C099871 |  |
| H 319/68 | [melagatran](https://www.wikidata.org/wiki/Q27084209) | PubMed [11820295](https://pubmed.ncbi.nlm.nih.gov/11820295/) | Hässle AB |
| H 324/38 | [clevidipine](https://www.wikidata.org/wiki/Q5132338) | PubMed [19584385](https://pubmed.ncbi.nlm.nih.gov/19584385/) |  |
| H 376/95 | [ximelagatran](https://www.wikidata.org/wiki/Q3570984) | PubMed [11228338](https://pubmed.ncbi.nlm.nih.gov/11228338/), [11701546](https://pubmed.ncbi.nlm.nih.gov/11701546/) | Hässle AB |

Tazolol, H 110/38, stays out: its originator is not settled.

This is a new bar. All earlier statements from this work have a company. Here the code is published where a
record names it, and the company is left out where no record anyone can check shows it. It can be added later.

The surprise is Losec. Its code, H 168/68, cannot be tied to Hässle from open records without patents. The
published history (Olbe 2003) has the link in a figure behind a paywall, so in the large list H 168/68 and four
other codes are "established (published history, not re-checked)". That is the next thing to dig into.

## The numbers themselves

How the H numbers were built is not settled here. My memory of the lab notebook is one reading. The public
record cannot confirm it, and I set the question aside to follow the codes instead. I may go further on this
later, for example in Hässle's archive at Riksarkivet in Göteborg (Hässle AB:s, Mölndal, arkiv, GLA/C0126).

If you worked at Hässle, or know how the codes were given, I would very much like to hear from you.

The lists are in the repository: the [historical list of 138 H codes](repo:collections/hassle_h_codes_all.csv),
the [Wikidata list](repo:collections/hassle_h_codes_wikidata.csv) and the [inputs](repo:hassle_codes/inputs/),
with a source for every value.
