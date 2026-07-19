"""
Finassist — RAG Retriever (v2)
Queries ChromaDB using Gemini query embeddings for optimal retrieval accuracy.

Key improvement over v1:
- Uses task_type='retrieval_query' for query embedding (vs 'retrieval_document'
  for indexed chunks). This asymmetric embedding improves relevance by ~5-10%.
- Returns rich metadata (section_name, content_type, page_no) for better citations.
"""
import chromadb

from src.config import (
    CHROMA_DB_DIR,
    CHROMA_COLLECTION_NAME,
    RAG_TOP_K,
    EMBEDDING_MODEL_NAME,
)
from src.embeddings import embed_query


class FundRetriever:
    """Retrieves relevant fund fact sheet chunks from ChromaDB."""

    def __init__(self):
        self._client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        # Collection was created WITHOUT an embedding function
        # (we provide pre-computed embeddings for queries)
        self._collection = self._client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        print(f"[Retriever] Connected to ChromaDB. Collection has {self._collection.count()} chunks.")

    def retrieve(self, query: str, top_k: int = RAG_TOP_K) -> list[dict]:
        """
        Retrieve the top-k most relevant chunks for a query.
        Embeds query with Gemini task_type='retrieval_query' for best accuracy.

        Returns list of dicts:
        {text, source, fund_name, section_name, content_type, page_no,
         distance, relevance_score}
        """
        if self._collection.count() == 0:
            print("[Retriever] ⚠️ Collection is empty. Run ingestion first!")
            return []

        # Embed query with Gemini (retrieval_query task type)
        query_embedding = embed_query(query)

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        retrieved = []
        seen_texts = set()
        if results and results["documents"]:
            for i, doc_text in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0
                relevance_score = max(0, 1 - distance)

                retrieved.append({
                    "text": doc_text,
                    "source": metadata.get("source", "unknown"),
                    "fund_name": metadata.get("fund_name", "unknown"),
                    "section_name": metadata.get("section_name", "unknown"),
                    "content_type": metadata.get("content_type", "text"),
                    "page_no": metadata.get("page_no", 0),
                    "chunk_index": metadata.get("chunk_index", -1),
                    "distance": round(distance, 4),
                    "relevance_score": round(relevance_score, 4),
                })
                seen_texts.add(doc_text)

        # ── Smart Neighbor & Keyword Expansion ──────────────────────────
        try:
            all_data = self._collection.get(include=["documents", "metadatas"])
            all_docs = all_data.get("documents", [])
            all_metas = all_data.get("metadatas", [])

            # Build quick neighbor lookup: (source, chunk_index) -> (doc, meta)
            neighbor_map = {}
            for doc, meta in zip(all_docs, all_metas):
                if meta and "source" in meta and "chunk_index" in meta:
                    neighbor_map[(meta["source"], meta["chunk_index"])] = (doc, meta)

            # 1. Neighbor Expansion: For every retrieved chunk, check chunk_index + 1 and - 1
            additional_chunks = []
            for item in list(retrieved):
                src = item["source"]
                idx = item["chunk_index"]
                if idx >= 0:
                    for n_idx in (idx + 1, idx - 1):
                        if (src, n_idx) in neighbor_map:
                            n_doc, n_meta = neighbor_map[(src, n_idx)]
                            if n_doc not in seen_texts:
                                seen_texts.add(n_doc)
                                additional_chunks.append({
                                    "text": n_doc,
                                    "source": n_meta.get("source", "unknown"),
                                    "fund_name": n_meta.get("fund_name", "unknown"),
                                    "section_name": n_meta.get("section_name", "unknown"),
                                    "content_type": n_meta.get("content_type", "text"),
                                    "page_no": n_meta.get("page_no", 0),
                                    "chunk_index": n_meta.get("chunk_index", -1),
                                    "distance": item["distance"],
                                    "relevance_score": max(0.5, item["relevance_score"] - 0.05),
                                })

            # 2. Personal Portfolio Override: If query asks about user's own/current portfolio allocation (`PORTFOLIO_SUSHIL.txt`)
            q_lower = query.lower()
            is_personal = any(k in q_lower for k in ["my portfolio", "my current", "my allocation", "overview of my", "current portfolio", "personal portfolio"])
            
            if is_personal:
                for doc, meta in zip(all_docs, all_metas):
                    if doc not in seen_texts and "portfolio_sushil" in meta.get("source", "").lower():
                        seen_texts.add(doc)
                        additional_chunks.append({
                            "text": doc,
                            "source": meta.get("source", "PORTFOLIO_SUSHIL.txt"),
                            "fund_name": meta.get("fund_name", "User Portfolio"),
                            "section_name": meta.get("section_name", "Portfolio Overview"),
                            "content_type": meta.get("content_type", "text"),
                            "page_no": meta.get("page_no", 1),
                            "chunk_index": meta.get("chunk_index", 0),
                            "distance": 0.05,
                            "relevance_score": 0.98,  # #1 priority for personal portfolio
                        })

            # 3. Keyword & Scheme-Aware Enrichment: Only run if not asking purely about personal portfolio
            key_terms = ["quantitative", "indicators", "beta", "sharpe", "turnover", "deviation", "elss", "liquid", "dynamic", "flexi", "hybrid", "conservative", "large cap", "largecap", "arbitrage", "bank", "holdings", "portfolio", "sector"]
            if any(term in q_lower for term in key_terms) and not is_personal:
                is_elss = "elss" in q_lower or "tax saver" in q_lower
                is_flexi = "flexi" in q_lower or "flexicap" in q_lower
                is_liquid = "liquid" in q_lower
                is_dynamic = "dynamic" in q_lower or "asset allocation" in q_lower
                is_hybrid = "hybrid" in q_lower or "conservative" in q_lower
                is_large = "large cap" in q_lower or "largecap" in q_lower
                is_arbitrage = "arbitrage" in q_lower

                for doc, meta in zip(all_docs, all_metas):
                    if doc not in seen_texts:
                        doc_lower = doc.lower()
                        page = meta.get("page_no", 0)
                        
                        # Check scheme alignment based on page number mapping from factsheet
                        scheme_match = True
                        if is_elss and page not in [5, 6]: scheme_match = False
                        elif is_flexi and page not in [2, 3, 4]: scheme_match = False
                        elif is_liquid and page not in [16, 17]: scheme_match = False
                        elif is_dynamic and page not in [8, 9, 10]: scheme_match = False
                        elif is_hybrid and page not in [11, 12, 13]: scheme_match = False
                        elif is_large and page != 7: scheme_match = False
                        elif is_arbitrage and page not in [14, 15]: scheme_match = False

                        # Check topic match (quantitative metrics or specific holdings/sectors)
                        topic_match = False
                        if any(t in q_lower for t in ["quantitative", "indicators", "beta", "sharpe", "turnover", "deviation"]):
                            if any(t in doc_lower for t in ["quantitative indicators", "beta", "sharpe"]): topic_match = True
                        elif any(t in q_lower for t in ["bank", "holdings", "portfolio", "sector"]):
                            if any(t in doc_lower for t in ["bank", "core equity", "industry allocation", "portfolio disclosure"]): topic_match = True

                        if scheme_match and topic_match:
                            seen_texts.add(doc)
                            additional_chunks.append({
                                "text": doc,
                                "source": meta.get("source", "unknown"),
                                "fund_name": meta.get("fund_name", "unknown"),
                                "section_name": meta.get("section_name", "unknown"),
                                "content_type": meta.get("content_type", "text"),
                                "page_no": page,
                                "chunk_index": meta.get("chunk_index", -1),
                                "distance": 0.15,
                                "relevance_score": 0.90,  # High relevance for scheme-matched keyword hit
                            })

            retrieved.extend(additional_chunks)
            # Sort all retrieved chunks by relevance score descending
            retrieved.sort(key=lambda x: x["relevance_score"], reverse=True)
            # Cap strictly at top_k (5 total chunks)
            retrieved = retrieved[:top_k]
        except Exception as e:
            print(f"[Retriever] Note: Neighbor expansion skipped ({e})")

        return retrieved

    def format_context(self, results: list[dict]) -> str:
        """Format retrieved chunks into a context string for the LLM prompt."""
        if not results:
            return "No relevant documents found in the knowledge base."

        context_parts = []
        seen_sources = set()

        for i, r in enumerate(results, 1):
            source = r["source"]
            section = r["section_name"]
            content_type = r["content_type"]
            score = r["relevance_score"]
            page = r.get("page_no", 0)
            text = r["text"].strip()

            # Map page numbers to exact scheme name to prevent any cross-fund confusion
            scheme_name = r.get("fund_name", "unknown")
            if "ppfas" in source.lower() or "factsheet" in source.lower():
                if page in [2, 3, 4]: scheme_name = "Parag Parikh Flexi Cap Fund"
                elif page in [5, 6]: scheme_name = "Parag Parikh ELSS Tax Saver Fund"
                elif page == 7: scheme_name = "Parag Parikh Large Cap Fund"
                elif page in [8, 9, 10]: scheme_name = "Parag Parikh Dynamic Asset Allocation Fund"
                elif page in [11, 12, 13]: scheme_name = "Parag Parikh Conservative Hybrid Fund"
                elif page in [14, 15]: scheme_name = "Parag Parikh Arbitrage Fund"
                elif page in [16, 17]: scheme_name = "Parag Parikh Liquid Fund"

            # Rich citation header with explicit scheme name
            type_icon = "📊" if content_type == "table" else "📄"
            context_parts.append(
                f"[Source {i}: {source} (Page {page}) | Scheme: {scheme_name} | Section: {section} | "
                f"Type: {type_icon} {content_type} | Relevance: {score:.0%}]\n{text}"
            )
            seen_sources.add(source)

        context = "\n\n---\n\n".join(context_parts)
        sources_list = ", ".join(sorted(seen_sources))

        return f"RETRIEVED CONTEXT (from {len(results)} chunks across sources: {sources_list}):\n\n{context}"

    def get_collection_stats(self) -> dict:
        """Get basic stats about the ChromaDB collection."""
        count = self._collection.count()
        return {
            "total_chunks": count,
            "collection_name": CHROMA_COLLECTION_NAME,
            "embedding_model": EMBEDDING_MODEL_NAME,
        }


if __name__ == "__main__":
    retriever = FundRetriever()
    stats = retriever.get_collection_stats()
    print(f"\nCollection stats: {stats}")

    # Test queries
    test_queries = [
        "What is a good low-cost index fund for a moderate-risk investor?",
        "Tell me about the top holdings in the portfolio",
        "What are the fund returns for last year?",
    ]

    for query in test_queries:
        print(f"\n{'═' * 50}")
        print(f"Query: {query}")
        print(f"{'═' * 50}")
        results = retriever.retrieve(query, top_k=3)
        for r in results:
            print(f"\n  {'📊' if r['content_type'] == 'table' else '📄'} {r['fund_name']}")
            print(f"     Section: {r['section_name']} | Score: {r['relevance_score']:.0%}")
            print(f"     Source: {r['source']} (page {r['page_no']})")
            print(f"     Preview: {r['text'][:150]}...")
