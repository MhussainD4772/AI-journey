import re
from pathlib import Path

import pymupdf

# Page furniture — present on the page, meaningless as content.
# Expect to add to this list as you look at more papers.
JUNK_LINE = re.compile(
    r"""^(
        arXiv:\S+\s+\[[^\]]+\].*           # the vertical arXiv stamp
      | Copyright\s+©.*                     # venue copyright notice
      | .*All\s+rights\s+reserved\..*
      | \*\s*Corresponding\s+authors?\..*
      | \d{1,3}                             # a bare page number on its own line
    )$""",
    re.VERBOSE | re.MULTILINE | re.IGNORECASE,
)

# "challeng-\ning" -> "challenging". Lowercase on the second line only.
HYPHEN_BREAK = re.compile(r"(\w)-\n([a-z])")

# "Retrieval-\nAugmented" -> "Retrieval-Augmented". A capital or digit after
# the break usually means a real compound, so keep the hyphen.
HYPHEN_COMPOUND = re.compile(r"(\w)-\n([A-Z0-9])")

# A line that is nothing but the heading.
REFERENCES = re.compile(
    r"^\s*(References|REFERENCES|Bibliography|BIBLIOGRAPHY)\s*$",
    re.MULTILINE,
)

# What comes after the bibliography in papers that have appendices.
APPENDIX = re.compile(
    r"^\s*(Appendix|APPENDIX|Supplementary|SUPPLEMENTARY)\b.*$",
    re.MULTILINE,
)


def clean_page(text: str) -> str:
    text = JUNK_LINE.sub("", text)
    text = HYPHEN_BREAK.sub(r"\1\2", text)
    text = HYPHEN_COMPOUND.sub(r"\1-\2", text)
    return text


def cut_references(pages: list[str]) -> list[str]:
    """Remove the bibliography, keeping any appendix that follows it."""
    start = None
    for i in range(len(pages) - 1, -1, -1):
        found = list(REFERENCES.finditer(pages[i]))
        if found:
            start = (i, found[-1].start())
            break

    if start is None:
        return pages

    si, s_off = start

    # Where does the bibliography end? First appendix heading after it.
    end = None
    for j in range(si, len(pages)):
        found = APPENDIX.search(pages[j], s_off if j == si else 0)
        if found:
            end = (j, found.start())
            break

    out = list(pages)
    out[si] = out[si][:s_off]

    if end is None:
        return out[: si + 1]          # nothing after the bibliography

    ej, e_off = end
    for k in range(si + 1, ej):
        out[k] = ""                   # pages that are purely bibliography
    out[ej] = out[ej][e_off:]         # keep the appendix onward
    return out


def extract_pages(path: Path) -> list[str]:
    """One cleaned string per page, bibliography removed."""
    doc = pymupdf.open(path)
    pages = [page.get_text() for page in doc]
    doc.close()

    return cut_references([clean_page(p) for p in pages])