"""Render a synthetic Markdown document to PDF (A4) with WeasyPrint.

Usage: DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib python3 tools/render_pdf.py <in.md> <out.pdf>

A deliberately small Markdown subset: #/##/### headings, paragraphs,
**bold**, *italic*, > blockquote, - lists, pipe tables, --- rules.
No third-party Markdown package is used (sandbox has no package access).
"""
import html, re, sys
from pathlib import Path

CSS = """
@page { size: A4; margin: 22mm 20mm 22mm 20mm;
  @bottom-center { content: counter(page) " / " counter(pages); font: 9pt Georgia, serif; color: #666; } }
body { font: 10.5pt/1.45 Georgia, "Times New Roman", serif; color: #111; }
h1 { font-size: 17pt; margin: 0 0 6pt; line-height: 1.2; }
h2 { font-size: 12.5pt; margin: 16pt 0 5pt; page-break-after: avoid; }
h3 { font-size: 11pt; margin: 12pt 0 4pt; page-break-after: avoid; }
p { margin: 0 0 7pt; text-align: justify; }
blockquote { margin: 0 0 9pt; padding: 5pt 9pt; border-left: 2.5pt solid #999; color: #444; font-size: 9.5pt; }
.synthetic { background: #f3f0e6; border: 0.6pt solid #b8ad8a; padding: 5pt 8pt; font-size: 9pt; margin: 0 0 12pt; }
table { border-collapse: collapse; width: 100%; table-layout: fixed; margin: 6pt 0 10pt; font-size: 9.5pt; page-break-inside: auto; }
th, td { border: 0.5pt solid #999; padding: 3pt 5pt; vertical-align: top; text-align: left; }
th { background: #eee; }
ul, ol { margin: 0 0 7pt 16pt; padding: 0; }
li { margin: 0 0 3pt; }
p.toc { margin: 0 0 2pt 12pt; text-align: left; }
p.sub { margin: 0 0 5pt 14pt; }
hr { border: 0; border-top: 0.6pt solid #999; margin: 12pt 0; }
"""
SYNTH = "Synthetic document, written to demonstrate a method."


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", s)
    return s


def table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r":?-{2,}:?", c or "-") for c in r)]
    ncol = max(len(r) for r in cells)
    widths = {1: [100], 2: [30, 70], 3: [22, 58, 20], 4: [8, 22, 50, 20]}.get(ncol, [100 // ncol] * ncol)
    cols = "".join(f'<col style="width:{w}%">' for w in widths)
    out = [f"<table><colgroup>{cols}</colgroup>"]
    for i, r in enumerate(cells):
        tag = "th" if i == 0 else "td"
        out.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in r + [""] * (ncol - len(r))) + "</tr>")
    out.append("</table>")
    return "\n".join(out)


def md_to_html(text):
    out, para, lst, tbl = [], [], [], []

    def flush():
        nonlocal para, lst, tbl
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>"); para = []
        if lst:
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in lst) + "</ul>"); lst = []
        if tbl:
            out.append(table(tbl)); tbl = []

    for line in text.splitlines():
        s = line.rstrip()
        if not s.strip():
            flush(); continue
        if s.startswith("|"):
            if para or lst: flush()
            tbl.append(s); continue
        if tbl: flush()
        m = re.match(r"^(#{1,3})\s+(.*)", s)
        if m:
            flush(); out.append(f"<h{len(m.group(1))}>{inline(m.group(2))}</h{len(m.group(1))}>"); continue
        if s.strip() == "---":
            flush(); out.append("<hr>"); continue
        if s.startswith("> "):
            flush(); out.append(f"<blockquote>{inline(s[2:])}</blockquote>"); continue
        m = re.match(r"^\s*[-*]\s+(.*)", s)
        if m and not para:
            lst.append(m.group(1)); continue
        m = re.match(r"^(\d{1,2})\.\s+(.*)", s)
        if m and not re.match(r"^\d{1,2}\.\d", s):
            flush(); out.append(f'<p class="toc">{m.group(1)}. {inline(m.group(2))}</p>'); continue
        if re.match(r"^\([a-z]{1,3}\)\s", s) or re.match(r"^\(\d{1,2}\)\s", s):
            flush(); out.append(f'<p class="sub">{inline(s)}</p>'); continue
        if lst: flush()
        if s.startswith(SYNTH):
            flush(); out.append(f'<p class="synthetic">{inline(s)}</p>'); continue
        if s.startswith("**") and para:
            flush()
        para.append(s.strip())
        if s.startswith("**"):
            flush()
    flush()
    return "\n".join(out)


def main(src, dst):
    from weasyprint import HTML, CSS as WCSS
    body = md_to_html(Path(src).read_text())
    title = re.search(r"<h1>(.*?)</h1>", body)
    doc = f"<!doctype html><html><head><meta charset='utf-8'><title>{title.group(1) if title else Path(src).stem}</title></head><body>{body}</body></html>"
    HTML(string=doc).write_pdf(dst, stylesheets=[WCSS(string=CSS)])
    print(dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
