#!/usr/bin/env python3
"""PDF Inventory Generator for Token Furnace Lab.

Scans a directory for PDF files and generates a structured inventory with metadata.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from pdfminer.high_level import extract_text
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False


def extract_title_from_pdf(filepath: str) -> Optional[str]:
    """Extract title from PDF metadata."""
    if PyPDF2 is None:
        return None
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if reader.metadata and reader.metadata.title:
                return reader.metadata.title
    except Exception:
        pass
    return None


def get_page_count(filepath: str) -> Optional[int]:
    """Get page count from PDF."""
    if PyPDF2 is None:
        return None
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return len(reader.pages)
    except Exception:
        return None


def is_text_extractable(filepath: str) -> bool:
    """Check if text can be extracted from PDF."""
    if PDFMINER_AVAILABLE:
        try:
            text = extract_text(filepath, maxpages=1)
            return len(text.strip()) > 50
        except Exception:
            return False
    elif PyPDF2 is not None:
        try:
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                if len(reader.pages) > 0:
                    text = reader.pages[0].extract_text()
                    return len(text.strip()) > 50
        except Exception:
            pass
    return False


def detect_language(text: str) -> str:
    """Detect language of text (simple heuristic)."""
    if not text:
        return "unknown"
    chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
    total_chars = len(text)
    if total_chars == 0:
        return "unknown"
    ratio = chinese_chars / total_chars
    if ratio > 0.3:
        return "zh"
    elif ratio > 0.1:
        return "mixed"
    return "en"


def extract_keywords(text: str, max_keywords: int = 10) -> list:
    """Extract simple keywords from text."""
    if not text:
        return []
    # Simple keyword extraction - split by whitespace and common separators
    import re
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    # Count frequency
    from collections import Counter
    word_counts = Counter(words)
    # Filter common words
    stop_words = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'are', 'was', 'were', 'been', 'have', 'has', 'had', 'not', 'but', 'what', 'all', 'can', 'her', 'his', 'our', 'out', 'one', 'two', 'new', 'some', 'could', 'would', 'may', 'might', 'shall', 'should'}
    keywords = [w for w, c in word_counts.most_common(max_keywords * 3) if w not in stop_words]
    return keywords[:max_keywords]


def detect_content_indicators(text: str) -> dict:
    """Detect if text contains formulas, block diagrams, experiments."""
    text_lower = text.lower()
    return {
        'has_formula': any(indicator in text_lower for indicator in [
            'equation', 'formula', '=', '\\frac', '\\sum', '\\int', 'fig.', 'figure'
        ]),
        'has_block_diagram': any(indicator in text_lower for indicator in [
            'block diagram', 'fig.', 'figure', 'diagram', 'schematic'
        ]),
        'has_experiment': any(indicator in text_lower for indicator in [
            'experiment', 'experimental', 'test', 'measurement', 'result', 'figure', 'table'
        ])
    }


def scan_pdf_directory(directory: str) -> list:
    """Scan directory for PDF files and generate inventory."""
    inventory = []
    pdf_files = list(Path(directory).rglob('*.pdf'))

    for pdf_path in pdf_files:
        filepath = str(pdf_path)
        filename = pdf_path.name

        # Extract metadata
        title = extract_title_from_pdf(filepath)
        page_count = get_page_count(filepath)
        text_extractable = is_text_extractable(filepath)

        # Extract sample text for analysis
        sample_text = ""
        if text_extractable:
            try:
                if PDFMINER_AVAILABLE:
                    sample_text = extract_text(filepath, maxpages=2)
                elif PyPDF2 is not None:
                    with open(filepath, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        for i in range(min(2, len(reader.pages))):
                            sample_text += reader.pages[i].extract_text() or ""
            except Exception:
                pass

        # Analyze content
        language = detect_language(sample_text)
        keywords = extract_keywords(sample_text)
        content_indicators = detect_content_indicators(sample_text)

        # Estimate category
        category = "unknown"
        if any(kw in filename.lower() or kw in sample_text.lower() for kw in ['foc', 'field oriented', 'vector control', 'sensorless']):
            category = "P1"  # Algorithm paper
        elif any(kw in filename.lower() or kw in sample_text.lower() for kw in ['implementation', 'hardware', 'dsp', 'tms320']):
            category = "P2"  # Engineering paper
        elif any(kw in filename.lower() or kw in sample_text.lower() for kw in ['comparison', 'review', 'survey']):
            category = "P3"  # Comparison paper

        inventory.append({
            'filename': filename,
            'filepath': filepath,
            'title': title or 'unknown',
            'page_count': page_count,
            'text_extractable': text_extractable,
            'language': language,
            'keywords': keywords,
            'has_formula': content_indicators['has_formula'],
            'has_block_diagram': content_indicators['has_block_diagram'],
            'has_experiment': content_indicators['has_experiment'],
            'estimated_category': category
        })

    return inventory


def format_inventory_markdown(inventory: list) -> str:
    """Format inventory as markdown table."""
    lines = ["# PDF Inventory\n"]
    lines.append(f"Total PDFs found: {len(inventory)}\n")
    lines.append("| Filename | Title | Pages | Text | Language | Keywords | Formula | Diagram | Experiment | Category |")
    lines.append("|----------|-------|-------|------|----------|----------|---------|---------|------------|----------|")

    for item in inventory:
        title_display = (item['title'][:40] + '...') if len(item['title']) > 40 else item['title']
        keywords_display = ', '.join(item['keywords'][:3]) if item['keywords'] else 'none'
        lines.append(
            f"| {item['filename'][:30]} | {title_display} | {item['page_count'] or '?'} | "
            f"{'✓' if item['text_extractable'] else '✗'} | {item['language']} | {keywords_display} | "
            f"{'✓' if item['has_formula'] else '✗'} | {'✓' if item['has_block_diagram'] else '✗'} | "
            f"{'✓' if item['has_experiment'] else '✗'} | {item['estimated_category']} |"
        )

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 pdf_inventory.py <directory> [--json]")
        print("Example: python3 pdf_inventory.py /path/to/pdfs --json")
        sys.exit(1)

    directory = sys.argv[1]
    output_json = '--json' in sys.argv

    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a directory")
        sys.exit(1)

    inventory = scan_pdf_directory(directory)

    if output_json:
        print(json.dumps(inventory, indent=2, ensure_ascii=False))
    else:
        print(format_inventory_markdown(inventory))


if __name__ == '__main__':
    main()
