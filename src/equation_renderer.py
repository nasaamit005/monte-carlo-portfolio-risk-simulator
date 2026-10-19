
import re
from html import escape

from latex2mathml.converter import convert


def render_equation(latex, display=False):
    """Convert a LaTeX expression into browser-renderable MathML."""
    latex = latex.strip()

    if not latex:
        return ""

    try:
        mathml = convert(latex)
        display_style = "block" if display else "inline"

        return (
            f'<math xmlns="http://www.w3.org/1998/Math/MathML" '
            f'display="{display_style}">'
            f'{mathml.split(">", 1)[1]}'
        )
    except Exception:
        # Keep a readable fallback rather than silently losing a formula.
        return (
            '<span class="equation-fallback">'
            + escape(latex)
            + "</span>"
        )


def render_math(text):
    """Render display and inline math before Markdown conversion."""

    # Protect fenced code blocks so formulas inside code aren't changed.
    code_blocks = []

    def save_code(match):
        code_blocks.append(match.group(0))
        return f"@@CODEBLOCK{len(code_blocks) - 1}@@"

    text = re.sub(
        r"```[\s\S]*?```",
        save_code,
        text,
    )

    # Display equations: \[...\] and $$...$$
    display_patterns = [
        r"\\\[([\s\S]*?)\\\]",
        r"\$\$([\s\S]*?)\$\$",
    ]

    for pattern in display_patterns:
        text = re.sub(
            pattern,
            lambda m: render_equation(m.group(1), display=True),
            text,
        )

    # Inline equations: \(...\) and $...$
    text = re.sub(
        r"\\\(([\s\S]*?)\\\)",
        lambda m: render_equation(m.group(1)),
        text,
    )

    text = re.sub(
        r"(?<!\$)\$([^$\n]+)\$(?!\$)",
        lambda m: render_equation(m.group(1)),
        text,
    )

    # Restore the original fenced code blocks.
    for i, block in enumerate(code_blocks):
        text = text.replace(f"@@CODEBLOCK{i}@@", block)

    return text
