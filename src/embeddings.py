"""
Finassist — Gemini Embedding Wrapper
Uses Google's Gemini embedding model for high-quality vector embeddings.

Key features:
- 2048 token input limit (8x more than MiniLM's 256)
- 768 dimensions
- Separate task types for documents vs queries (improves retrieval accuracy)
- Automatic batching with rate-limit handling
- Free with Gemini API key
- Uses the new `google.genai` SDK
"""
import time
from google import genai
from google.genai import errors as genai_errors

from src.config import GOOGLE_API_KEY, GEMINI_EMBEDDING_MODEL

# Initialize the Gemini client
client = genai.Client(api_key=GOOGLE_API_KEY)


def embed_documents(texts: list[str], batch_size: int = 20) -> list[list[float]]:
    """
    Embed a list of document texts using Gemini with task_type='RETRIEVAL_DOCUMENT'.

    Uses small batches (20) with delays to stay within the free tier
    rate limit of 100 requests/minute. Retries on 429 errors.
    """
    if not texts:
        return []

    all_embeddings = []
    total_batches = (len(texts) + batch_size - 1) // batch_size

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1

        # Retry logic for rate limiting
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = client.models.embed_content(
                    model=GEMINI_EMBEDDING_MODEL,
                    contents=batch,
                    config={
                        "task_type": "RETRIEVAL_DOCUMENT",
                    },
                )

                batch_embeddings = [emb.values for emb in result.embeddings]
                all_embeddings.extend(batch_embeddings)
                print(f"  [Embedding] Batch {batch_num}/{total_batches}: embedded {len(batch)} texts")
                break  # Success, exit retry loop

            except genai_errors.ClientError as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    wait_time = 60 if attempt < max_retries - 1 else 0
                    if wait_time > 0:
                        print(f"  [Embedding] Rate limited. Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        raise
                else:
                    raise

        # Delay between batches to stay within rate limits
        if i + batch_size < len(texts):
            time.sleep(1.5)

    return all_embeddings


def embed_query(query: str) -> list[float]:
    """
    Embed a single search query using Gemini with task_type='RETRIEVAL_QUERY'.
    """
    result = client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=query,
        config={
            "task_type": "RETRIEVAL_QUERY",
        },
    )
    return result.embeddings[0].values


# -- CLI Test -------------------------------------------------------------
if __name__ == "__main__":
    print("Testing Gemini Embeddings...")

    docs = [
        "SBI Bluechip Fund has an expense ratio of 0.89% and invests in large cap equities.",
        "HDFC Sensex Index Fund tracks the BSE Sensex with an expense ratio of 0.13%.",
    ]
    doc_embeddings = embed_documents(docs)
    print(f"\nDocument embeddings: {len(doc_embeddings)} vectors, {len(doc_embeddings[0])} dims each")

    q_embedding = embed_query("What is a good low-cost index fund?")
    print(f"Query embedding: {len(q_embedding)} dims")

    print("\nGemini embeddings working!")
