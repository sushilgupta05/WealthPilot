"""
Finassist — Central Configuration
All paths, model names, API URLs, and tuning parameters in one place.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FUND_PDF_DIR = DATA_DIR / "fund_pdfs"
FUND_CORPUS_DIR = DATA_DIR / "fund_corpus"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"
USER_PROFILES_PATH = PROJECT_ROOT / "user_profiles.json"

# Ensure directories exist
FUND_PDF_DIR.mkdir(parents=True, exist_ok=True)
FUND_CORPUS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

# ── Gemini Embedding Model ───────────────────────────────────────────────
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768

# ── Embedding Config ─────────────────────────────────────────────────────
EMBEDDING_MODEL_NAME = "Gemini text-embedding-004"

# ── ChromaDB ─────────────────────────────────────────────────────────────
CHROMA_COLLECTION_NAME = "wealthpilot_funds"

# ── Chunking ─────────────────────────────────────────────────────────────
# Gemini embedding supports 2048 tokens (~8000 chars).
# 1500 chars keeps sections intact while staying well within the limit.
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
TABLE_MAX_CHARS = 1200  # Tables under this size are kept intact

# ── LLM Providers & Models ──────────────────────────────────────────────
# Embedding model remains fixed:
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"

# LLM Provider: "groq" (Finance/Reasoning models via Groq), "huggingface", or "gemini"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq" if os.getenv("GROQ_API_KEY") else ("huggingface" if os.getenv("HF_TOKEN") else "gemini"))

# Groq Configuration (Finance dedicated / Reasoning model)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Hugging Face Configuration
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")

# Google Gemini Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = "gemini-3.5-flash"

LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 8192

# ── RAG Retrieval ────────────────────────────────────────────────────────
RAG_TOP_K = 5

# ── Default User ─────────────────────────────────────────────────────────
DEFAULT_USER = "Sushil"

# ── Formatting Helpers ───────────────────────────────────────────────────
def format_inr(number: float | int) -> str:
    """Format a number according to the Indian numbering system (Lakhs/Crores, e.g., 25,00,000)."""
    try:
        s = f"{int(number)}"
        if len(s) <= 3:
            return s
        last_three = s[-3:]
        remaining = s[:-3]
        groups = []
        while len(remaining) > 2:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.append(remaining)
        groups.reverse()
        return ",".join(groups) + "," + last_three
    except Exception:
        return str(number)

