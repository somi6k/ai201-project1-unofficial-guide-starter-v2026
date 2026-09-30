"""
Stages 3 and 4 of the pipeline: embedding chunks and retrieving them.

Three things in here are worth knowing about, because they'd quietly break the
rest of the project if they were wrong:

1. The Chroma collection is created with cosine distance, explicitly. Chroma
   defaults to squared L2, and the 0.6 threshold the course uses is calibrated
   against cosine. Getting this wrong makes every distance number meaningless.

2. `search` returns the distance alongside each chunk. Milestone 4 has you
   compare distances, so they have to be visible.

3. The embedding model is the one Chroma bundles, not one loaded through
   `sentence-transformers`. It is the same model — `all-MiniLM-L6-v2`, 384
   dimensions — but it arrives as an ONNX build from Chroma's own CDN, so the
   install needs neither PyTorch nor a reachable Hugging Face. See `_embedder`.
"""

import os
import shutil
from dataclasses import dataclass

# Must be set BEFORE chromadb is imported. Without it, some Chroma versions
# print "Failed to send telemetry event ..." on every single call — which looks
# exactly like a real error, isn't one, and cost a previous cohort a lot of
# confused help-channel messages.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb  # noqa: E402

import config
from chunker import Chunk


@dataclass
class Result:
    """One retrieved chunk and how far it was from the question."""

    text: str
    source: str
    label: str
    distance: float   # LOWER IS BETTER. 0.3 is close, 0.9 is unrelated.
    produced_by: str

    # ── Hybrid search only; all three are None/0.0 under meaning-only search.
    #
    # `distance` above stays the cosine distance from the question to this
    # chunk, always, under either retriever. That is deliberate and it is the
    # load-bearing decision in this file: THRESHOLD is calibrated against
    # cosine distances and the README's ten-row table is a table of cosine
    # distances, so hybrid search is allowed to change *which* chunks come
    # back and in *what order*, but not what a distance means. The fused
    # score is reported separately, below, rather than written over it.
    vector_rank: int | None = None    # 1-based rank in the vector list, or None
    keyword_rank: int | None = None   # 1-based rank in the BM25 list, or None
    fused_score: float = 0.0          # RRF score. HIGHER is better, unlike distance.

    @property
    def found_by(self) -> str:
        """Which retriever(s) nominated this chunk — for the README evidence."""
        if self.vector_rank and self.keyword_rank:
            return "both"
        if self.keyword_rank:
            return "keyword"
        if self.vector_rank:
            return "vector"
        return "—"


_model = None

# The model Chroma bundles. Anything else in config.EMBEDDING_MODEL means
# "fetch that one from Hugging Face instead" — see `_embedder`.
BUNDLED_MODEL = "all-MiniLM-L6-v2"


class _OnnxEmbedder:
    """
    Chroma's built-in embedder, wrapped to look like the other two.

    Chroma's embedding functions are called directly and hand back numpy
    arrays. The rest of this file wants `.encode(texts)`, so the adapter lives
    here rather than making every caller care which embedder it got.
    """

    def __init__(self):
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

        self._ef = ONNXMiniLM_L6_V2()

    def encode(self, texts, show_progress_bar: bool = False):
        return [vector.tolist() for vector in self._ef(list(texts))]


def _sentence_transformer(name: str):
    """
    The escape hatch: any model that isn't the bundled one.

    Unit 2's "try a second embedding model" stretch option comes through here,
    and so does anything you set `EMBEDDING_MODEL` to. This path *does* need
    `sentence-transformers` and a reachable Hugging Face, neither of which the
    default install has — which is the whole point of the default install.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            f"config.EMBEDDING_MODEL is set to {name!r}, which isn't the model "
            f"Chroma bundles ({BUNDLED_MODEL!r}), so it has to be downloaded "
            f"from Hugging Face.\n"
            f"Install the optional dependency first:\n"
            f"    pip install 'sentence-transformers>=3.4,<3.5'\n"
            f"Or set EMBEDDING_MODEL back to {BUNDLED_MODEL!r}."
        ) from exc

    return SentenceTransformer(name)


def _embedder():
    """
    Load the embedding model once and keep it.

    First call is slow — it downloads about 80 MB. That's why setup happens
    before class.
    """
    global _model

    if _model is not None:
        return _model

    # Used only by this repo's own smoke test, which runs where no model can be
    # downloaded at all. Never set this yourself.
    if os.getenv("AI201_FAKE_EMBEDDINGS") == "1":
        from _smoke_embedder import FakeEmbedder

        _model = FakeEmbedder()
    elif config.EMBEDDING_MODEL == BUNDLED_MODEL:
        _model = _OnnxEmbedder()
    else:
        _model = _sentence_transformer(config.EMBEDDING_MODEL)

    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """Turn text into vectors. Runs on your machine, costs no API quota."""
    vectors = _embedder().encode(texts, show_progress_bar=False)
    # sentence-transformers and the smoke stand-in return something with a
    # .tolist(); _OnnxEmbedder has already done that conversion itself.
    return vectors.tolist() if hasattr(vectors, "tolist") else vectors


def _client():
    return chromadb.PersistentClient(
        path=str(config.CHROMA_DIR),
        settings=chromadb.config.Settings(anonymized_telemetry=False),
    )


def build_index(
    chunks: list[Chunk],
    corpus: str | None = None,
    variant: str = "default",
) -> int:
    """
    Embed every chunk and store it.

    `variant` lets you keep more than one index of the same corpus at the same
    time. In unit 2, when you compare two chunking strategies, index the second
    one as variant="v2" and you can query both instead of deleting the first
    and starting over.
    """
    name = config.collection_name(corpus, variant)
    client = _client()

    try:
        client.delete_collection(name)
    except Exception:
        pass

    collection = client.create_collection(
        name=name,
        # ⚠️ Do not remove. Chroma defaults to squared L2, and every distance
        # number in this course assumes cosine.
        metadata={"hnsw:space": "cosine"},
    )

    batch = 256
    for start in range(0, len(chunks), batch):
        window = chunks[start : start + batch]
        collection.add(
            ids=[f"{c.source}#{c.index}" for c in window],
            documents=[c.text for c in window],
            embeddings=embed([c.text for c in window]),
            metadatas=[
                {"source": c.source, "index": c.index, "produced_by": c.produced_by}
                for c in window
            ],
        )

    return len(chunks)


def _open(corpus: str | None, variant: str):
    """Get the collection, or say which command would have created it."""
    name = config.collection_name(corpus, variant)
    try:
        return _client().get_collection(name)
    except Exception as exc:
        raise RuntimeError(
            f"No index called '{name}'. Run `python app.py index` first."
        ) from exc


def _make_result(text, meta, distance, **ranks) -> Result:
    return Result(
        text=text,
        source=str(meta.get("source", "unknown")),
        label=f"{meta.get('source', 'unknown')}#{meta.get('index', 0)}",
        distance=float(distance),
        produced_by=str(meta.get("produced_by", "unknown")),
        **ranks,
    )


def cosine_distance(a, b) -> float:
    """
    The same number Chroma's "cosine" space reports: 1 - cosine similarity.

    Needed because BM25 can nominate a chunk that the vector query never
    returned, and that chunk still has to carry a real cosine distance for the
    gate to read. Computing it here from the stored embedding is exact and
    costs no second trip through the embedder.
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm = (sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5)
    return 1.0 - dot / norm if norm else 1.0


def vector_search(
    question: str,
    top_k: int | None = None,
    corpus: str | None = None,
    variant: str = "default",
) -> list[Result]:
    """
    Retrieve the chunks closest in meaning to a question.

    Returns them nearest-first, each with its distance. This is the original
    meaning-only retriever, unchanged — `search` still routes here when
    `config.HYBRID_SEARCH` is off, which is what makes the before/after
    comparison in the run log a fair one.
    """
    top_k = top_k or config.TOP_K
    collection = _open(corpus, variant)

    raw = collection.query(
        query_embeddings=embed([question]),
        n_results=min(top_k, collection.count()),
    )

    return [
        _make_result(text, meta, distance, vector_rank=rank)
        for rank, (text, meta, distance) in enumerate(
            zip(raw["documents"][0], raw["metadatas"][0], raw["distances"][0]), start=1
        )
    ]


def hybrid_search(
    question: str,
    top_k: int | None = None,
    corpus: str | None = None,
    variant: str = "default",
) -> list[Result]:
    """
    Retrieve on meaning and on exact words at once, and fuse the two rankings.

    Both retrievers nominate `config.CANDIDATE_POOL` chunks. Reciprocal rank
    fusion then scores every nominated chunk by where it placed in each list —
    `weight / (RRF_K + rank)`, summed — so a chunk both retrievers liked beats
    one that only the stronger retriever put first.

    Results come back best-fused-first, which means they are NOT in ascending
    distance order any more. `gate.check` takes the minimum rather than the
    first element, so it is unaffected; anything else that assumed
    `results[0]` was the closest chunk would need to say `min(...)` instead.
    """
    import keyword_search

    top_k = top_k or config.TOP_K
    collection = _open(corpus, variant)
    pool = min(max(config.CANDIDATE_POOL, top_k), collection.count())

    question_vector = embed([question])[0]

    # ── Retriever 1: meaning.
    raw = collection.query(query_embeddings=[question_vector], n_results=pool)
    records: dict[str, dict] = {}
    vector_ranks: dict[str, int] = {}
    for rank, (chunk_id, text, meta, distance) in enumerate(
        zip(raw["ids"][0], raw["documents"][0], raw["metadatas"][0], raw["distances"][0]),
        start=1,
    ):
        records[chunk_id] = {"text": text, "meta": meta, "distance": float(distance)}
        vector_ranks[chunk_id] = rank

    # ── Retriever 2: exact words.
    keyword_hits = keyword_search.load_index(collection).search(question, pool)
    keyword_ranks = {chunk_id: rank for rank, (chunk_id, _) in enumerate(keyword_hits, start=1)}

    # A BM25 hit from outside the vector pool has no distance yet. Fetch the
    # stored embedding and work it out, rather than guessing or leaving a hole
    # the gate would then read as "nothing close".
    missing = [chunk_id for chunk_id in keyword_ranks if chunk_id not in records]
    if missing:
        fetched = collection.get(ids=missing, include=["documents", "metadatas", "embeddings"])
        for chunk_id, text, meta, vector in zip(
            fetched["ids"], fetched["documents"], fetched["metadatas"], fetched["embeddings"]
        ):
            records[chunk_id] = {
                "text": text,
                "meta": meta,
                "distance": cosine_distance(question_vector, vector),
            }

    # ── Fuse on rank.
    fused: dict[str, float] = {}
    for chunk_id, rank in vector_ranks.items():
        fused[chunk_id] = fused.get(chunk_id, 0.0) + config.VECTOR_WEIGHT / (config.RRF_K + rank)
    for chunk_id, rank in keyword_ranks.items():
        fused[chunk_id] = fused.get(chunk_id, 0.0) + config.KEYWORD_WEIGHT / (config.RRF_K + rank)

    # Ties broken by distance, so the order is stable run to run rather than
    # dependent on dict insertion order.
    order = sorted(fused, key=lambda cid: (-fused[cid], records[cid]["distance"]))

    return [
        _make_result(
            records[chunk_id]["text"],
            records[chunk_id]["meta"],
            records[chunk_id]["distance"],
            vector_rank=vector_ranks.get(chunk_id),
            keyword_rank=keyword_ranks.get(chunk_id),
            fused_score=fused[chunk_id],
        )
        for chunk_id in order[:top_k]
    ]


def search(
    question: str,
    top_k: int | None = None,
    corpus: str | None = None,
    variant: str = "default",
    hybrid: bool | None = None,
) -> list[Result]:
    """
    Retrieve the chunks worth answering a question from.

    The one entry point every caller uses. `config.HYBRID_SEARCH` picks the
    retriever; pass `hybrid=` to override it for a single call, which is how
    the two get compared side by side without editing config.
    """
    use_hybrid = config.HYBRID_SEARCH if hybrid is None else hybrid
    retrieve = hybrid_search if use_hybrid else vector_search
    return retrieve(question, top_k=top_k, corpus=corpus, variant=variant)


def index_exists(corpus: str | None = None, variant: str = "default") -> bool:
    """Is there an index here to search, without searching it?

    `serve.py`'s health check asks this. It deliberately does not embed
    anything: loading the embedding model takes 80 MB and a few seconds, and a
    health check that heavy is a health check nobody can afford to call.
    """
    try:
        collection = _client().get_collection(config.collection_name(corpus, variant))
        return collection.count() > 0
    except Exception:
        return False


def reset():
    """Delete every index. Occasionally the fastest way out of a mess."""
    if config.CHROMA_DIR.exists():
        shutil.rmtree(config.CHROMA_DIR)
