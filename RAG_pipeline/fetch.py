import json
from pathlib import Path

import arxiv
import requests

OUT = Path("papers")
OUT.mkdir(exist_ok=True)

HEADERS = {"User-Agent": "rag-pipeline/0.1 (learning project)"}

client = arxiv.Client(page_size=10, delay_seconds=5.0, num_retries=3)
search = arxiv.Search(
    query='abs:"retrieval augmented generation"',
    max_results=10,
    sort_by=arxiv.SortCriterion.Relevance,
)

meta = []

for paper in client.results(search):
    paper_id = paper.get_short_id()
    path = OUT / f"{paper_id}.pdf"

    meta.append({
        "id": paper_id,
        "title": paper.title,
        "authors": [a.name for a in paper.authors],
        "published": paper.published.isoformat(),
        "categories": paper.categories,
        "abstract": paper.summary,
        "pdf_url": paper.pdf_url,
    })

    if path.exists():
        print(f"skip  {paper_id}")
        continue

    response = requests.get(paper.pdf_url, headers=HEADERS, timeout=60)
    response.raise_for_status()
    path.write_bytes(response.content)

    print(f"ok    {paper_id}  {paper.title[:60]}")

Path("metadata.json").write_text(json.dumps(meta, indent=2))
print(f"\n{len(meta)} papers, metadata written")