"""
Finassist — PDF Loader
Extracts text and tables from fund fact sheet PDFs using pdfplumber.
Implements section-aware extraction with table preservation.

Handles:
- Plain text extraction (fund commentary, objectives, disclaimers)
- Structured table extraction → converted to markdown
- Section detection using heading patterns common in Indian MF fact sheets
- Text deduplication (avoids extracting table text twice)
"""
import re
from pathlib import Path
import pdfplumber

from src.config import FUND_PDF_DIR


# ── Section Heading Patterns (common in Indian MF fact sheets) ───────────
SECTION_PATTERNS = [
    r"investment\s+objective",
    r"fund\s+details?",
    r"fund\s+information",
    r"scheme\s+information",
    r"fund\s+facts?",
    r"portfolio\s+(?:composition|holdings?|breakdown)",
    r"top\s+(?:\d+\s+)?holdings?",
    r"(?:sector|sectoral)\s+allocation",
    r"asset\s+allocation",
    r"(?:scheme\s+)?performance",
    r"(?:historical\s+)?returns?",
    r"fund\s+manager",
    r"risk\s+(?:measures?|metrics?|ratios?|statistics?)",
    r"sip\s+(?:performance|returns?)",
    r"(?:total\s+)?expense\s+ratio",
    r"benchmark",
    r"nav\s+(?:details?|information)?",
    r"dividend\s+history",
    r"important\s+(?:information|notice)",
    r"disclaimer",
    r"market\s+(?:overview|commentary|review)",
    r"riskometer",
    r"(?:asset\s+)?quality",
    r"maturity\s+profile",
    r"portfolio\s+(?:characteristics|summary)",
    r"aum\s+(?:details?|information)?",
]

# Compiled regex for performance
SECTION_RE = re.compile(
    "|".join(f"(?:{p})" for p in SECTION_PATTERNS),
    re.IGNORECASE,
)


def is_section_heading(line: str) -> bool:
    """
    Detect if a line is a section heading.
    Uses pattern matching + structural heuristics.
    """
    line_clean = line.strip()
    if not line_clean or len(line_clean) > 120 or len(line_clean) < 3:
        return False

    # Match known section heading patterns
    if SECTION_RE.search(line_clean):
        return True

    # Heuristic: ALL CAPS lines that are short (likely headings)
    if line_clean.isupper() and 3 < len(line_clean) < 60:
        # Exclude lines that look like data (contain too many numbers/special chars)
        alpha_ratio = sum(c.isalpha() for c in line_clean) / len(line_clean)
        if alpha_ratio > 0.5:
            return True

    return False


def table_to_markdown(table: list[list]) -> str:
    """
    Convert a pdfplumber table (list of rows) to markdown format.
    Handles None cells, uneven rows, and cleans whitespace.
    """
    if not table or not table[0]:
        return ""

    # Clean cells: replace None/empty with "", strip whitespace
    clean_table = []
    max_cols = max(len(row) for row in table)
    for row in table:
        clean_row = []
        for cell in row:
            cell_text = str(cell).strip() if cell else ""
            # Collapse multi-line cell text
            cell_text = " ".join(cell_text.split())
            clean_row.append(cell_text)
        # Pad short rows
        while len(clean_row) < max_cols:
            clean_row.append("")
        clean_table.append(clean_row)

    # Skip tables that are mostly empty
    non_empty_cells = sum(1 for row in clean_table for cell in row if cell)
    total_cells = sum(len(row) for row in clean_table)
    if total_cells == 0 or non_empty_cells / total_cells < 0.2:
        return ""

    # Build markdown
    header = clean_table[0]
    md_lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * len(header)) + " |",
    ]
    for row in clean_table[1:]:
        md_lines.append("| " + " | ".join(row[:len(header)]) + " |")

    return "\n".join(md_lines)


def extract_text_outside_tables(page) -> str:
    """
    Extract text from page areas that are NOT inside detected tables.
    Prevents duplicate extraction of table content.
    """
    tables = page.find_tables()
    if not tables:
        return page.extract_text() or ""

    # Get table bounding boxes with small margin
    table_bboxes = [t.bbox for t in tables]

    def outside_tables(obj):
        """Keep only objects outside table bounding boxes."""
        obj_x0 = obj.get("x0", 0)
        obj_x1 = obj.get("x1", 0)
        obj_top = obj.get("top", 0)
        obj_bottom = obj.get("bottom", 0)
        for bbox in table_bboxes:
            x0, top, x1, bottom = bbox
            if (obj_x0 >= x0 - 5 and obj_x1 <= x1 + 5 and
                    obj_top >= top - 5 and obj_bottom <= bottom + 5):
                return False
        return True

    filtered_page = page.filter(outside_tables)
    return filtered_page.extract_text() or ""


def split_text_into_sections(
    text: str,
    page_num: int,
    source: str,
    fund_name: str,
) -> list[dict]:
    """
    Split extracted text into logical sections based on heading detection.
    Returns a list of section dicts with metadata.
    """
    sections = []
    lines = text.split("\n")
    current_heading = "General"
    current_lines = []

    for line in lines:
        if is_section_heading(line):
            # Save the previous section
            section_text = "\n".join(current_lines).strip()
            if section_text and len(section_text) > 20:
                sections.append({
                    "text": section_text,
                    "content_type": "text",
                    "page_no": page_num,
                    "section_name": current_heading,
                    "source": source,
                    "fund_name": fund_name,
                })
            # Start new section
            current_heading = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save the last section
    section_text = "\n".join(current_lines).strip()
    if section_text and len(section_text) > 20:
        sections.append({
            "text": section_text,
            "content_type": "text",
            "page_no": page_num,
            "section_name": current_heading,
            "source": source,
            "fund_name": fund_name,
        })

    return sections


def extract_pdf(pdf_path: Path) -> list[dict]:
    """
    Extract all content from a fund fact sheet PDF.
    Returns list of sections with text, tables, and metadata.

    Each section dict:
    {
        "text": str,          # The extracted content
        "content_type": str,  # "text" or "table"
        "page_no": int,       # 1-indexed page number
        "section_name": str,  # Detected section heading
        "source": str,        # PDF filename
        "fund_name": str,     # Inferred fund name
    }
    """
    sections = []
    fund_name = pdf_path.stem.replace("_", " ").replace("-", " ")

    with pdfplumber.open(pdf_path) as pdf:
        print(f"  📄 {pdf_path.name}: {len(pdf.pages)} pages")

        for page_num, page in enumerate(pdf.pages, 1):
            # 1. Extract tables as markdown
            page_tables = page.extract_tables()
            for table in page_tables:
                md_table = table_to_markdown(table)
                if md_table.strip() and len(md_table.strip()) > 30:
                    sections.append({
                        "text": md_table,
                        "content_type": "table",
                        "page_no": page_num,
                        "section_name": "Table Data",
                        "source": pdf_path.name,
                        "fund_name": fund_name,
                    })

            # 2. Extract text OUTSIDE tables (avoid duplication)
            text = extract_text_outside_tables(page)

            # 3. Split text into sections by headings
            if text.strip():
                text_sections = split_text_into_sections(
                    text, page_num, pdf_path.name, fund_name,
                )
                sections.extend(text_sections)

    return sections


def load_all_pdfs(pdf_dir: Path = FUND_PDF_DIR) -> list[dict]:
    """
    Load and extract all PDFs from the fund_pdfs directory.
    Returns a flat list of all sections from all PDFs.
    """
    all_sections = []

    if not pdf_dir.exists():
        print(f"[PDFLoader] ❌ Directory not found: {pdf_dir}")
        return all_sections

    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[PDFLoader] ⚠️ No PDF files found in {pdf_dir}")
        return all_sections

    print(f"\n[PDFLoader] Found {len(pdf_files)} PDF file(s)")
    print(f"{'─' * 50}")

    for pdf_path in sorted(pdf_files):
        try:
            sections = extract_pdf(pdf_path)
            all_sections.extend(sections)
            n_tables = sum(1 for s in sections if s["content_type"] == "table")
            n_text = sum(1 for s in sections if s["content_type"] == "text")
            print(f"  Success: {n_text} text sections, {n_tables} tables extracted")
        except Exception as e:
            print(f"  Error processing {pdf_path.name}: {e}")

    print(f"{'-' * 50}")
    print(f"[PDFLoader] Total: {len(all_sections)} sections from {len(pdf_files)} PDF(s)\n")
    return all_sections


# -- CLI Test -------------------------------------------------------------
if __name__ == "__main__":
    sections = load_all_pdfs()
    for i, sec in enumerate(sections[:10], 1):
        print(f"\n{'═' * 60}")
        print(f"Section {i}: [{sec['content_type'].upper()}] {sec['section_name']}")
        print(f"Source: {sec['source']} | Page: {sec['page_no']}")
        print(f"{'─' * 60}")
        print(sec["text"][:300])
        if len(sec["text"]) > 300:
            print(f"  ... ({len(sec['text'])} chars total)")
