import sys
from pathlib import Path

import pymupdf

path = Path(sys.argv[1])
page_no = int(sys.argv[2]) if len(sys.argv) > 2 else 0

print("=" * 72)
print(f"{path.name}  page {page_no}")
print("=" * 72)
print(pymupdf.open(path)[page_no].get_text())