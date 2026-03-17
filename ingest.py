"""
RAG Ingestion Script v2
Reads PDFs and DOCX files from ./docs/
Chunks, embeds with sentence-transformers, stores in ChromaDB at ./chroma_db/

Run once:  python ingest.py
Re-run any time you add new documents.
"""

import os, sys
from pathlib import Path

try:
    import chromadb
    from pypdf import PdfReader
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Missing dependencies. Run:")
    print("  pip install chromadb pypdf sentence-transformers python-docx")
    sys.exit(1)

DOCS_DIR      = Path("./docs")
CHROMA_DIR    = Path("./chroma_db")
CHUNK_SIZE    = 500
CHUNK_OVERLAP = 50
EMBED_MODEL   = "all-MiniLM-L6-v2"

FRAMEWORK_MAP = [
    ("800-207",           "Zero Trust"),
    ("CSWP.29",           "NIST CSF"),
    ("800-53",            "NIST SP 800-53"),
    ("AI.600",            "NIST AI RMF"),
    ("AI_RMF",            "NIST AI RMF"),
    ("Artificial Intelligence", "AI Security"),
    ("UAF",               "UAF"),
    ("AC_322",            "UAF"),
    ("NAFv4",             "NAF"),
    ("ArchiMate",         "NAF"),
    ("DNDAF",             "DNDAF"),
    ("DoDAF",             "DODAF"),
    ("DODAF",             "DODAF"),
    ("omg-22",            "TOGAF"),
    ("togaf",             "TOGAF"),
    ("C220",              "TOGAF"),
    ("TOGAF",             "TOGAF"),
    ("zachman",           "Zachman"),
    ("Zachman",           "Zachman"),
    ("System Of Systems", "Systems Architecture"),
    ("SABSA",             "SABSA"),
]

def detect_framework(filename: str) -> str:
    for key, fw in FRAMEWORK_MAP:
        if key.lower() in filename.lower():
            return fw
    return Path(filename).stem[:30]

def extract_from_pdf(pdf_path: Path) -> list:
    try:
        reader = PdfReader(str(pdf_path))
        pages = []
        for i, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            if len(text) > 80:
                pages.append({"text": text, "page": i + 1})
        return pages
    except Exception as e:
        print(f"  WARNING: Could not read PDF {pdf_path.name}: {e}")
        return []

def extract_from_docx(docx_path: Path) -> list:
    try:
        from docx import Document
        doc = Document(str(docx_path))
        pages, current, page_num = [], [], 1
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                current.append(text)
            if len(" ".join(current).split()) > 400:
                pages.append({"text": " ".join(current), "page": page_num})
                current = []
                page_num += 1
        if current:
            pages.append({"text": " ".join(current), "page": page_num})
        return pages
    except ImportError:
        print(f"  WARNING: python-docx not installed. Run: pip install python-docx")
        print(f"  SKIPPING {docx_path.name}")
        return []
    except Exception as e:
        print(f"  WARNING: Could not read DOCX {docx_path.name}: {e}")
        return []

def chunk_pages(pages: list) -> list:
    chunks, buf_words, buf_pages = [], [], []
    for page in pages:
        words = page["text"].split()
        buf_words.extend(words)
        buf_pages.append(page["page"])
        while len(buf_words) >= CHUNK_SIZE:
            chunks.append({
                "text": " ".join(buf_words[:CHUNK_SIZE]),
                "start_page": buf_pages[0],
                "end_page": buf_pages[-1],
            })
            buf_words = buf_words[CHUNK_SIZE - CHUNK_OVERLAP:]
            buf_pages = buf_pages[1:] if len(buf_pages) > 1 else buf_pages
    if len(buf_words) > 80:
        chunks.append({
            "text": " ".join(buf_words),
            "start_page": buf_pages[0] if buf_pages else 0,
            "end_page": buf_pages[-1] if buf_pages else 0,
        })
    return chunks

def main():
    if not DOCS_DIR.exists():
        print("Create a docs/ folder and place your PDFs/DOCX files in it.")
        sys.exit(1)

    # Collect PDFs and DOCX files
    files = list(DOCS_DIR.glob("*.pdf")) + list(DOCS_DIR.glob("*.docx"))
    if not files:
        print("No PDF or DOCX files found in ./docs/")
        sys.exit(1)

    print(f"\nFound {len(files)} document(s):\n")
    for f in sorted(files):
        fw = detect_framework(f.name)
        size_kb = f.stat().st_size // 1024
        print(f"  {f.name:<60} [{fw}]  {size_kb}KB")

    print(f"\nLoading embedding model: {EMBED_MODEL}")
    print("First run downloads ~90MB. Subsequent runs use cached model.\n")
    embedder = SentenceTransformer(EMBED_MODEL)

    CHROMA_DIR.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        client.delete_collection("framework_docs")
        print("Cleared existing collection.\n")
    except Exception:
        pass

    collection = client.create_collection(
        name="framework_docs",
        metadata={"hnsw:space": "cosine"}
    )

    total_chunks = 0

    for doc_path in sorted(files):
        framework = detect_framework(doc_path.name)
        print(f"Processing: {doc_path.name}")
        print(f"  Framework: {framework}")

        if doc_path.suffix.lower() == ".pdf":
            pages = extract_from_pdf(doc_path)
        elif doc_path.suffix.lower() == ".docx":
            pages = extract_from_docx(doc_path)
        else:
            continue

        if not pages:
            print(f"  SKIPPED\n")
            continue

        chunks = chunk_pages(pages)
        print(f"  Pages/sections: {len(pages)}  →  Chunks: {len(chunks)}")

        for i in range(0, len(chunks), 32):
            batch = chunks[i:i+32]
            texts = [c["text"] for c in batch]
            embeddings = embedder.encode(texts, show_progress_bar=False).tolist()
            collection.add(
                ids=[f"{framework}_{total_chunks+i+j}" for j in range(len(batch))],
                embeddings=embeddings,
                documents=texts,
                metadatas=[{
                    "framework": framework,
                    "source": doc_path.name,
                    "start_page": c["start_page"],
                    "end_page": c["end_page"],
                    "chunk_index": total_chunks+i+j,
                } for j, c in enumerate(batch)],
            )

        total_chunks += len(chunks)
        print(f"  Stored {len(chunks)} chunks\n")

    print("=" * 60)
    print(f"Ingestion complete!")
    print(f"  Total chunks stored: {total_chunks}")
    print(f"  ChromaDB location:   {CHROMA_DIR.absolute()}")
    print(f"\nNow restart agent_v2.py — RAG will activate automatically.")

if __name__ == "__main__":
    main()
