# Wikidata publication

Reviewed development codes are published to Wikidata as referenced statements with property
[P15001 "development code"](https://www.wikidata.org/wiki/Property:P15001), so that each code is verifiable,
attributed to a company, and can be told apart from other aliases in queries.

## Why a property

Before P15001, development codes on Wikidata were only aliases: no reference, no company, and no way to
correct a code without deleting it. Some aliases repeat errors of the sources they were copied from (a typo
of a code; a code of a different construct merged into a drug). Existing properties did not fit:
P2561 "name" is generic and monolingual; P1638 "working title" is constrained to works.

- Proposal: [Wikidata:Property proposal/development code](https://www.wikidata.org/wiki/Wikidata:Property_proposal/development_code),
  posted 2026-10-16, created as P15001 on 2026-10-25.
- Datatype string. Aliases: company code, compound code, compound number, research code.
- Qualifier P1027 "conferred by" for the company that assigned the code.

## Rules

**Which codes.** Only codes confirmed in review: `use_in_search` Y, rule `accept`, reviewer a person
(`collections/<collection>_code_evidence.csv`). Codes proposed by the AI and not confirmed, codes held for an
expert question, and codes accepted on one line of evidence are not published.

**Which item.** A code goes on the item of the level it names:

| Level | Example |
|-------|---------|
| Active moiety | most codes, e.g. AZD4522 on rosuvastatin |
| Salt or ester, only where the evidence names the salt | GSK573719A on umeclidinium bromide, GW642444M on vilanterol trifenatate |
| Fixed combination | LCZ696 on sacubitril/valsartan; GSK2834425 on fluticasone furoate/umeclidinium/vilanterol |

Items are found by UNII (P652). Where two items carry the same UNII, the one with P2275 (INN) or sitelinks is
used and the other is reported on its talk page.

**Which reference.**

| Evidence | Reference |
|----------|-----------|
| Trial registry | P248 ClinicalTrials.gov (Q5133746) + P3098 NCT ID + P813 retrieved |
| NCI Thesaurus | P248 NCI Thesaurus (Q19404626) + P1748 NCIt ID + P813 |
| Web | P854 URL + P813; regulator, company, registry documents and AdisInsight only |

PubChem is not used (synonyms are depositor aggregations and do not assert; circular with Wikidata). Wikipedia is
not used (circular). Codes left with only such references stay aliases.

**Trial for a registry reference.** A trial whose intervention name or other name contains the code (shared
matching rule, `patterns/aact_matching.py`), with the company that assigned the code as lead sponsor.
The value is spelled as in that trial record.

**Rank.** Normal for all statements so far.

**Aliases.** Codes are also kept as aliases, independent of the property.

## Corrections reported on talk pages

Posted 2026-10-16. Texts on the talk pages:

- [Talk:Q2697833](https://www.wikidata.org/wiki/Talk:Q2697833) abatacept: the aliases RG-2077 and CTLA4-IgG4m
  name a different construct (IgG4 fusion; NCT00076934, NCT00094380). Planned: remove the aliases.
- [Talk:Q48566801](https://www.wikidata.org/wiki/Talk:Q48566801) fluticasone furoate/umeclidinium/vilanterol:
  P527 has fluticasone where the product contains fluticasone furoate (Q2166700).
- [Talk:Q72444929](https://www.wikidata.org/wiki/Talk:Q72444929) "BCH 189" and
  [Talk:Q72498885](https://www.wikidata.org/wiki/Talk:Q72498885): label and identifiers do not match;
  possible duplicates of lamivudine and valsartan.

## State, 2026-11-07

| Step | State |
|------|-------|
| P15001 created, aliases added | done |
| Statements (manual and QuickStatements test batch, 2026-10-26) | AZD4522, BMS-562247, LY3298176, REGN668; plus 4 examples by the property creator |
| Batch for `top_sellers_fy2025` | 63 codes to go, trial pick pending |
| P2275 INN on 11 items that lack it, referenced to the WHO Recommended INN list | not started |
| Abatacept alias removal | not done; no reply on the talk page |
