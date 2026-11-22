# Study code patterns

Sponsor study codes (protocol IDs) in AACT `id_information.id_value` that embed a development code
without a word boundary, so a token search for the code does not find them.
Example: `CLOU064A1301` contains `LOU064`.

Background: Forsberg & Goude, "Study URI", PhUSE EU Connect 2018 (code type pattern recognition
of study codes).

## Admission rule

A pattern row is added only when all of these hold:

1. **It changes a count.** It finds trials for a code in a collection that no other search finds
   (INN in `interventions.name`; the code as a token in interventions, other names, titles or
   `id_information`). Rows that only classify study codes are not added; their examples become asserts.
2. **It is scoped to codes, not sponsors.** `applies_to_codes` lists accepted codes from the
   collections. The table grows only when a collection brings a new code.
3. **No substance-code mapping.** Study codes that do not contain the development code
   (e.g. AstraZeneca D-codes, D3562C00096 for rosuvastatin; BMS CA209-473 for nivolumab)
   are not searched, and study-code prefixes are not mapped to product codes
   (e.g. Regeneron R668-AD-1416: protocol code prefix R668, product code REGN668, EU CTR 2014-002619-40;
   R668 stays `not_a_code` in the review). Known limit, size unknown.
4. **Residue is reported, not chased.** Each run lists `id_information` values that contain a code
   key but match neither the token search nor a pattern row, for human review.

## study_code_patterns.csv

| Column | Content |
|--------|---------|
| `pattern_id` | P1, P2, ... |
| `applies_to_codes` | Development codes the pattern is used for |
| `field` | AACT field searched |
| `regex` | PostgreSQL regex, case-insensitive; `{code}` is replaced by the code with optional separators |
| `description` | The pattern in words |
| `maps_to` | What the matched part identifies |
| `example_id_value`, `example_nct` | A trial found only via this pattern |
| `trials_with_pattern` | Trials whose `id_information` matches, all listed codes |
| `trials_only_via_pattern` | Of these, trials not found by INN or code token search |
| `lead_sponsor_observed` | Lead sponsors of the matching trials |
| `source` | Where the pattern is documented |
| `aact_snapshot` | AACT date of the counts |
| `status` | `proposed` or `ruled <initials> <date>` |

## Decided

- Trials found only via a pattern include sponsor studies where the drug is named by brand only
  (NCT04781881, "Entresto") or not at all (NCT04459507, "No intervention"). They count as trials of
  the moiety: the sponsor's own studies of the compound (KF 2026-10-15). The archaeology output marks
  them in column `Found_only_via_pattern`, so reports can show them separately.
- A code with a hyphen or slash inside the number (`H 234/09`, `H 234-09`, `BMS-562247-01`, `NNC 0113-0217`)
  is searched only in spellings that keep that separator. When a source also gives a spelling without it
  (`H 37695` next to `H 376/95`), that spelling is not searched. Without the separator such codes collide
  with other identifiers: `H-23409` is a Baylor IRB number (NCT00831480), not almokalant. First ruled for
  H codes, then generalised: in AACT (2026-11-21) every trial of BMS-562247-01, BMS-936558-01 and
  NNC 0113-0217 keeps the separator in the record, so no trial is lost. A space inside the number is not
  such a separator: it can be digit grouping (`GSK 685 698` for GSK685698) (KF 2026-11-21).
