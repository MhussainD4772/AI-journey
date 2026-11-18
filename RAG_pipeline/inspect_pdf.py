import sys
from pathlib import Path

import pymupdf
import pypdf

path = Path(sys.argv[1])
page_no = int(sys.argv[2]) if len(sys.argv) > 2 else 0

print("=" * 72)
print(f"PYPDF  —  {path.name} page {page_no}")
print("=" * 72)
print(pypdf.PdfReader(path).pages[page_no].extract_text())

print()
print("=" * 72)
print(f"PYMUPDF  —  {path.name} page {page_no}")
print("=" * 72)
print(pymupdf.open(path)[page_no].get_text())