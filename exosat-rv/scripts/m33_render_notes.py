"""M33: render the Markdown notes as journal-styled HTML so they can be read and inspected.

Only the manuscript had a rendered form. The notes -- which are the longer pieces, and the
ones carrying the pre-submission checklists -- existed only as Markdown, so there was no way
to read them the way a referee would.

The stylesheet is NOT duplicated here. It is lifted from `docs/paper/draft.template.html` at
render time, so the manuscript and the notes cannot drift apart typographically: change the
manuscript's style block and every note follows on the next run. Only the handful of elements
Markdown produces and the hand-written manuscript does not -- lists, blockquotes, horizontal
rules, strikethrough, inline code -- are added on top.

Usage: python scripts/m33_render_notes.py
"""
import io
import os
import re

from markdown_it import MarkdownIt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER = os.path.join(ROOT, "docs", "paper")
TEMPLATE = os.path.join(PAPER, "draft.template.html")
NL = chr(10)

NOTES = [
    ("rnaas-etatel-draft.md", "First Radial-Velocity Constraints on eta Telescopii B",
     "Research Note draft - NOT SUBMITTED"),
    ("contrast-wall-note.md", "First resolve, then worry about contrast",
     "Working note - not submitted"),
    ("methods-note.md", "Flat is not quiet",
     "Working note - not submitted"),
    ("sampler-reproducibility-note.md",
     "A Nested Sampler's Internal Uncertainty Is Not Its Reproducibility",
     "Working note - not submitted"),
]

# Markdown emits elements the hand-written manuscript never uses. These follow the same
# type scale as the lifted stylesheet rather than introducing a second one.
EXTRA_CSS = """
  /* --- elements Markdown produces that the manuscript does not ------------- */
  .sheet ul, .sheet ol { margin: 0 0 10px; padding-left: 1.6em; }
  .sheet li { margin: 0 0 4px; text-indent: 0; }
  .sheet li > p { text-indent: 0; margin: 0 0 4px; }
  .sheet blockquote {
    margin: 12px 0; padding: 8px 0 8px 14px;
    border-left: 2px solid var(--hairline);
    color: var(--ink-2); font-size: 14px;
  }
  .sheet blockquote p { text-indent: 0; }
  .sheet hr { border: 0; border-top: 0.6px solid var(--hairline); margin: 22px 0; }
  .sheet del { color: var(--muted); }
  .sheet h1 + p, .sheet h2 + p, .sheet h3 + p { text-indent: 0; }
  .sheet table { margin: 12px 0; }
  .sheet code { background: rgba(0,0,0,.035); padding: 0 3px; border-radius: 2px; }
  .sheet a { color: var(--us); text-decoration: none; border-bottom: 0.5px solid currentColor; }
  .notebar {
    font-family: var(--sans); font-size: 9.5px; letter-spacing: .16em;
    text-transform: uppercase; color: var(--draft);
    border: 1px solid currentColor; display: inline-block;
    padding: 2px 8px; margin: 0 0 20px;
  }
"""


def journal_css():
    """Lift the manuscript's <style> block so the two cannot drift apart."""
    html = io.open(TEMPLATE, encoding="utf-8").read()
    m = re.search(r"<style>.*?</style>", html, re.S)
    if not m:
        raise SystemExit("no <style> block in the manuscript template")
    return m.group()[: -len("</style>")] + EXTRA_CSS + "</style>"


# A leading heading that is really a status line duplicates the banner this renderer
# already emits, and pushes the actual paper title down into the body where it reads as
# prose. Where that happens the configured title is promoted instead.
def _promote_title(src, title):
    """Replace a leading status-line heading with the real title.

    A first heading like "# DRAFT - ... NOT SUBMITTED" duplicates the banner this
    renderer already emits and pushes the actual title down into the body, where it
    reads as prose. Done with string operations rather than a regex because the
    pattern is trivial and a regex here is one more thing to get wrong.
    """
    lines = src.split(NL)
    if not lines:
        return src
    head = lines[0].strip()
    if head.startswith("# ") and head[2:].lstrip().lower().startswith(("draft", "status")):
        lines[0] = "# " + title
    return NL.join(lines)


def render(md_name, title, banner, css):
    src = _promote_title(io.open(os.path.join(PAPER, md_name), encoding="utf-8").read(),
                         title)
    md = MarkdownIt("commonmark", {"html": True, "typographer": True})
    md.enable(["table", "strikethrough"])
    body = md.render(src)
    out = (f"<title>{title} - draft</title>\n{css}\n\n"
           f'<div class="sheet">\n<div class="notebar">{banner}</div>\n{body}\n</div>\n')
    dest = os.path.join(PAPER, md_name.replace(".md", ".html"))
    io.open(dest, "w", encoding="utf-8", newline="\n").write(out)
    return dest, len(out)


def main():
    css = journal_css()
    print("# rendering the Markdown notes with the manuscript's own stylesheet\n")
    for name, title, banner in NOTES:
        if not os.path.exists(os.path.join(PAPER, name)):
            print(f"  {name:<40s} MISSING")
            continue
        dest, n = render(name, title, banner, css)
        print(f"  {os.path.basename(dest):<40s} {n/1024:7.1f} kB")
    print("\n# The .md files remain the source. These are build products: re-run after any")
    print("# edit, and never hand-edit the HTML, exactly as with the manuscript.")


if __name__ == "__main__":
    main()
