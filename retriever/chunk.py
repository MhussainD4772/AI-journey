import re
from dataclasses import dataclass
from pathlib import Path

# "# Request Body { #request-body }"  ->  strip the trailing anchor
ANCHOR = re.compile(r"\s*\{\s*#[^}]*\}\s*$")

# "{* ../../docs_src/body/tutorial001.py hl[2] *}"  ->  drop the whole line
INCLUDE = re.compile(r"^\{\*.*\*\}\s*$", re.MULTILINE)

# "/// note" and "///"  ->  drop the marker, keep the text between
ADMONITION = re.compile(r"^///.*$", re.MULTILINE)

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")

# How many levels of the heading hierarchy to keep. FastAPI nests four deep
# in places, which produced 200-character trails repeated on every piece.
# The deepest levels carry the meaning; the page title is already in `source`.
TRAIL_DEPTH = 2

# From the size histogram: 149 of 1147 chunks fell below this, almost all
# stubs left behind by stripping the code includes.
MIN_CHARS = 200

# MiniLM reads ~256 tokens, roughly 1000 characters of English. This is the
# budget for the WHOLE chunk — heading trail included, not just the body.
MAX_CHARS = 1000


@dataclass
class Chunk:
    text: str       # heading trail + body; this is what gets embedded
    source: str     # path relative to the docs root
    heading: str    # "Background Tasks > Use Cases with Early Exit Code"


def clean(raw: str) -> str:
    """Remove mkdocs markup that carries no meaning on its own."""
    raw = INCLUDE.sub("", raw)
    raw = ADMONITION.sub("", raw)
    return raw


def split_large(text: str, reserved: int = 0) -> list[str]:
    """Break an oversized body into paragraph groups.

    `reserved` is how many characters the heading prefix will take once it
    gets prepended, so the finished chunk lands under MAX_CHARS rather than
    the body alone.
    """
    budget = max(MAX_CHARS - reserved, 200)

    if len(text) <= budget:
        return [text]

    pieces: list[str] = []
    current: list[str] = []
    size = 0

    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue

        if current and size + len(para) > budget:
            pieces.append("\n\n".join(current))
            current, size = [], 0

        current.append(para)
        size += len(para) + 2       # +2 for the blank line between

    if current:
        pieces.append("\n\n".join(current))

    return pieces


def merge_small(chunks: list[Chunk]) -> list[Chunk]:
    """Fold chunks under MIN_CHARS into the chunk that follows them."""
    out: list[Chunk] = []
    pending: list[Chunk] = []

    for chunk in chunks:
        if len(chunk.text) < MIN_CHARS:
            pending.append(chunk)
            continue

        if pending:
            text = "\n\n".join(p.text for p in pending) + "\n\n" + chunk.text
            chunk = Chunk(text=text, source=chunk.source, heading=chunk.heading)
            pending = []

        out.append(chunk)

    if pending:
        # Stubs at the end of the file have nothing after them.
        tail = "\n\n".join(p.text for p in pending)
        if out:
            last = out[-1]
            out[-1] = Chunk(
                text=last.text + "\n\n" + tail,
                source=last.source,
                heading=last.heading,
            )
        else:
            out = pending          # the whole file was stubs

    return out


def chunk_file(path: Path, root: Path) -> list[Chunk]:
    """Split one markdown file into chunks, one per heading section."""
    raw = clean(path.read_text(encoding="utf-8"))
    source = str(path.relative_to(root))

    chunks: list[Chunk] = []
    trail: dict[int, str] = {}
    heading = ""
    body: list[str] = []
    in_fence = False

    def finish() -> None:
        text = "\n".join(body).strip()
        if not text:
            return
        prefix = f"{heading}\n\n" if heading else ""
        for piece in split_large(text, reserved=len(prefix)):
            chunks.append(Chunk(text=prefix + piece, source=source, heading=heading))

    for line in raw.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            body.append(line)
            continue

        match = None if in_fence else HEADING.match(line)

        if match is None:
            body.append(line)
            continue

        finish()                     # the heading ends the previous section

        level = len(match.group(1))
        title = ANCHOR.sub("", match.group(2)).strip()

        trail = {k: v for k, v in trail.items() if k < level}
        trail[level] = title

        # Keep only the deepest TRAIL_DEPTH levels.
        levels = sorted(trail)[-TRAIL_DEPTH:]
        heading = " > ".join(trail[k] for k in levels)

        body = []

    finish()                         # the last section has nothing after it
    return merge_small(chunks)