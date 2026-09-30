"""
Stage 4, the other half: keyword retrieval with BM25.

The vector search in `store.py` matches on meaning, which is what makes it
good at "anywhere to stay in Givens Mill?" — no chunk contains the word
"anywhere", and it finds the right one anyway. What it is bad at is the
opposite case: a rare word that has to match *exactly*.

Two examples from this corpus:

  - "Thornby Wells" and "Pellew Sands" are proper nouns the embedder has never
    seen. They land in roughly the same region of vector space as every other
    two-word English place name, so nine town guides compete on meaning alone
    and the right one wins by a small margin, or doesn't.
  - "90 minutes" is a token, not a concept. Embeddings are famously weak on
    numbers: "90 minutes" and "30 minutes" sit almost on top of each other.

BM25 has the reverse profile. It cannot match "anywhere" to "Nothing in the
village itself", but a document containing the literal word "Thornby" scores
far above one that doesn't, precisely *because* the word is rare — that is
what the IDF term measures. Combining the two is the point: each covers the
other's blind spot.

The index is built from the documents already stored in Chroma rather than
from the corpus files, so it cannot drift out of sync with what the vector
search is searching. It is rebuilt whenever the chunk count changes.

Named `keyword_search` and not `keyword` because `keyword` is a standard
library module, and a file by that name in the project root shadows it for
every package in the venv.
"""

import re

from rank_bm25 import BM25Okapi

# Lowercase alphanumeric runs. Deliberately keeps digits as their own tokens,
# so "90" in a question can match "90" in a chunk — half the reason this file
# exists. Apostrophes split ("don't" -> "don", "t"), which is harmless here:
# both halves are stopwords or near-enough.
WORD_RE = re.compile(r"[a-z0-9]+")

# BM25's IDF term already drives common words towards zero weight, so this
# list is not load-bearing for the ranking. It is here for the question words
# specifically — "what", "how", "do", "i" appear in most of the questions and
# in none of the chunks, and dropping them keeps a question's token count
# closer to its number of *content* words, which is what BM25's length
# normalisation is tuned against.
STOPWORDS = frozenset(
    """
    a about an and any are as at be been but by can did do does for from
    get give got had has have how i if in into is it its me my no not of on
    one or our so than that the their them then there these they this to
    too was were what when where which who why will with would you your
    """.split()
)


def tokenize(text: str) -> list[str]:
    """Text to comparable tokens. The same function runs on chunks and questions."""
    return [word for word in WORD_RE.findall(text.lower()) if word not in STOPWORDS]


class KeywordIndex:
    """A BM25 index over the chunks, addressed by the same ids Chroma uses."""

    def __init__(self, ids: list[str], texts: list[str]):
        self.ids = ids
        # BM25Okapi divides by the corpus average document length, so an empty
        # corpus is a ZeroDivisionError rather than an empty result. Guard it:
        # `index_exists` is the caller's job, not this constructor's.
        self.bm25 = BM25Okapi([tokenize(text) for text in texts]) if ids else None

    def __len__(self) -> int:
        return len(self.ids)

    def search(self, question: str, n: int) -> list[tuple[str, float]]:
        """
        The n best-matching chunk ids, best first, as (id, score) pairs.

        Scores are unbounded and corpus-relative — a 7.4 means nothing on its
        own, which is exactly why `store.hybrid_search` fuses on *rank* rather
        than trying to put these on the same scale as a cosine distance.

        Chunks scoring zero share no terms with the question at all and are
        dropped rather than returned in arbitrary order. That matters for the
        out-of-scope questions: "Who won the 1994 World Cup?" has no content
        word anywhere in this corpus, so this returns nothing and the fused
        ranking is the vector ranking unchanged.
        """
        if self.bm25 is None:
            return []

        scores = self.bm25.get_scores(tokenize(question))
        ranked = sorted(
            ((self.ids[i], float(score)) for i, score in enumerate(scores) if score > 0),
            key=lambda pair: pair[1],
            reverse=True,
        )
        return ranked[:n]


# Keyed by collection name. The stored chunk count comes along so that
# re-indexing invalidates the cache instead of serving a stale index.
_cache: dict[str, tuple[int, KeywordIndex]] = {}


def load_index(collection) -> KeywordIndex:
    """
    Build (or reuse) the BM25 index for an open Chroma collection.

    Tokenising this corpus takes a few milliseconds, so this is built on first
    use rather than persisted at index time. If you bring a corpus big enough
    for that to hurt, this is the function to change — nothing else knows how
    the index is stored.
    """
    count = collection.count()
    cached = _cache.get(collection.name)
    if cached and cached[0] == count:
        return cached[1]

    stored = collection.get(include=["documents"])
    index = KeywordIndex(ids=list(stored["ids"]), texts=list(stored["documents"]))
    _cache[collection.name] = (count, index)
    return index
