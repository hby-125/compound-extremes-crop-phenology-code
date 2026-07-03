# -*- coding: utf-8 -*-
"""Compile v2 markdown to NCC-style PDF via tectonic. Reuses the build pipeline
from build_submission.py with adjustments for the Liu Dingyu paper's structure."""

import os, re, sys, shutil, subprocess
from pathlib import Path

# ---- Path configuration ----
# NOTE: This script compiles the manuscript PDF via Tectonic LaTeX.
# It requires: (1) the manuscript markdown, (2) figure PDFs, (3) tectonic executable.
# Set the environment variables below or edit paths directly.
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = Path(os.environ.get("OUTPUTS_DIR", REPO_ROOT / "outputs"))
ROOT = Path(os.environ.get("MANUSCRIPT_DIR", REPO_ROOT / "manuscript"))
V3 = ROOT / "01_完整手稿_NCC版式_v3.md"
OUT = OUTPUTS / "manuscript_pdf"
OUT.mkdir(exist_ok=True)
FIG = OUTPUTS / "figures"
# Tectonic LaTeX engine (install from https://tectonic-typesetting.github.io)
TECT = Path(os.environ.get("TECTONIC_PATH", "tectonic"))
# Fallback figure source (figures/ in manuscript dir)
V1_FIG = Path(os.environ.get("V1_FIG_DIR", str(ROOT / "figures")))

# Copy figures (ED Fig 1 from v2; main figs 1-4 from v1)
(OUT / "figures").mkdir(exist_ok=True)
for src in V1_FIG.glob("*.pdf"):
    shutil.copy(src, OUT / "figures" / src.name)
for src in FIG.glob("Extended_Data_Figure_1.pdf"):
    shutil.copy(src, OUT / "figures" / src.name)
print("figures copied")

text = V3.read_text(encoding="utf-8")
# Strip HTML comments
text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

# ---------- Parser (block list) ----------
def parse_blocks(t):
    t = t.replace("\r\n", "\n").strip()
    lines = t.split("\n")
    blocks = []; i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s: i += 1; continue
        if re.fullmatch(r'-{3,}', s):
            blocks.append(("hr", None)); i += 1; continue
        m = re.match(r'^(#+)\s+(.*)$', s)
        if m:
            blocks.append((f"h{len(m.group(1))}", m.group(2))); i += 1; continue
        if s.startswith(">"):
            bq = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                bq.append(lines[i].strip().lstrip("> ").rstrip()); i += 1
            blocks.append(("blockquote", "\n".join(bq))); continue
        if s.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:]); i += 1
            blocks.append(("list", items)); continue
        if s.startswith("|"):
            tbl = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl.append(lines[i].rstrip()); i += 1
            blocks.append(("table", tbl)); continue
        para = [s]; i += 1
        while i < len(lines):
            ns = lines[i].strip()
            if not ns: break
            if re.match(r'^#+\s', ns) or ns.startswith(("|",">","- ")) or re.fullmatch(r'-{3,}', ns):
                break
            para.append(ns); i += 1
        blocks.append(("paragraph", " ".join(para)))
    return blocks

BLOCKS = parse_blocks(text)
print(f"parsed {len(BLOCKS)} blocks")

# ---------- Inline markdown → LaTeX ----------
def md_to_latex(s):
    placeholders = []
    def stash(m):
        placeholders.append(m.group(1)); return f"\x00{len(placeholders)-1}\x00"
    s = re.sub(r'`([^`]+)`', stash, s)
    s = s.replace(r'\*', '\x02')
    # superscripts: <sup>X</sup> -> \textsuperscript{X}
    s = re.sub(r'<sup>([^<]+)</sup>', r'\\textsuperscript{\1}', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\\textit{\1}', s)
    s = s.replace('\x02', '*')
    s = re.sub(r'(?<!\\)&', r'\\&', s)
    s = re.sub(r'(?<!\\)%', r'\\%', s)
    s = re.sub(r'(?<!\\)#', r'\\#', s)
    parts = re.split(r'(\$[^$]+\$)', s)
    for j in range(0, len(parts), 2):
        parts[j] = re.sub(r'(?<!\\)_', r'\\_', parts[j])
    s = "".join(parts)
    # Restore code
    def unstash(m):
        idx = int(m.group(1))
        return r'\texttt{' + placeholders[idx].replace("_", r"\_") + r'}'
    s = re.sub(r'\x00(\d+)\x00', unstash, s)
    # Unicode arrows
    s = s.replace("→", r"$\rightarrow$").replace("←", r"$\leftarrow$")
    s = s.replace("≥", r"$\geq$").replace("≤", r"$\leq$").replace("≈", r"$\approx$")
    s = s.replace("×", r"$\times$")
    s = s.replace("±", r"$\pm$")
    s = s.replace("°", r"$^{\circ}$")
    s = s.replace("⁻¹", r"$^{-1}$")
    s = s.replace("²", r"$^{2}$")
    s = s.replace("³", r"$^{3}$")
    return s

# ---------- Table renderer ----------
def parse_md_table(lines):
    rows = []
    for ln in lines:
        ln = ln.strip()
        if not ln.startswith("|"): continue
        inner = ln[1:-1] if ln.endswith("|") else ln[1:]
        cells = [c.strip() for c in inner.split("|")]
        rows.append(cells)
    if len(rows) >= 2 and all(re.fullmatch(r':?-+:?', c) for c in rows[1]):
        return rows[0], rows[2:]
    return rows[0], rows[1:]

def latex_table(title, header, rows, notes=None):
    n = len(header)
    def make_cell(c):
        c = c.strip()
        if not c: return ""
        # split coef and (se)
        m = re.match(r'^(.*?)\s+(\([^)]+\))$', c)
        if m:
            return r"\makecell{" + md_to_latex(m.group(1)) + r"\\" + md_to_latex(m.group(2)) + "}"
        return md_to_latex(c)
    head = " & ".join(r"\textbf{" + md_to_latex(h) + r"}" for h in header) + r" \\"
    body = []
    for r in rows:
        r = list(r) + [""] * (n - len(r))
        cells = " & ".join(make_cell(c) for c in r[:n])
        body.append(cells + r" \\")
    cols = "l" + "c"*(n-1)
    caption = re.sub(r'^\*\*(.+?)\*\*$', r'\1', title.strip()).strip()
    label = "tab:" + re.sub(r'[^a-z0-9]+', '_', caption.lower())[:20]
    notes_block = ""
    if notes:
        cleaned = re.sub(r'^\*Notes[^*]*\*\s*', '', notes.strip())
        cleaned = re.sub(r'^\*([^*]+)\*$', r'\1', cleaned.strip())  # surrounding *...*
        notes_block = (r"\begin{tablenotes}\footnotesize" + "\n" +
                       r"\item " + md_to_latex(cleaned) + "\n" +
                       r"\end{tablenotes}" + "\n")
    is_wide = n >= 5
    tabular = (r"\begin{tabular}{" + cols + r"}" + "\n" +
               r"\toprule" + "\n" + head + "\n" +
               r"\midrule" + "\n" + "\n".join(body) + "\n" +
               r"\bottomrule" + "\n" + r"\end{tabular}")
    if is_wide:
        tabular = r"\resizebox{\textwidth}{!}{%" + "\n" + tabular + "}"
    return (r"\begin{table}[ht]\centering\small" + "\n" +
            r"\caption{" + md_to_latex(caption) + r"}\label{" + label + r"}" + "\n" +
            r"\begin{threeparttable}\setlength{\tabcolsep}{4pt}" + "\n" +
            tabular + "\n" + notes_block + r"\end{threeparttable}\end{table}" + "\n")

# Figure inserts (which figure after which section heading)
FIGS = {
    "Compound extremes carry independent information": ("fig1", "Figure 1 | Compound extremes carry phenological information beyond single indices."),
    "Sharper responses in southern China":              ("fig3", "Figure 3 | North-South divergence in compound-extreme sensitivity on GSL."),
    "Sensitivity intensifies after 2010":               ("fig4", "Figure 4 | Sensitivity to compound extremes shifts over time."),
}
FIG2 = ("fig2", "Figure 2 | Compound extremes advance crop maturity.")

# ---------- Render LaTeX ----------
def is_table_title(s):
    return bool(re.match(r'^\*\*Table\s+\w+\s*\|', s) or re.match(r'^\*\*Extended Data Table\s+\d+\s*\|', s)) or re.match(r'^###\s+(Extended Data )?Table\s+', s)

def render():
    L = []
    L.append(r"\documentclass[11pt,a4paper]{article}")
    L.append(r"\usepackage[utf8]{inputenc}")
    L.append(r"\usepackage[T1]{fontenc}")
    L.append(r"\usepackage{lmodern}")
    L.append(r"\usepackage[margin=2.2cm]{geometry}")
    L.append(r"\usepackage{setspace}\onehalfspacing")
    L.append(r"\usepackage{lineno}")
    L.append(r"\usepackage{graphicx}")
    L.append(r"\usepackage{booktabs}")
    L.append(r"\usepackage{threeparttable}")
    L.append(r"\usepackage{makecell}")
    L.append(r"\usepackage{multirow}")
    L.append(r"\usepackage{amsmath,amssymb}")
    L.append(r"\usepackage[hidelinks]{hyperref}")
    L.append(r"\usepackage{caption}")
    L.append(r"\usepackage{tabularx}")
    L.append(r"\usepackage{enumitem}")
    L.append(r"\usepackage{titlesec}")
    L.append(r"\titleformat{\section}{\large\bfseries}{}{0pt}{}")
    L.append(r"\titleformat{\subsection}{\normalsize\bfseries}{}{0pt}{}")
    L.append(r"\setcounter{secnumdepth}{0}")
    L.append(r"\graphicspath{{figures/}}")
    L.append(r"\linenumbers")
    L.append("")
    L.append(r"\begin{document}")
    L.append("")

    # Walk blocks
    i = 0
    figs_emit = set()
    fig2_emitted = False
    inside_main = False
    while i < len(BLOCKS):
        typ, payload = BLOCKS[i]
        if typ == "h1":
            t = md_to_latex(payload)
            L.append(r"\begin{center}{\LARGE\bfseries " + t + r"\par}\end{center}")
            L.append("")
        elif typ == "h2":
            heading = payload.strip()
            # Skip 'Main display items' wrap section
            if heading == "Main display items":
                # Skip until References
                while i < len(BLOCKS):
                    if BLOCKS[i][0] == "h2" and BLOCKS[i][1].strip() in ("Methods","References","Extended Data"):
                        break
                    i += 1
                continue
            L.append(r"\section*{" + md_to_latex(heading) + "}")
            inside_main = (heading == "Main text")
        elif typ == "h3":
            heading_text = payload.strip()
            # Figure anchor (insert AFTER results subsection heading)
            L.append(r"\subsection*{" + md_to_latex(heading_text) + "}")
            if heading_text in FIGS:
                stem, cap = FIGS[heading_text]
                if stem not in figs_emit:
                    L.append(r"\begin{figure}[t]\centering")
                    L.append(r"\includegraphics[width=0.95\linewidth]{" + stem + r".pdf}")
                    L.append(r"\caption*{" + md_to_latex(cap) + "}")
                    L.append(r"\end{figure}")
                    figs_emit.add(stem)
            # If we're in "Compound extremes carry independent information",
            # also emit Fig 2 (Maturity) since it's referenced there
            if heading_text == "Compound extremes carry independent information" and not fig2_emitted:
                stem, cap = FIG2
                L.append(r"\begin{figure}[t]\centering")
                L.append(r"\includegraphics[width=0.95\linewidth]{" + stem + r".pdf}")
                L.append(r"\caption*{" + md_to_latex(cap) + "}")
                L.append(r"\end{figure}")
                fig2_emitted = True
                figs_emit.add(stem)
        elif typ == "paragraph":
            # Detect table title
            if (payload.lstrip().startswith("**Table ") or
                payload.lstrip().startswith("**Extended Data Table ")):
                # Find table block
                if i+1 < len(BLOCKS) and BLOCKS[i+1][0] == "table":
                    header, rows = parse_md_table(BLOCKS[i+1][1])
                    notes = None
                    if i+2 < len(BLOCKS) and BLOCKS[i+2][0] == "paragraph" and BLOCKS[i+2][1].lstrip("*").startswith(("Notes","Standardized","Dependent","Each","Means","North","Standard","All","Pixel","Crop")):
                        notes = BLOCKS[i+2][1]
                        i += 1
                    L.append(latex_table(payload, header, rows, notes))
                    i += 2
                    continue
            # Detect figure caption (starts with **Figure N |)
            if re.match(r'^\*\*Figure\s+\w+\s*\|', payload.lstrip()):
                # Caption already emitted alongside figure include; suppress duplicate
                pass
            else:
                L.append(md_to_latex(payload))
        elif typ == "blockquote":
            # Equation (Y(i,p,t) = ...) treat as displayed math
            txt = payload.strip()
            if "=" in txt and ("i,p,t" in txt or "α" in txt or "β" in txt):
                body = txt.split("\n")[0].strip(", ")
                body = re.sub(r'([A-Za-zα-ωΑ-Ω])_([A-Za-z0-9,]+)', r'\1_{\2}', body)
                # Convert (i,p,t) subscripts in 'Y(i,p,t)' to 'Y_{i,p,t}'
                body = re.sub(r'([A-Z])\(([a-z,]+)\)', r'\1_{\2}', body)
                L.append(r"\begin{equation}" + "\n" + body + "\n" + r"\end{equation}")
            else:
                L.append(r"\begin{quote}" + md_to_latex(txt) + r"\end{quote}")
        elif typ == "list":
            L.append(r"\begin{itemize}[leftmargin=*,itemsep=2pt,topsep=2pt]")
            for it in payload:
                L.append(r"\item " + md_to_latex(it))
            L.append(r"\end{itemize}")
        elif typ == "hr":
            pass
        elif typ == "table":
            # standalone table without title
            header, rows = parse_md_table(payload)
            L.append(latex_table("**Table.**", header, rows))
        i += 1

    L.append("")
    L.append(r"\end{document}")
    return "\n\n".join(L)

tex = render()
(OUT / "manuscript_v3.tex").write_text(tex, encoding="utf-8")
print(f"LaTeX written: {OUT / 'manuscript_v3.tex'}")
print("Compiling ...")
proc = subprocess.run([str(TECT), "manuscript_v3.tex"], cwd=str(OUT),
                     capture_output=True, text=False)
err = (proc.stderr or b"").decode("utf-8", errors="ignore")
err_t = "\n".join(err.splitlines()[-12:]).encode("ascii", errors="ignore").decode("ascii")
print(err_t)
pdf = OUT / "manuscript_v3.pdf"
if pdf.exists():
    print(f"PDF OK: {pdf} ({pdf.stat().st_size/1024:.0f} KB)")
else:
    print("PDF FAILED")
