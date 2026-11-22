"""Step 3-4: extract -> chunk (with overlap + metadata) -> embed -> Chroma.
Embeddings: offline hashing embedder by default (no downloads). Swap `embed()` for bge-m3 / OpenAI / Voyage in production."""
import hashlib
import re
import sys
import chromadb
import fitz  # pymupdf
from . import config

DIM = 384


def embed(texts):
    """Hashed bag-of-words (unigrams+bigrams), L2-normalised. Good enough for the demo; replace for real quality."""
    out = []
    for t in texts:
        v = [0.0] * DIM
        toks = re.findall(r"\w+", t.lower())
        for tok in toks + [a + "_" + b for a, b in zip(toks, toks[1:])]:
            v[int(hashlib.md5(tok.encode()).hexdigest(), 16) % DIM] += 1.0
        n = sum(x * x for x in v) ** 0.5 or 1.0
        out.append([x / n for x in v])
    return out


def read_pages(path):
    if path.suffix.lower() == ".pdf":
        with fitz.open(path) as d:
            return [(i + 1, p.get_text()) for i, p in enumerate(d)]
    return [(1, path.read_text(encoding="utf-8"))]


def chunk_words(text, size=None, overlap=None):
    size, overlap = size or config.CHUNK_SIZE, overlap or config.CHUNK_OVERLAP
    w = text.split()
    step = max(1, size - overlap)
    return [" ".join(w[i:i + size]) for i in range(0, max(len(w), 1), step) if w[i:i + size]]


def chunk_by_heading(text, max_words=None):
    """Strategy B: split at markdown headings first, then fall back to word windows. Compare A vs B in /eval."""
    parts = re.split(r"\n(?=#{1,3} )", text)
    out = []
    for p in parts:
        out.extend(chunk_words(p, max_words or config.CHUNK_SIZE, 0) if len(p.split()) > (max_words or config.CHUNK_SIZE) else [p.strip()])
    return [c for c in out if c]


def get_collection(reset=False):
    cl = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    if reset:
        try:
            cl.delete_collection("docs")
        except Exception:
            pass
    return cl.get_or_create_collection("docs", metadata={"hnsw:space": "cosine"})


def ingest(strategy="heading"):
    col = get_collection(reset=True)
    ids, docs, metas = [], [], []
    for f in sorted(config.DOCS_DIR.glob("*")):
        if f.suffix.lower() not in {".pdf", ".md", ".txt"}:
            continue
        for page, text in read_pages(f):
            chunks = chunk_by_heading(text) if strategy == "heading" else chunk_words(text)
            for j, c in enumerate(chunks):
                ids.append(hashlib.md5(f"{f.name}{page}{j}".encode()).hexdigest())
                docs.append(c)
                metas.append({"source": f.name, "page": page, "chunk": j})
    if docs:
        col.add(ids=ids, documents=docs, embeddings=embed(docs), metadatas=metas)
    return len(docs)


if __name__ == "__main__":
    print("chunks indexed:", ingest(sys.argv[1] if len(sys.argv) > 1 else "heading"))
