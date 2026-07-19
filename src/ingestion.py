"""
Finassist — Ingestion Pipeline (v2)
Section-aware chunking with table preservation.

Pipeline: PDF → pdfplumber (text+tables) → section-aware chunking
         → Gemini text-embedding-004 → ChromaDB

Key design decisions:
- Tables are NEVER split mid-row (preserves data integrity)
- Large tables are split with header row repeated in each chunk
- Text sections are split at paragraph/sentence boundaries
- Each chunk carries rich metadata (source, section, page, content_type)
- Gemini embeddings with task_type='retrieval_document' for indexing
"""
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb

from src.config import (
    FUND_CORPUS_DIR,
    FUND_PDF_DIR,
    CHROMA_DB_DIR,
    CHROMA_COLLECTION_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TABLE_MAX_CHARS,
    DEFAULT_USER,
    format_inr,
)
from src.pdf_loader import load_all_pdfs
from src.embeddings import embed_documents
from src.user_profile_loader import get_user_profile


# ── Text Chunking ────────────────────────────────────────────────────────

def chunk_text_section(section: dict) -> list[dict]:
    """
    Chunk a text section using RecursiveCharacterTextSplitter.
    Splits at paragraph/sentence boundaries, never mid-word.
    """
    text = section["text"]

    # If text is small enough, keep as a single chunk
    if len(text) <= CHUNK_SIZE:
        return [section]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=[
            "\n\n",   # Paragraph breaks (best)
            "\n",     # Line breaks
            ". ",     # Sentence boundaries
            ", ",     # Clause boundaries
            " ",      # Word boundaries (last resort)
        ],
    )

    splits = splitter.split_text(text)
    chunks = []
    for i, split_text in enumerate(splits):
        chunk = dict(section)  # Copy metadata
        chunk["text"] = split_text
        chunk["chunk_index"] = i
        chunk["total_chunks"] = len(splits)
        chunks.append(chunk)

    return chunks


def chunk_table_section(section: dict) -> list[dict]:
    """
    Chunk a table section. Small tables stay intact.
    Large tables are split by rows with the header row repeated.
    """
    text = section["text"]

    # Small table: keep intact
    if len(text) <= TABLE_MAX_CHARS:
        return [section]

    # Large table: split by rows, repeat header
    lines = text.strip().split("\n")
    if len(lines) < 3:
        return [section]  # Too few rows to split

    header_line = lines[0]       # | Col1 | Col2 | ...
    separator_line = lines[1]    # | --- | --- | ...
    data_rows = lines[2:]

    header_block = header_line + "\n" + separator_line + "\n"
    header_len = len(header_block)

    # Split data rows into groups that fit within TABLE_MAX_CHARS
    chunks = []
    current_rows = []
    current_len = header_len

    for row in data_rows:
        row_len = len(row) + 1  # +1 for newline
        if current_len + row_len > TABLE_MAX_CHARS and current_rows:
            # Save current chunk
            chunk_text = header_block + "\n".join(current_rows)
            chunk = dict(section)
            chunk["text"] = chunk_text
            chunk["chunk_index"] = len(chunks)
            chunks.append(chunk)
            # Start new chunk
            current_rows = [row]
            current_len = header_len + row_len
        else:
            current_rows.append(row)
            current_len += row_len

    # Save last chunk
    if current_rows:
        chunk_text = header_block + "\n".join(current_rows)
        chunk = dict(section)
        chunk["text"] = chunk_text
        chunk["chunk_index"] = len(chunks)
        chunks.append(chunk)

    # Update total_chunks
    for chunk in chunks:
        chunk["total_chunks"] = len(chunks)

    return chunks


def chunk_all_sections(sections: list[dict]) -> list[dict]:
    """
    Apply the appropriate chunking strategy to each section.
    Tables get table-aware chunking; text gets recursive splitting.
    """
    all_chunks = []

    for section in sections:
        if section["content_type"] == "table":
            chunks = chunk_table_section(section)
        else:
            chunks = chunk_text_section(section)
        all_chunks.extend(chunks)

    # Add global chunk IDs
    for i, chunk in enumerate(all_chunks):
        chunk["chunk_id"] = f"chunk_{i:04d}"

    return all_chunks


# ── Portfolio Document ───────────────────────────────────────────────────

def build_portfolio_document(user_name: str) -> list[dict]:
    """
    Generate a portfolio overview document as sections for RAG context.
    This helps the assistant understand the user's complete financial picture.
    """
    profile = get_user_profile(user_name)
    if not profile:
        return []

    # Build the portfolio text
    doc = f"""INVESTOR PROFILE: {profile['name']}
Age: {profile['age']}
Occupation: {profile['occupation']}
Risk Profile: {profile['riskProfile']}
Total Portfolio: {profile['currency']} {format_inr(profile['totalPortfolioValue'])}

INVESTMENT GOALS
"""
    for i, goal in enumerate(profile.get("goals", []), 1):
        doc += f"{i}. {goal}\n"

    doc += "\nPORTFOLIO ALLOCATION\n"
    for key, alloc in profile.get("allocation", {}).items():
        doc += f"- {key}: {alloc['percentage']}% (₹{format_inr(alloc['value'])}) — {alloc['description']}\n"

    metrics = profile.get("yearlyFinancialMetrics", {})
    if metrics:
        doc += f"""
FINANCIAL METRICS
Expected Annual Return: {metrics.get('expectedAnnualReturn', 'N/A')}
Expected Volatility: {metrics.get('expectedVolatility', 'N/A')}
Sharpe Ratio: {metrics.get('sharpeRatio', 'N/A')}
Projected Value (5yr): ₹{format_inr(metrics.get('projectedValue_5yr', 0))}
Projected Value (10yr): ₹{format_inr(metrics.get('projectedValue_10yr', 0))}
"""

    doc += f"""
REBALANCING
Strategy: {profile.get('rebalancingStrategy', 'N/A')}
Last Rebalanced: {profile.get('lastRebalanced', 'N/A')}
Next Recommended: {profile.get('nextRebalanceDateRecommended', 'N/A')}
"""

    return [{
        "text": doc.strip(),
        "content_type": "text",
        "page_no": 0,
        "section_name": "User Portfolio Overview",
        "source": f"PORTFOLIO_{user_name.upper()}.txt",
        "fund_name": f"Portfolio - {user_name}",
    }]


# ── Corpus Loading (Legacy .txt support) ─────────────────────────────────

def load_txt_documents(corpus_dir: Path = FUND_CORPUS_DIR) -> list[dict]:
    """Load any existing .txt files from the corpus directory (backward compat)."""
    documents = []
    if not corpus_dir.exists():
        return documents

    for file_path in sorted(corpus_dir.glob("*.txt")):
        content = file_path.read_text(encoding="utf-8")
        if not content.strip():
            continue

        fund_name = file_path.stem.replace("_", " ")
        documents.append({
            "text": content,
            "content_type": "text",
            "page_no": 0,
            "section_name": "Full Document",
            "source": file_path.name,
            "fund_name": fund_name,
        })

    if documents:
        print(f"[Ingestion] Also loaded {len(documents)} legacy .txt documents")
    return documents


# ── ChromaDB Storage ─────────────────────────────────────────────────────

def create_fresh_collection():
    """Create a fresh ChromaDB collection (deletes existing data)."""
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    # Delete existing collection for a clean rebuild
    try:
        client.delete_collection(name=CHROMA_COLLECTION_NAME)
        print(f"[Ingestion] Deleted existing collection: {CHROMA_COLLECTION_NAME}")
    except Exception:
        pass

    # Create collection WITHOUT an embedding function
    # (we provide pre-computed Gemini embeddings manually)
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    return collection


def store_chunks_in_chromadb(chunks: list[dict]):
    """
    Embed all chunks with Gemini and store in ChromaDB.
    Uses task_type='retrieval_document' for optimal indexing.
    """
    if not chunks:
        print("[Ingestion] ❌ No chunks to store!")
        return 0

    collection = create_fresh_collection()

    # Prepare data
    ids = [chunk["chunk_id"] for chunk in chunks]
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            "source": chunk["source"],
            "fund_name": chunk["fund_name"],
            "section_name": chunk["section_name"],
            "content_type": chunk["content_type"],
            "page_no": chunk["page_no"],
            "chunk_index": chunk.get("chunk_index", 0),
            "total_chunks": chunk.get("total_chunks", 1),
        }
        for chunk in chunks
    ]

    # Embed with Gemini
    print(f"\n[Ingestion] Embedding {len(texts)} chunks with Gemini text-embedding-004...")
    embeddings = embed_documents(texts)

    # Store in ChromaDB in batches
    batch_size = 100
    total_batches = (len(ids) + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        start = batch_num * batch_size
        end = min(start + batch_size, len(ids))

        collection.add(
            ids=ids[start:end],
            documents=texts[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  [ChromaDB] Batch {batch_num + 1}/{total_batches}: stored chunks {start}–{end - 1}")

    print(f"\n[Ingestion] ✅ Stored {collection.count()} chunks in ChromaDB")
    return collection.count()


# ── Main Pipeline ────────────────────────────────────────────────────────

def run_ingestion(user_name: str = DEFAULT_USER):
    """
    Full ingestion pipeline:
    1. Load PDFs from data/fund_pdfs/
    2. Load any legacy .txt files from data/fund_corpus/
    3. Generate portfolio overview document
    4. Section-aware chunking with table preservation
    5. Embed with Gemini text-embedding-004
    6. Store in ChromaDB
    """
    print(f"\n{'═' * 60}")
    print(f"  Finassist — RAG Ingestion Pipeline v2")
    print(f"  Section-Aware Chunking + Gemini Embeddings")
    print(f"{'═' * 60}\n")

    # Step 1: Load PDFs
    print("📄 Step 1: Loading PDF fact sheets...")
    pdf_sections = load_all_pdfs()

    # Step 2: Load legacy .txt files (if any)
    print("📝 Step 2: Loading legacy .txt documents...")
    txt_sections = load_txt_documents()

    # Step 3: Generate portfolio document
    print(f"👤 Step 3: Generating portfolio overview for '{user_name}'...")
    portfolio_sections = build_portfolio_document(user_name)
    if portfolio_sections:
        print(f"  ✅ Portfolio document generated ({len(portfolio_sections[0]['text'])} chars)")

    # Combine all sections
    all_sections = pdf_sections + txt_sections + portfolio_sections
    print(f"\n📊 Total sections: {len(all_sections)}")
    print(f"   - PDF sections: {len(pdf_sections)}")
    print(f"   - TXT sections: {len(txt_sections)}")
    print(f"   - Portfolio: {len(portfolio_sections)}")

    if not all_sections:
        print("\n[Ingestion] ❌ No documents found! Place PDF files in data/fund_pdfs/")
        return 0

    # Step 4: Chunk
    print(f"\n🧩 Step 4: Chunking (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    chunks = chunk_all_sections(all_sections)

    # Stats
    table_chunks = sum(1 for c in chunks if c["content_type"] == "table")
    text_chunks = sum(1 for c in chunks if c["content_type"] == "text")
    avg_len = sum(len(c["text"]) for c in chunks) / len(chunks) if chunks else 0
    print(f"  Total chunks: {len(chunks)} ({text_chunks} text, {table_chunks} table)")
    print(f"  Avg chunk size: {avg_len:.0f} chars")

    # Step 5 & 6: Embed and store
    print(f"\n💾 Step 5: Embedding + storing in ChromaDB...")
    count = store_chunks_in_chromadb(chunks)

    # Summary
    print(f"\n{'═' * 60}")
    print(f"  ✅ Ingestion Complete!")
    print(f"  📄 PDFs processed: {len(list(FUND_PDF_DIR.glob('*.pdf')))}")
    print(f"  🧩 Chunks created: {len(chunks)}")
    print(f"  💾 Stored in ChromaDB: {count} vectors")
    print(f"  🧠 Embedding model: Gemini text-embedding-004 (768 dims)")
    print(f"  📁 DB location: {CHROMA_DB_DIR}")
    print(f"{'═' * 60}\n")

    return count


if __name__ == "__main__":
    run_ingestion()
