"""
Stage 2 of the pipeline: splitting documents into chunks.

`split_documents` cuts on markdown section boundaries and prepends the
document title and section heading to every chunk. `fallback_split` is the
starter's original fixed-size character window, kept for comparison.

Why sections, for `city_guides`:

  - The 84 `##` sections run 175 to 710 characters. Nothing reaches the 800
    of CHUNK_SIZE, so the fixed window never lands on a boundary — it lands
    across them. 64% of the baseline's 51 chunks end mid-sentence.
  - Nine of the fourteen documents are town guides sharing one 7-section
    template, and the town is named in the H1 and almost nowhere else: 80 of
    84 sections never mention their own subject. Unprefixed, the chunk that
    answers "anywhere to stay in Givens Mill?" reads "Nothing in the village
    itself. The nearest rooms are in Brightwater..." — nine such anonymous
    chunks compete, and the only town named in that one is the wrong one.
  - The `## Practical notes` body is byte-identical across all nine town
    guides. The title prefix is what tells those nine chunks apart.

On a corpus with no markdown headings — `campus_life`, `advice_threads`,
`practice` are plain .txt — a document has no sections to split on and stays
whole, which is the right call for posts of ~300 characters. CHUNK_SIZE then
acts only as a ceiling: the four oversized files in `practice` get packed on
paragraph breaks rather than cut blind.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document

# A section heading (`## Eat and drink`) and a document title (`# Givens Mill`).
HEADING_RE = re.compile(r"^##\s+(.+)$", re.M)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.M)

# One or more blank lines. `ingest.clean_text` has already collapsed runs of
# three or more newlines down to two, so this is the paragraph break.
PARAGRAPH_RE = re.compile(r"\n\s*\n")


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def split_sections(text: str) -> tuple[str | None, list[tuple[str | None, str]]]:
    """
    Pull a document apart into its title and its `##` sections.

    Returns the title (None if the document has no `#` heading) and a list of
    (heading, body) pairs in document order. Text sitting between the title
    and the first `##` — the opening paragraph of every town guide, which is
    where the population and the one-line description live — comes back as a
    leading section with no heading of its own rather than being dropped.

    A document with no `##` at all comes back as a single unheaded section
    holding the whole thing. That is what keeps the plain-text corpora
    behaving sensibly.
    """
    headings = list(HEADING_RE.finditer(text))

    # Everything before the first `##` is title plus preamble.
    head_region = text[: headings[0].start()] if headings else text
    title_match = TITLE_RE.search(head_region)
    if title_match:
        title = title_match.group(1).strip()
        preamble = head_region[: title_match.start()] + head_region[title_match.end() :]
    else:
        title = None
        preamble = head_region

    sections: list[tuple[str | None, str]] = []
    if preamble.strip():
        sections.append((None, preamble.strip()))

    for position, match in enumerate(headings):
        following = headings[position + 1].start() if position + 1 < len(headings) else len(text)
        body = text[match.end() : following].strip()
        if body:
            sections.append((match.group(1).strip(), body))

    return title, sections


def pack_paragraphs(body: str, ceiling: int) -> list[str]:
    """
    Keep a section whole if it fits, and break it on paragraphs if it doesn't.

    No section in `city_guides` reaches the ceiling, so this returns a
    one-item list for all 84 of them. It earns its place on the four
    oversized files in `practice`, and it means the strategy doesn't quietly
    depend on the current corpus staying small.
    """
    if len(body) <= ceiling:
        return [body]

    pieces: list[str] = []
    current = ""

    for paragraph in PARAGRAPH_RE.split(body):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # A single paragraph longer than the ceiling has no boundary left to
        # cut on. This is the one place we fall back to counting characters.
        if len(paragraph) > ceiling:
            if current:
                pieces.append(current)
                current = ""
            pieces.extend(split_on_characters(paragraph, ceiling))
            continue

        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) > ceiling:
            pieces.append(current)
            current = paragraph
        else:
            current = candidate

    if current:
        pieces.append(current)

    return pieces


def split_on_characters(text: str, ceiling: int) -> list[str]:
    """Last resort: fixed windows, for a paragraph with no break to cut on."""
    overlap = min(config.CHUNK_OVERLAP, ceiling // 4)
    step = max(ceiling - overlap, 1)
    return [
        piece
        for start in range(0, len(text), step)
        if (piece := text[start : start + ceiling].strip())
    ]


def section_label(title: str | None, heading: str | None) -> str:
    """`Givens Mill: Where to stay`, or as much of it as the document has."""
    return ": ".join(part for part in (title, heading) if part)


def with_context(label: str, piece: str) -> str:
    """
    Put the title and heading into the chunk's own text.

    This is the part that matters for retrieval, not just for reading. The
    embedder only ever sees this string, so a section that never names its
    own town needs the town in here — metadata alone would not be searchable.
    """
    return f"{label}\n\n{piece}" if label else piece


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split documents on section boundaries, titled and headed.

    One chunk per `##` section, with `Title: Heading` prepended, and
    `config.CHUNK_SIZE` demoted from the size of a chunk to a ceiling that
    almost never fires. See the module docstring for why this corpus wants
    that. `fallback_split` is still here to compare against.
    """
    ceiling = config.CHUNK_SIZE
    chunks: list[Chunk] = []

    for doc in documents:
        title, sections = split_sections(doc.text)
        index = 0
        for heading, body in sections:
            label = section_label(title, heading)

            # The label goes into the chunk text, so it has to come out of the
            # budget — otherwise CHUNK_SIZE bounds the body and the emitted
            # chunk runs over it by the length of the prefix. The floor stops
            # a long title from shredding a section into fragments; a label
            # that eats three quarters of the ceiling is a corpus problem, not
            # something to solve by making the chunks useless.
            budget = ceiling - len(label) - 2 if label else ceiling
            budget = max(budget, ceiling // 4, 1)

            for piece in pack_paragraphs(body, budget):
                chunks.append(
                    Chunk(
                        text=with_context(label, piece),
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::split_documents",
                    )
                )
                index += 1

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
