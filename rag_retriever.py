"""
RAG Retriever v2
Queries ChromaDB for relevant framework passages.
Falls back to knowledge_base.py if ChromaDB not available.
"""

from pathlib import Path
from typing import Optional

CHROMA_DIR  = Path("./chroma_db")
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K       = 5

_embedder   = None
_collection = None
_rag_available = False

def init_rag() -> bool:
    global _embedder, _collection, _rag_available
    if not CHROMA_DIR.exists():
        print("[RAG] No chroma_db/ found. Run ingest.py first. Using knowledge_base fallback.")
        return False
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        print("[RAG] Loading embedding model (first load may take 10s)...")
        _embedder   = SentenceTransformer(EMBED_MODEL)
        client      = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_collection("framework_docs")
        count       = _collection.count()
        if count == 0:
            print("[RAG] Collection empty. Run ingest.py.")
            return False
        print(f"[RAG] Ready — {count} chunks loaded from ChromaDB")
        _rag_available = True
        return True
    except Exception as e:
        print(f"[RAG] Failed to init: {e}. Using knowledge_base fallback.")
        return False

# Domain → extra search terms to boost relevant chunk retrieval
DOMAIN_BOOST = {
    "Identity":            "identity management authentication access control IAM zero trust",
    "Network":             "network segmentation microsegmentation firewall zero trust network",
    "Data":                "data security classification encryption data loss prevention",
    "Application":         "application security SDLC secure coding API security",
    "Governance":          "governance risk management policy compliance audit",
    "Cloud Security":      "cloud security posture management shared responsibility hybrid cloud",
    "Detection & Response":"monitoring threat detection incident response SIEM SOC",
    "API Security":        "API security gateway authentication authorisation rate limiting",
}

# Framework → extra context terms
FRAMEWORK_BOOST = {
    "NIST AI RMF": "AI risk trustworthy artificial intelligence machine learning model governance bias",
    "Zero Trust":  "zero trust architecture never trust always verify microsegmentation identity",
    "NIST CSF":    "cybersecurity framework govern identify protect detect respond recover",
    "TOGAF":       "architecture development method ADM enterprise architecture governance",
    "NAF":         "NATO architecture framework viewpoints capability operational service",
    "DNDAF":       "defence architecture framework capability operational technical",
    "DODAF":       "DoD architecture framework systems views operational views",
    "Zachman":     "zachman framework rows columns why how what who where when",
}

def retrieve(query: str, framework_filter: Optional[str] = None, n: int = TOP_K) -> list:
    if not _rag_available or _collection is None or _embedder is None:
        return []
    try:
        embedding = _embedder.encode([query]).tolist()
        where = {"framework": framework_filter} if framework_filter else None
        results = _collection.query(
            query_embeddings=embedding,
            n_results=n,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        passages = []
        for i, doc in enumerate(results["documents"][0]):
            meta  = results["metadatas"][0][i]
            score = round(1 - results["distances"][0][i], 3)
            if score < 0.15:
                continue
            passages.append({
                "text":       doc[:800],
                "framework":  meta.get("framework", "Unknown"),
                "source":     meta.get("source", ""),
                "start_page": meta.get("start_page", 0),
                "end_page":   meta.get("end_page", 0),
                "score":      score,
            })
        return passages
    except Exception as e:
        print(f"[RAG] Retrieval error: {e}")
        return []

def retrieve_for_requirement(requirement: str, domain: str, active_frameworks: list) -> list:
    if not _rag_available:
        return []

    domain_terms = DOMAIN_BOOST.get(domain, "")
    all_passages = []

    for fw in active_frameworks:
        fw_terms = FRAMEWORK_BOOST.get(fw, "")
        # Richer query: requirement + domain terms + framework-specific terms
        query = f"{requirement} {domain_terms} {fw_terms}".strip()
        passages = retrieve(query, framework_filter=fw, n=3)
        all_passages.extend(passages)

    # Also do a broad query for AI-related frameworks if domain is Governance
    if domain == "Governance" and any(
        fw in active_frameworks for fw in ["NIST AI RMF", "AI Security"]
    ):
        ai_query = f"{requirement} AI model risk governance trustworthy artificial intelligence"
        for fw in ["NIST AI RMF", "AI Security"]:
            passages = retrieve(ai_query, framework_filter=fw, n=3)
            all_passages.extend(passages)

    # Deduplicate by source+page, sort by score
    seen, unique = set(), []
    for p in sorted(all_passages, key=lambda x: x["score"], reverse=True):
        key = f"{p['source']}_{p['start_page']}"
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return unique[:TOP_K]

def format_citation(passage: dict) -> dict:
    fw     = passage["framework"]
    source = passage["source"].replace(".pdf", "").replace(".docx", "")
    page   = passage["start_page"]
    if passage["end_page"] and passage["end_page"] != passage["start_page"]:
        page = f"{passage['start_page']}–{passage['end_page']}"
    return {
        "id":        f"{fw}-p{passage['start_page']}",
        "framework": fw,
        "source":    f"{source}, p.{page}",
        "clause":    passage["text"],
        "score":     passage["score"],
        "type":      "rag",
    }
