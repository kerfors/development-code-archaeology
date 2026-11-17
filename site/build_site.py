"""Build the GitHub Pages site into docs/ from the Markdown sources in site/.

  site/notes/*.md   numbered field notes; fixed once written (figures come from site/data/<run_id>/)
  site/pages/*.md   living reference pages (method, decisions, identity, collections)
  site/style.css    copied to docs/

Each source file starts with a YAML front matter block (title, description; field notes also number, covers, written, data, batches).
A line that is only a placeholder, e.g. {{chart:by_phase fda_novel_2025}}, is replaced by computed HTML.
Decisions are read from wikidata/README.md and publication outcomes from wikidata/batches/, so neither is
typed twice. docs/ is generated: edit site/, then run  python site/build_site.py  from the repository root.
Requires: pandas, markdown, pyyaml.
"""
import glob
import html
import os
import re
import shutil

import markdown
import pandas as pd
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
DOCS = os.path.join(ROOT, "docs")
REPO_URL = "https://github.com/kerfors/development-code-archaeology/blob/main"
SITE_TITLE = "Development code archaeology"
COLLECTION_LABEL = {"fda_novel_2025": "FDA novel approvals 2025", "top_sellers_fy2025": "Top sellers FY2025"}


def esc(s):
    return html.escape(str(s))


def read_source(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    assert m, f"{path}: no front matter"
    meta = yaml.safe_load(m.group(1))
    for key in ["title", "description"]:
        assert meta.get(key), f"{path}: front matter lacks '{key}'"
    meta["slug"] = os.path.splitext(os.path.basename(path))[0]
    return meta, m.group(2)


# ------------------------------------------------------------------ figure data
def data(run_id, name):
    path = os.path.join(SITE, "data", run_id, f"{name}.csv")
    assert os.path.isfile(path), f"missing {path}: run derive_figures.py for {run_id}"
    return pd.read_csv(path)


def svg_per_drug(run_id, collection):
    g = data(run_id, "per_drug")
    g = g[g["collection"] == collection].copy()
    assert len(g), f"no per_drug rows for {collection}"
    g["share"] = g["hidden"] / g["pairs"]
    g = g.sort_values(["share", "hidden"], ascending=[False, False])
    row, left, width, gap = 19, 190, 420, 6
    max_pairs = g["pairs"].max()
    out = [f'<svg class="chart" viewBox="0 0 {left + width + 90} {row * len(g) + 40}" role="img">',
           f"<title>{esc(COLLECTION_LABEL[collection])}: drug–trial pairs per drug, via the INN and only via a code</title>",
           f'<rect class="bar-hid" x="{left}" y="4" width="10" height="10"/><text class="lbl" x="{left + 15}" y="13">only via a code</text>',
           f'<rect class="bar-inn" x="{left + 125}" y="4" width="10" height="10"/><text class="lbl" x="{left + 140}" y="13">via the INN</text>']
    for i, r in enumerate(g.itertuples()):
        y = 24 + i * row
        w_all, w_hid = width * r.pairs / max_pairs, width * r.hidden / max_pairs
        out += [f'<text class="lbl" x="{left - 8}" y="{y + 11}" text-anchor="end">{esc(r.inn)}</text>',
                f'<rect class="bar-hid" x="{left}" y="{y}" width="{w_hid:.1f}" height="{row - gap}"/>',
                f'<rect class="bar-inn" x="{left + w_hid:.1f}" y="{y}" width="{w_all - w_hid:.1f}" height="{row - gap}"/>',
                f'<text class="val" x="{left + w_all + 6:.1f}" y="{y + 11}">{r.hidden} of {r.pairs}</text>']
    return "\n".join(out + ["</svg>"])


def svg_shares(run_id, name, collection, label_col):
    g = data(run_id, name)
    g = g[(g["collection"] == collection) & (g["pairs"] > 0)]
    assert len(g), f"no {name} rows for {collection}"
    left, width, row = 130, 300, 24
    out = [f'<svg class="chart small" viewBox="0 0 {left + width + 150} {row * len(g) + 8}" role="img">',
           f"<title>{esc(COLLECTION_LABEL[collection])}: share of drug–trial pairs found only via a code</title>"]
    for i, r in enumerate(g.itertuples()):
        y, pct = 4 + i * row, 100 * r.hidden / r.pairs
        out += [f'<text class="lbl" x="{left - 8}" y="{y + 13}" text-anchor="end">{esc(getattr(r, label_col))}</text>',
                f'<rect class="bar-track" x="{left}" y="{y}" width="{width}" height="{row - 8}"/>',
                f'<rect class="bar-hid" x="{left}" y="{y}" width="{width * pct / 100:.1f}" height="{row - 8}"/>',
                f'<text class="val" x="{left + width + 8}" y="{y + 13}">{pct:.0f}% ({r.hidden} of {r.pairs})</text>']
    return "\n".join(out + ["</svg>"])


def stats_trials_2025(run_id):
    t = data(run_id, "totals").set_index("collection")
    ph = data(run_id, "by_phase")
    p1 = ph[(ph["collection"] == "fda_novel_2025") & (ph["phase"] == "Phase 1")].iloc[0]
    fda, top = t.loc["fda_novel_2025"], t.loc["top_sellers_fy2025"]
    cells = [(f"{100 * fda.hidden / fda.pairs:.0f}%", f"of drug–trial pairs for the 2025 FDA novel approvals are found only via a code ({fda.hidden} of {fda.pairs})"),
             (f"{100 * p1.hidden / p1.pairs:.0f}%", f"of their Phase 1 pairs are found only via a code ({p1.hidden} of {p1.pairs})"),
             (f"{100 * top.hidden / top.pairs:.1f}%", f"for the top-selling medicines of 12 large companies ({top.hidden} of {top.pairs:,})")]
    return '<div class="stats">' + "".join(
        f'<div class="stat"><span class="num">{n}</span><span class="txt">{esc(t)}</span></div>' for n, t in cells) + "</div>"


# ------------------------------------------------------------------ tables read from the repository
def decision_rows():
    rows = []
    for line in open(os.path.join(ROOT, "wikidata", "README.md"), encoding="utf-8"):
        m = re.match(r"^\| (D\d+) \| ([\d-]+) \| (.+?) \| (.+?) \|\s*$", line)
        if m:
            rows.append(m.groups())
    assert rows and [r[0] for r in rows] == [f"D{i}" for i in range(len(rows))], "decision table D0..Dn not found"
    return rows


def inline_md(s):
    return markdown.markdown(s).removeprefix("<p>").removesuffix("</p>")


def table_decisions():
    body = "".join(f"<tr><td>{d}</td><td>{inline_md(text)}</td><td class=\"codes\">{inline_md(codes)}</td></tr>"
                   for d, _, text, codes in decision_rows())
    return ('<div class="tablewrap"><table><thead><tr><th>ID</th><th>Decision</th><th>Codes</th></tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def outcome_rows(files=None):
    """Per batch file: codes mapped, published, held, not published. files=None: all batches (living pages)."""
    rows, tot = [], [0, 0, 0, 0]
    paths = sorted(glob.glob(os.path.join(ROOT, "wikidata", "batches", "*_batch_*.csv")))
    if files is not None:
        paths = [os.path.join(ROOT, "wikidata", "batches", f) for f in files]
        assert all(os.path.isfile(p) for p in paths), f"batch files not found: {files}"
    for path in paths:
        collection = re.match(r"(.+)_batch_\d{8}_\d{4}\.csv$", os.path.basename(path)).group(1)
        b = pd.read_csv(path, dtype=str, keep_default_na=False)
        pub = b[b["result"] == "publish"]
        refs = pub["reference"].value_counts()
        n = [len(b), len(pub), int((b["result"] == "hold").sum()), int((b["result"] == "not published").sum())]
        assert sum(n[1:]) == n[0], f"{path}: unknown result values"
        tot = [a + c for a, c in zip(tot, n)]
        rows.append([COLLECTION_LABEL.get(collection, collection), n[0],
                     f"{n[1]} ({refs.get('ClinicalTrials.gov', 0)} registry, {refs.get('NCI Thesaurus', 0)} NCIt)", n[2], n[3]])
    rows.append(["All", tot[0], tot[1], tot[2], tot[3]])
    return rows


def table_outcome(files=None):
    head = ["Collection", "Codes mapped", "Published", "Held", "No acceptable reference"]
    body = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in outcome_rows(files))
    return ('<div class="tablewrap"><table class="num"><thead><tr>' + "".join(f"<th>{h}</th>" for h in head)
            + f"</tr></thead><tbody>{body}</tbody></table></div>")


# ------------------------------------------------------------------ diagrams
DIAGRAMS = {
    "pipeline": """<svg class="diagram" viewBox="0 0 760 210" role="img">
<title>Pipeline: named sources, harvest, evidence rule and review, trial search, Wikidata</title>
<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="arrowhead" d="M0,0 L10,5 L0,10 z"/></marker></defs>
<g class="src"><rect x="4" y="10" width="150" height="30" rx="4"/><text x="79" y="30">NCI Thesaurus</text>
<rect x="4" y="50" width="150" height="30" rx="4"/><text x="79" y="70">PubChem synonyms</text>
<rect x="4" y="90" width="150" height="30" rx="4"/><text x="79" y="110">AACT other names</text>
<rect x="4" y="130" width="150" height="30" rx="4"/><text x="79" y="150">AACT intervention names</text>
<rect x="4" y="170" width="150" height="30" rx="4"/><text x="79" y="190">Web, URL-cited</text></g>
<g class="step"><rect x="190" y="75" width="130" height="60" rx="6"/><text x="255" y="100">Harvest</text><text class="sub" x="255" y="118">candidates + evidence</text>
<rect x="335" y="75" width="140" height="60" rx="6"/><text x="405" y="100">Rule + review</text><text class="sub" x="405" y="118">a person decides</text>
<rect x="495" y="20" width="135" height="60" rx="6"/><text x="562" y="45">Trial search</text><text class="sub" x="562" y="63">INN + accepted codes</text>
<rect x="495" y="130" width="135" height="60" rx="6"/><text x="562" y="155">Wikidata</text><text class="sub" x="562" y="173">P15001, referenced</text></g>
<g class="note"><text class="start" x="642" y="54">hidden trials</text><text class="start" x="642" y="164">or hold, with reason</text></g>
<g class="lines"><path d="M154,25 C175,25 175,100 190,103" marker-end="url(#ar)"/><path d="M154,65 C175,65 175,103 190,104" marker-end="url(#ar)"/>
<path d="M154,105 L190,105" marker-end="url(#ar)"/><path d="M154,145 C175,145 175,107 190,106" marker-end="url(#ar)"/>
<path d="M154,185 C175,185 175,110 190,107" marker-end="url(#ar)"/><path d="M320,105 L335,105" marker-end="url(#ar)"/>
<path d="M475,95 C485,95 485,50 495,50" marker-end="url(#ar)"/><path d="M475,115 C485,115 485,160 495,160" marker-end="url(#ar)"/></g></svg>""",
    "zoliflodacin": """<svg class="diagram" viewBox="0 0 760 130" role="img">
<title>One substance, three names: AZD0914, ETX0914, zoliflodacin</title>
<defs><marker id="ar2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="arrowhead" d="M0,0 L10,5 L0,10 z"/></marker></defs>
<g class="step"><rect x="10" y="10" width="200" height="56" rx="6"/><text x="110" y="34">AZD0914</text><text class="sub" x="110" y="52">AstraZeneca</text>
<rect x="280" y="10" width="200" height="56" rx="6"/><text x="380" y="34">ETX0914</text><text class="sub" x="380" y="52">Entasis Therapeutics</text>
<rect x="550" y="10" width="200" height="56" rx="6"/><text x="650" y="34">zoliflodacin</text><text class="sub" x="650" y="52">INN; Nuzolvence</text></g>
<g class="lines"><path d="M210,38 L280,38" marker-end="url(#ar2)"/><path d="M480,38 L550,38" marker-end="url(#ar2)"/></g>
<g class="note"><text x="110" y="90">4 trials name it in</text><text x="110" y="106">the intervention</text>
<text x="380" y="90">in trial descriptions only,</text><text x="380" y="106">not in searched fields</text>
<text x="650" y="90">a search on the INN</text><text x="650" y="106">misses 5 of 9 trials</text></g></svg>""",
}


def render_placeholder(spec, meta):
    kind, _, arg = spec.partition(":")
    args = arg.split()
    run_id = meta.get("data")
    if kind == "diagram":
        return DIAGRAMS[args[0]]
    if kind == "chart":
        assert run_id, f"{meta['slug']}: chart needs 'data' in front matter"
        name, collection = args
        if name == "per_drug":
            return svg_per_drug(run_id, collection)
        return svg_shares(run_id, name, collection, {"by_phase": "phase", "by_start": "period"}[name])
    if kind == "stats":
        assert run_id, f"{meta['slug']}: stats needs 'data' in front matter"
        return {"trials_2025": stats_trials_2025}[args[0]](run_id)
    if kind == "table":
        if args[0] == "outcome":
            # A post pins its batch files in front matter; a living page shows all batches
            return table_outcome(meta.get("batches"))
        return {"decisions": table_decisions}[args[0]]()
    if kind == "notes":
        return note_list()
    raise ValueError(f"unknown placeholder {{{{{spec}}}}} in {meta['slug']}")


def to_html(body, meta, depth):
    out = markdown.markdown(body, extensions=["tables", "fenced_code", "attr_list", "md_in_html"])
    out = re.sub(r"<table>(.*?)</table>", r'<div class="tablewrap"><table>\1</table></div>', out, flags=re.S)
    out = re.sub(r"<p>\{\{(.+?)\}\}</p>", lambda m: render_placeholder(m.group(1), meta), out)
    out = out.replace('href="repo:', f'href="{REPO_URL}/')
    # Relative links are written as they resolve from the page: posts link to pages with ../, to posts directly
    for target in re.findall(r'href="([^":#]+\.html)"', out):
        resolved = os.path.normpath(os.path.join(DOCS, "notes" if depth else "", target))
        LINKS.append((meta["slug"], target, resolved))
    assert "{{" not in out, f"{meta['slug']}: placeholder not on its own line"
    return out


# ------------------------------------------------------------------ pages
NAV = [("index.html", "Field notes"), ("method.html", "Method"), ("decisions.html", "Publication decisions"),
       ("identity.html", "Identity findings"), ("collections.html", "Collections")]
NOTES = []
LINKS = []


def note_list():
    items = []
    for meta, _ in reversed(NOTES):  # latest note first
        items.append(f'<li><span class="post-meta">Field note {meta["number"]} · covers {esc(meta["covers"])}</span>'
                     f'<a class="post-title" href="notes/{meta["slug"]}.html">{esc(meta["title"])}</a>'
                     f'<span class="post-summary">{esc(meta["description"])}</span></li>')
    return '<ul class="posts">' + "".join(items) + "</ul>"


def write_page(path, meta, content, current, depth=0):
    pre = "../" * depth
    nav = " ".join(f'<a href="{pre}{f}"{" aria-current=page" if f == current else ""}>{esc(t)}</a>' for f, t in NAV)
    header = written = ""
    if "number" in meta:
        header = f'<p class="post-meta">Field note {meta["number"]} · covers {esc(meta["covers"])}</p>'
        written = f'<p class="written">Written {esc(meta["written"])}.</p>'
    title = meta["title"] if meta["title"] == SITE_TITLE else f'{meta["title"]} — {SITE_TITLE}'
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(meta['description'])}">
<link rel="stylesheet" href="{pre}style.css">
</head>
<body>
<header class="site"><div class="wrap">
<a class="brand" href="{pre}index.html">{SITE_TITLE}</a>
<nav>{nav}</nav>
</div></header>
<main class="wrap">
{header}
{content}
{written}
</main>
<footer class="site"><div class="wrap">
<p>Kerstin Forsberg. Text and data CC BY 4.0; code MIT. Developed with Claude (Anthropic); review decisions and
published codes are confirmed by a person. Source: <a href="https://github.com/kerfors/development-code-archaeology">kerfors/development-code-archaeology</a>.</p>
</div></footer>
</body>
</html>
"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)


def main():
    os.makedirs(DOCS, exist_ok=True)
    # docs/ holds generated pages only: remove earlier HTML so a renamed source leaves no stale page
    for old in glob.glob(os.path.join(DOCS, "*.html")) + glob.glob(os.path.join(DOCS, "notes", "*.html")):
        os.remove(old)
    shutil.copy(os.path.join(SITE, "style.css"), os.path.join(DOCS, "style.css"))
    shutil.copytree(os.path.join(SITE, "images"), os.path.join(DOCS, "images"), dirs_exist_ok=True)
    open(os.path.join(DOCS, ".nojekyll"), "w").close()

    for path in glob.glob(os.path.join(SITE, "notes", "*.md")):
        meta, body = read_source(path)
        for key in ["number", "covers", "written"]:
            assert key in meta, f"{path}: field note front matter lacks '{key}'"
        meta["written"] = str(meta["written"])
        NOTES.append((meta, body))
    NOTES.sort(key=lambda n: n[0]["number"])
    assert [m["number"] for m, _ in NOTES] == list(range(len(NOTES))), "field notes must be numbered 0, 1, 2, ..."
    for meta, body in NOTES:
        write_page(os.path.join(DOCS, "notes", f"{meta['slug']}.html"), meta, to_html(body, meta, 1), "", depth=1)

    for path in glob.glob(os.path.join(SITE, "pages", "*.md")):
        meta, body = read_source(path)
        write_page(os.path.join(DOCS, f"{meta['slug']}.html"), meta, to_html(body, meta, 0), f"{meta['slug']}.html")

    broken = [(src, t) for src, t, resolved in LINKS if not os.path.isfile(resolved)]
    assert not broken, f"links to pages that were not built: {broken}"
    written = sorted(os.path.relpath(p, DOCS) for p in glob.glob(os.path.join(DOCS, "**", "*.html"), recursive=True))
    print(f"{len(NOTES)} field notes; pages written to docs/: {written}")


if __name__ == "__main__":
    main()
