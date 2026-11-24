import re
from dataclasses import dataclass

# End punctuation, whitespace, then a capital. Breaks on "et al. 2023"
# and "Fig. 3" — approximate on purpose, it only picks boundaries.
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")

WHITESPACE = re.compile(r"\s+")

MAX_CHARS = 1000
OVERLAP_SENTENCES = 2


@dataclass
class Chunk:
    text: str
    page: int        # page the chunk starts on, zero-based
    index: int       # position of this chunk within the document

def _make(items: list[tuple[str, int]], index: int) -> Chunk:
    return Chunk(
        text=" ".join(sentence for sentence, _ in items),
        page=items[0][1],
        index=index,
    )

def _hard_split(sentence: str) -> list[str]:
    """A 'sentence' longer than the budget has no boundary to split on."""
    return [sentence[i : i + MAX_CHARS] for i in range(0, len(sentence), MAX_CHARS)]


def chunk_pages(pages: list[str]) -> list[Chunk]:
    """Flat page text -> overlapping chunks that know their page."""
    located: list[tuple[str, int]] = []

    for page_no, page in enumerate(pages):
        text = WHITESPACE.sub(" ", page).strip()
        if not text:
            continue
        for sentence in SENTENCE_END.split(text):
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(sentence) > MAX_CHARS:
                for piece in _hard_split(sentence):
                    located.append((piece, page_no))
            else:
                located.append((sentence, page_no))

    chunks: list[Chunk] = []
    current: list[tuple[str, int]] = []
    size = 0

    for sentence, page_no in located:
        if current and size + len(sentence) > MAX_CHARS:
            chunks.append(_make(current, len(chunks)))

            current = current[-OVERLAP_SENTENCES:]          # carry the tail
            size = sum(len(s) + 1 for s, _ in current)

            # If the overlap plus this sentence still won't fit, drop it.
            if size + len(sentence) > MAX_CHARS:
                current, size = [], 0

        current.append((sentence, page_no))
        size += len(sentence) + 1

    if current:
        chunks.append(_make(current, len(chunks)))

    return chunks