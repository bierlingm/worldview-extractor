"""RAG (Retrieval-Augmented Generation) for transcript corpus interrogation."""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from wve.cache import cache_key, get_cached, set_cached


@dataclass
class Chunk:
    """A chunk of transcript text with source info."""
    text: str
    source_id: str
    source_title: str
    chunk_index: int


@dataclass
class SearchResult:
    """A chunk matched by semantic search."""
    chunk: Chunk
    score: float


class EmbeddingIndex:
    """Vector index for semantic search over chunks."""

    def __init__(self, chunks: list[Chunk], embeddings: np.ndarray, model_name: str):
        self.chunks = chunks
        self.embeddings = embeddings
        self.model_name = model_name

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        """Find top-k most similar chunks."""
        similarities = np.dot(self.embeddings, query_embedding)
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [
            SearchResult(chunk=self.chunks[i], score=float(similarities[i]))
            for i in top_indices
        ]


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks by approximate token count."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
    return chunks


def chunk_transcripts(
    transcripts: dict[str, str],
    titles: dict[str, str] | None = None,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[Chunk]:
    """Split transcripts into overlapping chunks.

    Args:
        transcripts: Dict mapping video_id -> text content
        titles: Optional dict mapping video_id -> title
        chunk_size: Approximate words per chunk
        overlap: Words of overlap between chunks
    """
    titles = titles or {}
    chunks = []
    for source_id, text in transcripts.items():
        text_chunks = chunk_text(text, chunk_size, overlap)
        for i, chunk_text_ in enumerate(text_chunks):
            chunks.append(Chunk(
                text=chunk_text_,
                source_id=source_id,
                source_title=titles.get(source_id, source_id),
                chunk_index=i,
            ))
    return chunks


def build_index(
    chunks: list[Chunk],
    model_name: str = "all-MiniLM-L6-v2",
    use_cache: bool = True,
) -> EmbeddingIndex:
    """Build embedding index for chunks."""
    model = SentenceTransformer(model_name)

    if use_cache:
        texts_hash = cache_key("chunks", [c.text for c in chunks])
        cached = get_cached(f"embed_{texts_hash}")
        if cached is not None:
            embeddings = np.array(cached["embeddings"])
            return EmbeddingIndex(chunks, embeddings, model_name)

    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    if use_cache:
        set_cached(f"embed_{texts_hash}", {"embeddings": embeddings.tolist()})

    return EmbeddingIndex(chunks, embeddings, model_name)


def search_index(
    index: EmbeddingIndex,
    query: str,
    top_k: int = 5,
    model_name: str = "all-MiniLM-L6-v2",
) -> list[SearchResult]:
    """Search index for chunks similar to query."""
    model = SentenceTransformer(model_name)
    query_embedding = model.encode(query, normalize_embeddings=True)
    return index.search(query_embedding, top_k)


def ask_corpus(
    index: EmbeddingIndex,
    question: str,
    top_k: int = 5,
    model: str = "mistral",
    ollama_host: str = "http://localhost:11434",
) -> dict:
    """Ask a question of the corpus using RAG.

    Returns dict with 'answer' and 'sources'.
    """
    import ollama

    results = search_index(index, question, top_k)

    context_parts = []
    sources = []
    for r in results:
        context_parts.append(f"[{r.chunk.source_title}]\n{r.chunk.text}")
        if r.chunk.source_id not in sources:
            sources.append(r.chunk.source_id)

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""Based on the following transcript excerpts, answer the question. 
Cite specific sources when possible. If the answer isn't in the excerpts, say so.

## Excerpts
{context}

## Question
{question}

Provide a clear, specific answer based on the evidence above."""

    client = ollama.Client(host=ollama_host)
    response = client.generate(model=model, prompt=prompt)

    return {
        "answer": response.get("response", ""),
        "sources": sources,
        "chunks_used": len(results),
    }


def load_transcripts_for_rag(input_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Load transcripts from directory or manifest.

    Returns (transcripts dict, titles dict).
    """
    transcripts = {}
    titles = {}

    if input_path.is_file() and input_path.name == "manifest.json":
        with open(input_path) as f:
            manifest = json.load(f)
        for video in manifest.get("videos", []):
            vid = video["id"]
            titles[vid] = video.get("title", vid)
        transcript_dir = input_path.parent
    else:
        transcript_dir = input_path

    manifest_path = transcript_dir / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
        for video in manifest.get("videos", []):
            titles[video["id"]] = video.get("title", video["id"])

    for txt_file in transcript_dir.glob("*.txt"):
        video_id = txt_file.stem
        transcripts[video_id] = txt_file.read_text()
        if video_id not in titles:
            titles[video_id] = video_id

    return transcripts, titles
