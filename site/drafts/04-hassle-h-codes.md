---
title: "Why is omeprazole H 168/68? A first report on the Hässle codes"
description: "Hässle in Mölndal gave its substances codes like H 168/68. What the public record says about how they were built, 133 codes later, and what only the archive can answer."
written: 2026-12-XX
covers: November 2026
number: 4
---

# Why is omeprazole H 168/68?

Omeprazole, the first proton pump inhibitor, was developed at Hässle in Mölndal, outside Göteborg. Before it
had a name it was **H 168/68**. Metoprolol was H 93/26, felodipine H 154/82, ximelagatran H 376/95.

I want to add H 168/68 to the omeprazole item on Wikidata as a development code
([field note 3](03-codes-on-wikidata.html)). That made me ask what the code means. Years ago, when I worked
with product names at AstraZeneca, I read that the code tells **which page in the lab notebook** the
structure was first written down. I have not found that source again.

This note reports what the public record says so far. A follow-up will come when the archive answers.

## What the published history says

The history of omeprazole is well told by the people who made it (Olbe, Carlsson and Lindberg 2003; Olbe
2015; Sjöstrand, Olbe and Fellenius 1999). It gives the codes along the way, with the year of synthesis:

| Code | Substance | Year |
|---|---|---|
| H 81/75 | a carbamate, tested in volunteers | 1971–72 |
| H 124/26 | first benzimidazole lead | 1973 |
| H 83/69 | timoprazole | 1974 |
| H 149/94 | picoprazole | 1976 |
| H 168/68 | omeprazole | 1979 |

None of these sources says how the codes were built.

## What I did

I collected H codes from the same named sources as for the recent drugs: MeSH, ChEMBL, GSRS, NCI Thesaurus,
PubMed and Wikidata ([Method](../method.html)). Then I read AB Hässle's US patents on Google Patents, and the
patent PDFs where the text was unclear.

Most patents never name a code. Three do, and two of them print the codes in a table headed "Code Number",
**without the H**. My pattern search missed those two until I looked at the page images. The benzofuran
patent from April 1968 alone lists 52 codes with full structures.

The count is now **133 Hässle codes**. Two other "H codes" turned out not to be Hässle's: in "H-7-94", a
cyclosporin analogue, the H is a letter in a series that also has A-4-16 and C-5-34.

To date the codes I used the **latest-possible date**. That is the patent filing or priority date where the
code is printed, or where the substance is described under its chemical name, or the first publication naming
the code. A latest-possible date says the substance existed by then. It does not say when it was made.

## What the data rules out

- **The second number is not a year.** H 81/75 was tested in 1971–72; H 168/68 was made in 1979.
- **The whole code is not one running number.** Timoprazole, 83/69, came after H 124/26.
- **The first number is not a project.** H 124/26 and its sulphoxide, timoprazole H 83/69, differ.
  Felodipine, a cardiovascular drug, sits between two of the ulcer compounds.

## Two readings still standing

Both readings say the code points to where a substance was first recorded:

1. **Lab notebook and page.** The first number is the notebook, the second the page.
2. **Compound register and line.** The first number is a page in a central register, the second the line.

Some of the evidence leans towards the notebook. Some of it fits a register equally well.

**The second number runs from 03 to 99.** There are no three-digit second numbers. Notebooks of about 100
pages are common. A register page with 100 lines would be unusual. This leans towards the notebook, weakly,
because I do not know what Hässle's register looked like.

**One first number, one team.** 18 first numbers carry more than one code. In every case where I know the
team, one team or project has them all. One case is open: first number 56 holds two of Brändström's
benzofurans and alprenolol, and I do not know who made alprenolol. A notebook belongs to a chemist, so this
leans towards the notebook. But the codes come from patent tables about one series at a time, so the sample
is biased.

**End of one, start of the next.** In the zimelidine patent of 1971 one team's codes go H 94/96, H 99/88,
H 100/03 and H 100/04, then H 102/09 and H 102/10: near the end of one number or the start of the next. That
is what you would see if a chemist fills a notebook and takes a new one. But it is one team, and few codes.

**Two numbers from one reaction.** The same patent separates two isomers from one reaction. The one that
crystallises first is H 100/04, the one recovered later from the mother liquor is H 100/03. So the code is
given per isolated substance, not per experiment. A register with one line per substance fits that directly.
A notebook fits it only if each substance got its own page.

## Two loose ends

**Timoprazole.** By April 1968 the first numbers had passed 56, and by 1971 they had reached 102. Yet
timoprazole, made in 1974 according to the published history, is H 83/69. Either an old notebook was still
in use in 1974, or the substance was made years earlier for another purpose and tested against acid
secretion only in 1974.

**Omeprazole's year.** The omeprazole patent names the compound in its claims and claims a Swedish priority
of 14 April 1978. The published history says omeprazole was synthesised in 1979. Either it was in the
Swedish application, or it was added when the US application was filed in April 1979. Only the Swedish
application can tell.

## What I learned

1. **"H" is not always Hässle.** A pattern finds strings. Each one has to be checked against the record.
2. **Patents are an underused source for codes,** but you have to read the pages, not just the text layer.
   A table can print the codes without the prefix you search for.
3. **Latest-possible dates are honest dates.** They moved several codes back by years: felodipine from 2006
   (first PubMed record) to 1978 (patent), metoprolol from 1973 to 1970.
4. **The public record has an edge.** It can narrow the question, but not answer it. The answer is in a lab
   notebook or a register, if they still exist.

## What only the archive can answer

Hässle's archive is at Riksarkivet in Göteborg (Hässle AB:s, Mölndal, arkiv, GLA/C0126). Lab notebooks may
still be with AstraZeneca. I have asked both:

- Was there a central compound register? How many lines per page?
- Were lab notebooks numbered from one central series, and how many pages did they have?
- Did each isolated substance, salt and intermediate get its own number?
- When was timoprazole first made, and for what purpose?
- Was omeprazole in the Swedish application of April 1978?

If you worked at Hässle, or know how the codes were given, I would very much like to hear from you.

All codes, dates and sources are in the repository: `hassle_codes/output/research/` (findings files with a
source for every value).
