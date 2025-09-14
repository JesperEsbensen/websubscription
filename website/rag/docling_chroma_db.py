import io
import os
import hashlib
import re
from uuid import uuid4
from pathlib import Path
from typing import Iterable, List, Optional, Dict, Any, Union

import chromadb
from chromadb.utils import embedding_functions

# ---- Docling imports ----
try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat, DocumentStream
    from docling.datamodel.pipeline_options import PdfPipelineOptions

    # Chunking (structure + tokens)
    from docling.chunking import HybridChunker
    from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer

    from transformers import AutoTokenizer
    
    DOCLING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Docling dependencies not available: {e}")
    print("DoclingChromaDB will not be functional. Please install docling package.")
    DOCLING_AVAILABLE = False
    
    # Create dummy classes to prevent import errors
    class DocumentConverter:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Docling not available. Please install docling package.")
    
    class PdfFormatOption:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Docling not available. Please install docling package.")
    
    class InputFormat:
        PDF = "pdf"
    
    class DocumentStream:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Docling not available. Please install docling package.")
    
    class PdfPipelineOptions:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Docling not available. Please install docling package.")
    
    class HybridChunker:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Docling not available. Please install docling package.")
    
    class HuggingFaceTokenizer:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Docling not available. Please install docling package.")
    
    class AutoTokenizer:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            raise RuntimeError("Docling not available. Please install docling package.")

# ---- LangChain imports ----
from langchain_community.vectorstores import Chroma as LCChroma
from langchain_community.embeddings import HuggingFaceEmbeddings
try:
    # Only needed if you choose OpenAI in LangChain
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
except Exception:
    OpenAIEmbeddings = None
    ChatOpenAI = None
    ChatPromptTemplate = None
    RunnablePassthrough = None
    StrOutputParser = None

try:
    from langchain_core.retrievers import BaseRetriever
    from langchain_core.documents import Document
    from langchain_core.callbacks import (
        CallbackManagerForRetrieverRun,
        AsyncCallbackManagerForRetrieverRun,
    )
except ImportError:
    # Older LangChain fallbacks
    from langchain.schema import BaseRetriever, Document
    from langchain.callbacks.manager import (
        CallbackManagerForRetrieverRun,
        AsyncCallbackManagerForRetrieverRun,
    )

try:
    from rank_bm25 import BM25Okapi
    RANK_BM25_AVAILABLE = True
except ImportError:
    print("Warning: rank_bm25 not available. BM25 functionality will be disabled.")
    RANK_BM25_AVAILABLE = False
    
    # Create dummy class
    class BM25Okapi:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("rank_bm25 not available. Please install rank_bm25 package.")


class LCChromaHybridRetriever(BaseRetriever):
    """
    LangChain-compatible retriever over a *plain Chroma* collection.
    Strategies:
      - 'vector' : dense similarity via Chroma
      - 'bm25'   : lexical BM25 over same corpus
      - 'hybrid' : Reciprocal Rank Fusion (RRF) of both
    """

    class _Hit:
        def __init__(self, _id, text, meta, score, distance=None):
            self.id = _id
            self.text = text
            self.meta = meta or {}
            self.score = float(score)
            self.distance = distance

    def __init__(
        self,
        *,
        collection,                                   # existing chroma collection instance
        distance_space: str = "cosine",
        k: int = 4,
        strategy: str = "hybrid",                     # 'vector' | 'bm25' | 'hybrid'
        tokenizer=None,                               # optional callable(str)->List[str]
        rrf_k: int = 60,
        where: Optional[Dict[str, Any]] = None,       # default metadata filter
        where_document: Optional[Dict[str, Any]] = None,  # Chroma doc filter
    ):
        super().__init__()
        self.col = collection
        self.distance_space = distance_space
        self.k = k
        self.strategy = strategy
        self.rrf_k = rrf_k
        self.where = where
        self.where_document = where_document

        # --- BM25 state (rebuilt from collection) ---
        self._tok = tokenizer or (lambda s: re.findall(r"\w+", s.lower()))
        self._bm25: Optional[BM25Okapi] = None
        self._bm25_ids: List[str] = []
        self._bm25_texts: List[str] = []
        self._bm25_metas: List[Dict[str, Any]] = []
        self._rebuild_bm25()

    # ---------- LangChain hooks ----------
    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> List[Document]:
        return self._retrieve(query, k=self.k, strategy=self.strategy)

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[AsyncCallbackManagerForRetrieverRun] = None,
    ) -> List[Document]:
        return self._get_relevant_documents(query)

    # ---------- Core ----------
    def _retrieve(
        self,
        query: str,
        *,
        k: int,
        strategy: str,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        vector_k: Optional[int] = None,
        bm25_k: Optional[int] = None,
    ) -> List[Document]:
        where = where if where is not None else self.where
        where_document = where_document if where_document is not None else self.where_document

        if strategy == "vector":
            hits = self._vector_search(query, k, where, where_document)
            return [self._to_doc(h) for h in hits]

        if strategy == "bm25":
            hits = self._bm25_search(query, k, where)
            return [self._to_doc(h) for h in hits]

        # hybrid
        v_k = vector_k or max(k, 10)
        b_k = bm25_k or max(k, 10)
        vec = self._vector_search(query, v_k, where, where_document)
        lex = self._bm25_search(query, b_k, where)
        fused = self._rrf_fuse(vec, lex, k)
        return [self._to_doc(h) for h in fused]

    # --- Vector via Chroma ---
    def _vector_search(self, query, k, where, where_document) -> List[_Hit]:
        res = self.col.query(
            query_texts=[query],
            n_results=k,
            where=where or {},
            where_document=where_document,
            include=["documents", "metadatas", "distances", "ids"],
        )
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        ids = res.get("ids", [[]])[0]
        dists = res.get("distances", [[]])[0] if res.get("distances") else [None] * len(docs)

        out: List[LCChromaHybridRetriever._Hit] = []
        for _id, doc, meta, dist in zip(ids, docs, metas, dists):
            sim = self._distance_to_similarity(dist) if dist is not None else 0.0
            out.append(self._Hit(_id, doc, meta, sim, dist))
        return out

    # --- BM25 (lexical) ---
    def _bm25_search(self, query, k, where) -> List[_Hit]:
        if not self._bm25_texts:
            return []
        scores = self._bm25.get_scores(self._tok(query))

        idxs = range(len(self._bm25_ids))
        if where:
            idxs = [i for i in idxs if self._meta_match(self._bm25_metas[i], where)]

        idxs_sorted = sorted(idxs, key=lambda i: scores[i], reverse=True)[:k]
        out: List[LCChromaHybridRetriever._Hit] = []
        for i in idxs_sorted:
            out.append(self._Hit(self._bm25_ids[i], self._bm25_texts[i], self._bm25_metas[i], float(scores[i]), None))
        return out

    # --- RRF fusion ---
    def _rrf_fuse(self, A: List[_Hit], B: List[_Hit], k: int) -> List[_Hit]:
        def ranks(lst: List[LCChromaHybridRetriever._Hit]) -> Dict[str, int]:
            return {d.id: r for r, d in enumerate(lst, start=1)}

        ra, rb = ranks(A), ranks(B)
        ids = set(ra) | set(rb)
        fused: List[LCChromaHybridRetriever._Hit] = []

        for _id in ids:
            s = 0.0
            if _id in ra:
                s += 1.0 / (self.rrf_k + ra[_id])
            if _id in rb:
                s += 1.0 / (self.rrf_k + rb[_id])
            proto = next((h for h in A if h.id == _id), None) or next((h for h in B if h.id == _id), None)
            fused.append(self._Hit(_id, proto.text, proto.meta, s, getattr(proto, "distance", None)))

        fused.sort(key=lambda h: h.score, reverse=True)
        return fused[:k]

    # --- Utilities ---
    def _distance_to_similarity(self, dist: float) -> float:
        if self.distance_space == "cosine":
            return 1.0 - float(dist)
        if self.distance_space == "euclidean":
            return 1.0 / (1.0 + float(dist))
        return -float(dist)  # inner product fallback

    def _meta_match(self, meta: Dict[str, Any], where: Dict[str, Any]) -> bool:
        """Supports {k:v} and {k:{'$in':[...]} }."""
        for k, cond in where.items():
            if isinstance(cond, dict) and "$in" in cond:
                if meta.get(k) not in cond["$in"]:
                    return False
            else:
                if meta.get(k) != cond:
                    return False
        return True

    def _rebuild_bm25(self):
        data = self.col.get(include=["documents", "metadatas", "ids"])
        self._bm25_ids = data.get("ids", [])
        self._bm25_texts = data.get("documents", [])
        self._bm25_metas = data.get("metadatas", [])
        if RANK_BM25_AVAILABLE and self._bm25_texts:
            self._bm25 = BM25Okapi([self._tok(t) for t in self._bm25_texts])
        else:
            self._bm25 = None

    def _to_doc(self, h: _Hit) -> Document:
        meta = dict(h.meta or {})
        meta.update({"id": h.id, "score": h.score})
        if h.distance is not None:
            meta["distance"] = h.distance
        return Document(page_content=h.text, metadata=meta)


class DoclingChromaDB:
    """
    End-to-end ingestion + retrieval pipeline:
      - Persistent ChromaDB (re-opens the same store across sessions)
      - Docling multi-format parsing (PDF, DOCX/PPTX/XLSX, MD/HTML/TXT, CSV, images with OCR)
      - Token/structure-aware chunking
      - Duplicate prevention (file-level via SHA256, chunk IDs stable)
    """

    DEFAULT_EXTS = {
        ".pdf", ".docx", ".pptx", ".xlsx",
        ".md", ".markdown", ".html", ".htm", ".txt", ".csv",
        ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"
    }

    def __init__(
        self,
        persist_dir: str = "./chroma_store",
        collection_name: str = "docling_chunks",
        embed_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        ocr_langs: Iterable[str] = ("en", "da"),
        allowed_exts: Optional[Iterable[str]] = None,
        max_tokens_per_chunk: int = 512,
        merge_peers: bool = True,
    ) -> None:
        if not DOCLING_AVAILABLE:
            raise RuntimeError(
                "DoclingChromaDB requires the docling package to be installed. "
                "Please run: pip install docling"
            )
            
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.embed_model = embed_model
        self.ocr_langs = list(ocr_langs)
        self.allowed_exts = set(allowed_exts) if allowed_exts else set(self.DEFAULT_EXTS)
        self.max_tokens = max_tokens_per_chunk
        self.merge_peers = merge_peers

        # Embedding function (swap to OpenAI/etc. if desired)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embed_model
        )

        # Lazily initialized; call init_db() before use (constructor calls it)
        self.client: Optional[chromadb.api.client.Client] = None
        self.collection = None

        # Docling converter + chunker (configured in init_db())
        self.converter: Optional[DocumentConverter] = None
        self.chunker: Optional[HybridChunker] = None

        self.init_db()  # ensure ready to go

    # -------------------------
    # Initialization / Utilities
    # -------------------------
    def init_db(self) -> None:
        """Create or re-open the persistent Chroma collection; set up Docling and chunker."""
        print(f"Persisting chroma db to: {self.persist_dir}")
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
        )

        # Docling with OCR languages for PDFs
        pdf_opts = PdfPipelineOptions()
        pdf_opts.ocr_options.lang = self.ocr_langs
        self.converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_opts)}
        )

        # Tokenizer aligned with embedding model for chunk sizing
        hf_tok = AutoTokenizer.from_pretrained(self.embed_model)
        tokenizer = HuggingFaceTokenizer(tokenizer=hf_tok, max_tokens=self.max_tokens)

        # Hybrid = structure-aware + token-aware
        self.chunker = HybridChunker(tokenizer=tokenizer, merge_peers=self.merge_peers)

    @staticmethod
    def _sha256_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _sha256_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _is_allowed(self, path: Union[str, Path]) -> bool:
        return Path(path).suffix.lower() in self.allowed_exts

    def _identical_doc_exists(self, doc_hash: str) -> bool:
        """True if any record with this doc_hash (file-level identity) is already present."""
        res = self.collection.get(where={"doc_hash": doc_hash}, limit=1)
        return len(res.get("ids", [])) > 0

    def _count(self) -> int:
        """Number of chunks in the collection."""
        try:
            return self.collection.count()
        except Exception:
            # Older Chroma versions may not have .count()
            res = self.collection.get(ids=[], limit=0)
            return len(res.get("ids", []))

    # -------------------------
    # Ingestion
    # -------------------------
    def add_paths(
        self,
        paths: List[str],
        batch_size: int = 1000,
        verbose: bool = True,
    ) -> None:
        """
        Ingest one or many paths (files or directories). For directories, scans recursively.
        Skips files with identical bytes (via SHA256) already in the DB.
        """
        files: List[Path] = []
        for p in paths:
            p = Path(p)
            print(f"Ingesting path: {p}")
            if p.is_dir():
                files.extend([f for f in p.rglob("*") if f.is_file() and self._is_allowed(f)])
            elif p.is_file() and self._is_allowed(p):
                files.append(p)

        if verbose:
            print(f"Found {len(files)} file(s) to consider… (collection count: {self._count()})")

        for file_path in files:
            try:
                print(f"Ingesting file: {file_path}")
                self._ingest_file(file_path, batch_size=batch_size, verbose=verbose)
            except Exception as e:
                if verbose:
                    print(f"❌ Error ingesting {file_path}: {e}")

    def _ingest_file(
        self,
        path: Path,
        batch_size: int = 1000,
        verbose: bool = True,
    ) -> None:
        raw = path.read_bytes()
        doc_hash = self._sha256_bytes(raw)

        # Skip exact duplicates at file level
        if self._identical_doc_exists(doc_hash):
            if verbose:
                print(f"⏭️  Skipping identical: {path.name} ({doc_hash[:12]}…)")
            return

        # Convert with Docling (auto-detects format; supports images/ocr)
        source = DocumentStream(name=path.name, stream=io.BytesIO(raw))
        result = self.converter.convert(source)
        dl_doc = result.document

        # Chunk (token/structure aware) and contextualize chunks
        chunks = list(self.chunker.chunk(dl_doc=dl_doc))
        if not chunks:
            if verbose:
                print(f"⚠️  No chunks produced for {path.name}")
            return

        texts = [self.chunker.contextualize(chunk=c) for c in chunks]

        # Build IDs / metadata
        ids: List[str] = []
        docs: List[str] = []
        metas: List[Dict[str, Any]] = []

        base = doc_hash[:16]
        for i, text in enumerate(texts):
            chunk_hash = self._sha256_text(text)
            chunk_id = f"{base}-{i}-{chunk_hash[:12]}"
            ids.append(chunk_id)
            docs.append(text)
            metas.append({
                "doc_hash": doc_hash,
                "source": str(path),
                "chunk_index": i,
                "chunk_hash": chunk_hash,
            })

        # Add in batches
        if verbose:
            print(f"📄 Ingesting {path.name}: {len(ids)} chunk(s)…")

        for start in range(0, len(ids), batch_size):
            end = start + batch_size
            self.collection.add(
                ids=ids[start:end],
                documents=docs[start:end],
                metadatas=metas[start:end],
            )

        if verbose:
            print(f"✅ Done {path.name} (doc_hash={doc_hash[:12]}…) — collection count: {self._count()}")

    # -------------------------
    # Retrieval
    # -------------------------
    def query(
        self,
        text: str,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over chunks.
        'where' filters by metadata (e.g., {'source': {'$contains': 'policy.pdf'}} or {'doc_hash': '...'})
        Returns a list of {document, metadata, distance} dicts ordered by relevance.
        """
        if include is None:
            include = ["documents", "metadatas", "distances"]

        res = self.collection.query(
            query_texts=[text],
            n_results=k,
            where=where or {},
            include=include,
        )
        # Normalize output to a simple list of dicts
        out = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0] if "distances" in res else [None] * len(docs)
        for d, m, dist in zip(docs, metas, dists):
            out.append({"document": d, "metadata": m, "distance": dist})
        return out

    # -------------------------
    # Convenience
    # -------------------------
    def get_by_doc_hash(self, doc_hash: str, limit: int = 5) -> Dict[str, Any]:
        """Fetch a few chunks from a specific ingested file by its doc_hash."""
        return self.collection.get(where={"doc_hash": doc_hash}, limit=limit)

    def exists_source(self, source_path: Union[str, Path]) -> bool:
        """Check if any chunk from a given source path is present."""
        res = self.collection.get(where={"source": str(Path(source_path))}, limit=1)
        return len(res.get("ids", [])) > 0



# ---- LangChain interface ----

def as_retriever(
    self,
    *,
    k: int = 5,
    strategy: str = "hybrid",                     # 'vector' | 'bm25' | 'hybrid'
    where: Optional[Dict[str, Any]] = None,
    where_document: Optional[Dict[str, Any]] = None,
    rrf_k: int = 60,
    tokenizer=None,
):
    # NOTE: Chroma defaults to cosine unless you created with a different space.
    return LCChromaHybridRetriever(
        collection=self.collection,
        distance_space="cosine",
        k=k,
        strategy=strategy,
        where=where,
        where_document=where_document,
        rrf_k=rrf_k,
        tokenizer=tokenizer,
    )
