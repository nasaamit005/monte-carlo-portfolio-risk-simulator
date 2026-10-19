
from pathlib import Path
import html

import markdown

# ============================================================
# PROJECT PATHS
# ============================================================
ROOT = Path(__file__).resolve().parents[1]
MC_DIR = ROOT / "reports" / "monte_carlo"
DOCS_DIR = ROOT / "docs"

# Professional color palette
NAVY = "#12345A"
BLUE = "#2563EB"
TEAL = "#0F766E"
PURPLE = "#7C3AED"
TEXT = "#263449"
BORDER = "#D6E2F0"
PALE_BLUE = "#EFF6FF"
PALE_TEAL = "#F0FDFA"

# ============================================================
# DOCUMENTS TO FORMAT
# Original Markdown files are preserved.
# ============================================================
DOCUMENTS = [
    {
        "source": MC_DIR / "monte_carlo_analysis_report.md",
        "output": MC_DIR / "monte_carlo_analysis_report.html",
        "title": "Monte Carlo Portfolio Risk — Analysis Report",
        "subtitle": (
            "Simulation results, interpretation, risk metrics, "
            "and business value"
        ),
        "accent": BLUE,
    },
    {
        "source": DOCS_DIR / "MONTE_CARLO_METHODOLOGY.md",
        "output": DOCS_DIR / "MONTE_CARLO_METHODOLOGY.html",
        "title": "Monte Carlo Portfolio Risk — Methodology",
        "subtitle": (
            "Mathematical framework, model assumptions, "
            "and validation approach"
        ),
        "accent": TEAL,
    },
    {
        "source": DOCS_DIR / "REFERENCES.md",
        "output": DOCS_DIR / "REFERENCES.html",
        "title": "Research References",
        "subtitle": (
            "Academic foundations and research-to-code mapping"
        ),
        "accent": PURPLE,
    },
]

# ============================================================
# STYLESHEET
# This is a regular string, not an f-string.
# CSS braces therefore do not cause Python syntax errors.
# ============================================================
CSS_TEMPLATE = r"""
:root {
    --navy: __NAVY__;
    --accent: __ACCENT__;
    --text: __TEXT__;
    --muted: #5C6B80;
    --border: __BORDER__;
    --pale-blue: __PALE_BLUE__;
    --pale-teal: __PALE_TEAL__;
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    background: #F2F5FA;
    color: var(--text);
    font-family: "Times New Roman", Times, serif;
    font-size: 12pt;
    line-height: 1.65;
}

.hero {
    color: white;
    background: linear-gradient(120deg, var(--navy), var(--accent));
    padding: 35px 24px;
    border-bottom: 5px solid var(--accent);
}

.hero-inner {
    max-width: 1050px;
    margin: 0 auto;
}

.eyebrow {
    font-family: Arial, sans-serif;
    font-size: 10pt;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #DCEAFE;
}

.hero h1 {
    font-family: "Times New Roman", Times, serif;
    font-size: 28pt;
    line-height: 1.2;
    margin: 10px 0;
    color: white;
}

.hero p {
    margin: 0;
    color: #E6EDF8;
    font-size: 12pt;
}

main {
    max-width: 1050px;
    margin: 26px auto 35px;
    background: white;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 34px 42px;
    box-shadow: 0 8px 28px rgba(18, 52, 90, 0.07);
}

h1, h2, h3, h4 {
    font-family: "Times New Roman", Times, serif;
    line-height: 1.3;
    break-after: avoid;
}

main h1 {
    color: var(--navy);
    font-size: 23pt;
}

h2 {
    color: var(--navy);
    font-size: 18pt;
    margin-top: 30px;
    margin-bottom: 15px;
    padding: 9px 13px;
    border-left: 5px solid var(--accent);
    border-bottom: 1px solid var(--border);
    background: var(--pale-blue);
}

h3 {
    color: var(--accent);
    font-size: 14pt;
    margin-top: 22px;
}

h4 {
    color: var(--navy);
    font-size: 12pt;
}

p, li {
    font-size: 12pt;
}

li {
    margin-bottom: 5px;
}

a {
    color: var(--accent);
    overflow-wrap: anywhere;
}

a:hover {
    text-decoration: underline;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 18px 0 24px;
    font-size: 11pt;
}

thead th, th {
    background: var(--navy);
    color: white;
    font-weight: bold;
    text-align: left;
}

th, td {
    border: 1px solid var(--border);
    padding: 9px 11px;
    vertical-align: top;
}

tbody tr:nth-child(even) {
    background: var(--pale-blue);
}

tbody tr:nth-child(odd) {
    background: #FFFFFF;
}

blockquote {
    margin: 22px 0;
    padding: 13px 20px;
    background: var(--pale-teal);
    border-left: 5px solid var(--teal, #0F766E);
}

code {
    font-family: Consolas, "Courier New", monospace;
    font-size: 10pt;
    background: #EDF2F7;
    padding: 2px 5px;
    border-radius: 4px;
    overflow-wrap: anywhere;
}

pre {
    background: #132238;
    color: #F0F6FF;
    padding: 17px;
    border-radius: 8px;
    overflow-x: auto;
    white-space: pre-wrap;
}

pre code {
    background: transparent;
    color: inherit;
}

hr {
    border: 0;
    border-top: 1px solid var(--border);
    margin: 28px 0;
}

mjx-container {
    color: #142D4E;
    max-width: 100%;
}

mjx-container[display="true"] {
    overflow-x: auto;
    overflow-y: hidden;
    padding: 14px 10px;
    margin: 18px 0 !important;
    background: #F1F7FF;
    border: 1px solid #D5E5FB;
    border-radius: 8px;
}

.actions {
    max-width: 1050px;
    margin: 18px auto 0;
    padding: 0 8px;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.actions button {
    font-family: Arial, sans-serif;
    font-size: 10pt;
    border: 1px solid var(--border);
    background: white;
    color: var(--navy);
    padding: 10px 15px;
    border-radius: 7px;
    cursor: pointer;
}

.actions button:hover {
    background: var(--pale-blue);
}

footer {
    max-width: 1050px;
    margin: 0 auto;
    color: var(--muted);
    padding: 0 20px 28px;
    font-size: 10pt;
    text-align: center;
}

@media (max-width: 700px) {
    main {
        margin: 12px;
        padding: 20px 17px;
    }

    .hero {
        padding: 25px 18px;
    }

    .hero h1 {
        font-size: 23pt;
    }

    table {
        display: block;
        overflow-x: auto;
    }
}

@page {
    size: A4;
    margin: 18mm 16mm;
}

@media print {
    body {
        background: white;
        font-size: 12pt;
    }

    .hero {
        background: white !important;
        color: var(--navy) !important;
        padding: 0 0 15px;
        border-bottom: 2px solid var(--accent);
    }

    .hero h1 {
        color: var(--navy);
    }

    .hero p, .eyebrow {
        color: var(--navy);
    }

    main {
        max-width: none;
        margin: 0;
        padding: 15px 0;
        box-shadow: none;
        border: 0;
    }

    .actions {
        display: none;
    }

    h2, h3 {
        break-after: avoid;
    }

    tr, blockquote {
        break-inside: avoid;
    }

    a {
        color: var(--navy);
        text-decoration: none;
    }

    table {
        font-size: 10pt;
    }
}
"""


# ============================================================
# HTML TEMPLATE
# Also a regular string: JavaScript and CSS braces are safe.
# ============================================================
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>__TITLE__</title>

<style>
__CSS__
</style>

<script>
window.MathJax = {
  tex: {
    inlineMath: [['\\(', '\\)'], ['$', '$']],
    displayMath: [['\\[', '\\]'], ['$$', '$$']],
    processEscapes: true
  },
  options: {
    skipHtmlTags: [
      'script', 'noscript', 'style', 'textarea', 'pre', 'code'
    ]
  }
};
</script>

<script
  defer
  src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
</script>

</head>
<body>

<header class="hero">
  <div class="hero-inner">
    <div class="eyebrow">
      Quantitative Finance · Research &amp; Analytics
    </div>
    <h1>__TITLE__</h1>
    <p>__SUBTITLE__</p>
  </div>
</header>

<div class="actions">
  <button type="button" onclick="window.print()">
    Print / Save as PDF
  </button>
  <button
    type="button"
    onclick="window.scrollTo({top: 0, behavior: 'smooth'})">
    Back to top
  </button>
</div>

<main>
__BODY__
</main>

<footer>
  Monte Carlo Portfolio Risk Simulator ·
  Educational analysis, not investment advice
</footer>

</body>
</html>
"""


def build_css(accent):
    """Replace named placeholders without using f-string interpolation."""
    replacements = {
        "__NAVY__": NAVY,
        "__ACCENT__": accent,
        "__TEXT__": TEXT,
        "__BORDER__": BORDER,
        "__PALE_BLUE__": PALE_BLUE,
        "__PALE_TEAL__": PALE_TEAL,
    }

    css = CSS_TEMPLATE
    for placeholder, value in replacements.items():
        css = css.replace(placeholder, value)

    return css


def markdown_to_html(source_path):
    """Convert Markdown to HTML while preserving LaTeX delimiters."""
    source_text = source_path.read_text(encoding="utf-8")

    return markdown.markdown(
        source_text,
        extensions=[
            "tables",
            "fenced_code",
            "toc",
            "sane_lists",
        ],
        output_format="html5",
    )


def render_document(item):
    """Create one formatted HTML document from its Markdown source."""
    source_path = item["source"]
    output_path = item["output"]

    if not source_path.exists():
        raise FileNotFoundError(
            f"Source document not found:\n{source_path}\n\n"
            "Run the Monte Carlo dashboard/documentation generator first."
        )

    body = markdown_to_html(source_path)
    css = build_css(item["accent"])

    # HTML escaping is used for metadata only.
    # Body is generated HTML from our own Markdown files.
    replacements = {
        "__TITLE__": html.escape(item["title"]),
        "__SUBTITLE__": html.escape(item["subtitle"]),
        "__CSS__": css,
        "__BODY__": body,
    }

    document = HTML_TEMPLATE
    for placeholder, value in replacements.items():
        document = document.replace(placeholder, value)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")

    print(f"Created: {output_path}")


def update_dashboard_links():
    """Point the dashboard documentation links to formatted HTML files."""
    dashboard_path = MC_DIR / "monte_carlo_dashboard.html"

    if not dashboard_path.exists():
        print(
            "Note: Combined dashboard not found; "
            "skipping dashboard link updates."
        )
        return

    dashboard = dashboard_path.read_text(encoding="utf-8")

    link_replacements = {
        'href="monte_carlo_analysis_report.md"':
            'href="monte_carlo_analysis_report.html"',
        'href="../../docs/MONTE_CARLO_METHODOLOGY.md"':
            'href="../../docs/MONTE_CARLO_METHODOLOGY.html"',
        'href="../../docs/REFERENCES.md"':
            'href="../../docs/REFERENCES.html"',
    }

    for old_link, new_link in link_replacements.items():
        dashboard = dashboard.replace(old_link, new_link)

    dashboard_path.write_text(dashboard, encoding="utf-8")
    print(f"Updated report links: {dashboard_path}")


def main():
    print("FORMATTING MONTE CARLO DOCUMENTS")
    print("=" * 55)

    for item in DOCUMENTS:
        render_document(item)

    update_dashboard_links()

    print("\nFORMATTING COMPLETE")
    print("Body font: Times New Roman, 12 pt")
    print("Headings: colored, numbered structure retained from Markdown")
    print("Tables: colored headers and alternating row backgrounds")
    print("Equations: MathJax LaTeX rendering")
    print("Print support: A4 page layout")
    print("\nOriginal Markdown files have not been modified.")


if __name__ == "__main__":
    main()
