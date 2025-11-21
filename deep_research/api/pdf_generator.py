"""
PDF Generation utilities for research reports.

Converts markdown reports to professional PDF documents.
"""

import os
import tempfile
from typing import Optional
from datetime import datetime
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


def markdown_to_html(markdown_text: str, title: str = "Research Report") -> str:
    """
    Convert markdown to styled HTML.

    Args:
        markdown_text: Markdown content
        title: Document title

    Returns:
        Complete HTML document
    """
    # Convert markdown to HTML
    md = markdown.Markdown(extensions=[
        'extra',           # Tables, footnotes, etc.
        'codehilite',      # Code syntax highlighting
        'toc',             # Table of contents
        'sane_lists',      # Better list handling
        'nl2br',           # Newline to <br>
    ])

    content_html = md.convert(markdown_text)

    # Create full HTML document with styling
    html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        @page {{
            size: A4;
            margin: 2.5cm 2cm;
            @bottom-right {{
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10pt;
                color: #666;
            }}
        }}

        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #1A202C;
            max-width: 800px;
            margin: 0 auto;
        }}

        h1 {{
            font-size: 24pt;
            font-weight: 600;
            color: #1A202C;
            margin-top: 0;
            margin-bottom: 0.5em;
            padding-bottom: 0.3em;
            border-bottom: 2px solid #3182CE;
        }}

        h2 {{
            font-size: 18pt;
            font-weight: 600;
            color: #2D3748;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            page-break-after: avoid;
        }}

        h3 {{
            font-size: 14pt;
            font-weight: 600;
            color: #4A5568;
            margin-top: 1.2em;
            margin-bottom: 0.4em;
            page-break-after: avoid;
        }}

        p {{
            margin-bottom: 0.8em;
            text-align: justify;
        }}

        ul, ol {{
            margin-bottom: 1em;
            padding-left: 1.5em;
        }}

        li {{
            margin-bottom: 0.3em;
        }}

        blockquote {{
            margin: 1em 0;
            padding: 0.5em 1em;
            border-left: 4px solid #3182CE;
            background-color: #F7FAFC;
            font-style: italic;
        }}

        code {{
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
            background-color: #F7FAFC;
            padding: 0.2em 0.4em;
            border-radius: 3px;
        }}

        pre {{
            background-color: #F7FAFC;
            padding: 1em;
            border-radius: 5px;
            overflow-x: auto;
            page-break-inside: avoid;
        }}

        pre code {{
            background-color: transparent;
            padding: 0;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            page-break-inside: avoid;
        }}

        th, td {{
            border: 1px solid #E2E8F0;
            padding: 0.5em;
            text-align: left;
        }}

        th {{
            background-color: #EDF2F7;
            font-weight: 600;
        }}

        a {{
            color: #3182CE;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        .header {{
            margin-bottom: 2em;
            padding-bottom: 1em;
            border-bottom: 1px solid #E2E8F0;
        }}

        .metadata {{
            font-size: 10pt;
            color: #718096;
            margin-top: 0.5em;
        }}

        .footer {{
            margin-top: 2em;
            padding-top: 1em;
            border-top: 1px solid #E2E8F0;
            font-size: 9pt;
            color: #718096;
            text-align: center;
        }}

        /* Syntax highlighting for code blocks */
        .codehilite {{
            background-color: #F7FAFC;
            padding: 1em;
            border-radius: 5px;
            margin: 1em 0;
        }}

        .codehilite .k {{ color: #D73A49; font-weight: bold; }}
        .codehilite .s {{ color: #032F62; }}
        .codehilite .c {{ color: #6A737D; font-style: italic; }}
        .codehilite .n {{ color: #1A202C; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="metadata">
            Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
        </div>
    </div>

    <div class="content">
        {content_html}
    </div>

    <div class="footer">
        Generated by Deep Research Agent • Powered by LangGraph
    </div>
</body>
</html>
    """

    return html_template


def generate_pdf(
    markdown_text: str,
    output_path: Optional[str] = None,
    title: str = "Research Report"
) -> str:
    """
    Generate a PDF from markdown text.

    Args:
        markdown_text: Markdown content
        output_path: Optional output file path. If None, uses temp file.
        title: Document title

    Returns:
        Path to generated PDF file
    """
    # Convert markdown to HTML
    html_content = markdown_to_html(markdown_text, title)

    # Generate output path if not provided
    if output_path is None:
        output_path = os.path.join(
            tempfile.gettempdir(),
            f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

    # Create PDF using WeasyPrint
    font_config = FontConfiguration()

    # Custom CSS for additional styling
    css = CSS(string="""
        @page {
            size: A4;
            margin: 2.5cm 2cm;
        }
    """, font_config=font_config)

    # Generate PDF
    html_doc = HTML(string=html_content)
    html_doc.write_pdf(output_path, stylesheets=[css], font_config=font_config)

    return output_path


def generate_pdf_with_metadata(
    markdown_text: str,
    metadata: dict,
    output_path: Optional[str] = None
) -> str:
    """
    Generate a PDF with additional metadata section.

    Args:
        markdown_text: Markdown content
        metadata: Dictionary with research metadata (sources, time, etc.)
        output_path: Optional output file path

    Returns:
        Path to generated PDF file
    """
    # Add metadata section to markdown
    metadata_section = "\n\n---\n\n## Research Metadata\n\n"

    if metadata.get("query"):
        metadata_section += f"**Original Query:** {metadata['query']}\n\n"

    if metadata.get("started_at"):
        metadata_section += f"**Started:** {metadata['started_at']}\n\n"

    if metadata.get("completed_at"):
        metadata_section += f"**Completed:** {metadata['completed_at']}\n\n"

    if metadata.get("total_time"):
        metadata_section += f"**Total Time:** {metadata['total_time']}\n\n"

    if metadata.get("subquery_count"):
        metadata_section += f"**Sub-questions Researched:** {metadata['subquery_count']}\n\n"

    # Append metadata to markdown
    full_markdown = markdown_text + metadata_section

    # Generate PDF
    title = f"Research: {metadata.get('query', 'Unknown')[:50]}..."
    return generate_pdf(full_markdown, output_path, title)


def add_citations_section(markdown_text: str, citations: list) -> str:
    """
    Add a citations section to the markdown.

    Args:
        markdown_text: Original markdown
        citations: List of citation dictionaries

    Returns:
        Markdown with citations appended
    """
    if not citations:
        return markdown_text

    citations_section = "\n\n---\n\n## Sources and Citations\n\n"

    for i, citation in enumerate(citations, 1):
        url = citation.get("url", "")
        title = citation.get("title", "Untitled")
        snippet = citation.get("snippet", "")

        citations_section += f"{i}. **{title}**\n"
        if url:
            citations_section += f"   - URL: {url}\n"
        if snippet:
            citations_section += f"   - {snippet}\n"
        citations_section += "\n"

    return markdown_text + citations_section
