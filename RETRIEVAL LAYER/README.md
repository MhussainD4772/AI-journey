# retriever

Semantic search over documentation. Ask a question the way you'd ask a colleague, get back the passages that answer it.

```
$ python -m retriever "how do I return a custom status code"

hybrid: "how do I return a custom status code"

0.0164  tutorial/response-status-code.md
          Response Status Code > Changing the default

0.0161  advanced/response-change-status-code.md
          Response - Change Status Code

0.0159  advanced/additional-status-codes.md
          Additional Status Codes > Additional status codes
```

Built against the FastAPI documentation, but it takes any folder of markdown.

---

## Why

Documentation search is keyword search. You have to already know the word the docs used. Search for "how do I stop my API returning everything" and you get nothing, because the page is called "response model filtering."

This matches on meaning instead. It also still does keyword matching, because meaning-based search is bad at the thing keyword search is good at — error codes, function names, anything that's an arbitrary identifier rather than a word.

It stops at retrieval. It finds the passages and hands them to you; it doesn't write an answer. That's deliberate — generating an answer is the layer above, and it's only ever as good as what retrieval gives it.

---

## How it works

**Ingest, once.** Walk the docs folder, split each markdown file into chunks on heading boundaries, turn each chunk into a 384-number vector with a local embedding model, and write text, source, heading and vector into Postgres.

**Query, per question.** Embed the question with the same model. Run two searches against the same table — one on the vector column, one on the text — then merge their rankings and return the top passages with their source.

```
ingest                   query
──────                   ─────
markdown files           your question
    ↓                          ↓
  chunk              ┌─────────┴─────────┐
    ↓                ↓                   ↓
  embed         vector search      keyword search
    ↓                └─────────┬─────────┘
  store                        ↓
    ↓                   merge rankings
    └──────→ Postgres ←────────┘
             + pgvector         ↓
                          ranked passages
```

---

## Setup

Postgres with the pgvector extension:

```bash
docker run -d \
  --name retriever-db \
  -e POSTGRES_PASSWORD=localdev \
  -p 5433:5432 \
  -v retriever-pgdata:/var/lib/postgresql/data \
  pgvector/pgvector:pg17
```

Schema:

```sql
CREATE EXTENSION vector;

CREATE TABLE chunks (
    id        bigserial PRIMARY KEY,
    content   text NOT NULL,
    source    text,
    heading   text,
    embedding vector(384)
);

ALTER TABLE chunks ADD COLUMN tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON chunks USING gin (tsv);
```

Python:

```bash
python3 -m venv venv && source venv/bin/activate
pip install sentence-transformers psycopg[binary] pgvector
```

Documents — not vendored, fetch them yourself:

```bash
git clone --depth 1 https://github.com/fastapi/fastapi.git /tmp/fastapi-docs
```

---

## Use

```bash
# build the index (~90 seconds for 1,204 chunks)
python -m retriever.ingest /tmp/fastapi-docs/docs/en/docs

# search
python -m retriever "how do I handle errors"

# pick a strategy
python -m retriever "HTTPException" --mode vector
python -m retriever "HTTPException" --mode keyword
python -m retriever "HTTPException" --mode hybrid     # default

# restrict to part of the docs
python -m retriever "status codes" --source advanced

# measure
python -m retriever.eval
```

---

## Results

Ten test queries, each with a known correct source file. Hit rate is how often that file appeared in the top k.

| mode | @1 | @3 | @5 |
|---|---|---|---|
| vector | 30% | 60% | 70% |
| keyword | 20% | 30% | 30% |
| **hybrid** | **40%** | 60% | **80%** |

**Did hybrid beat pure vector?** Marginally, and not conclusively. It was never worse, and it fixed one case outright — searching `HTTPException`, vector search returned an HTTP Basic Auth page first because the strings look alike, while hybrid put the correct page first. But at ten queries a ten-point difference is one query. Treat anything under twenty points as noise.

**Keyword alone returned nothing for four of ten queries.** Postgres full-text search joins terms with AND, so if no single chunk contains every non-stop word in the question, you get zero rows. That's not a bug and it's why it doesn't run alone.

**Rank-1 accuracy is weak across the board.** The answer is usually in the top five but rarely first. That's a ranking problem rather than a retrieval problem, and it's what a reranker would fix — score the top twenty properly against the query instead of comparing pre-computed vectors.

**The real hit rate is higher than 80%.** Three of the recorded misses look like wrong expectations rather than bad search: a query for reading configuration returned `advanced/settings.md` when the test expected `environment-variables.md`, and settings is arguably the better answer. Scoring against a single correct file undercounts whenever a question has two legitimate answers.

---

## Decisions

**Chunk on headings, not on character count.** The author already marked where topics change. A heading is a boundary someone chose; character 500 is not. Fixed-size chunking cuts mid-sentence and mid-code-block.

**Split anything over 1,000 characters by paragraph.** 1,000 characters is roughly 256 tokens, which is all the embedding model reads. Past that it silently discards the rest and hands back a perfectly normal-looking vector describing only the first half. Before this rule, 20% of chunks were partially invisible to search with no error anywhere.

**Merge anything under 200 characters forward.** That number came from a size histogram of this corpus: 149 of 1,147 chunks fell below it and reading them showed they were almost all stubs — a sentence introducing code that had been stripped out.

**Prepend the heading trail into the chunk text before embedding.** A chunk reading "Set this to true in production" is meaningless alone and so is its vector. Prefixed with `Security > OAuth2 scopes`, the vector carries what the chunk is about rather than only what it says.

**Keep two heading levels, not the full trail.** FastAPI nests four deep in places, which produced 200-character trails repeated on every split piece — a large share of what the model read was the same heading over and over. The page title is already recorded in the source path.

**Strip the code includes.** FastAPI's raw markdown doesn't contain code; it contains `{* path/to/file.py *}` directives that get inlined when the site builds. Resolving them is possible and deliberately deferred.

**Merge rankings by position, not by score.** Cosine similarity runs 0 to 1; Postgres `ts_rank` has no fixed range at all. They aren't comparable, so any weighted sum would be arbitrary. Reciprocal Rank Fusion ignores the scores and uses rank position, which also means a chunk appearing in both lists beats one that tops only one.

**No overlap between chunks.** Overlap exists so an answer split across a boundary still appears whole somewhere. Structural splitting largely sidesteps that, since boundaries fall where the subject genuinely changes. It costs duplicated storage and makes the same content match twice, so it stays out until the evaluation asks for it.

**Full rebuild on ingest, not incremental.** `TRUNCATE` then insert, in one transaction, so a failed insert rolls the truncate back with it. Incremental ingest — tracking file modification times and only re-embedding what changed — matters at scale and not at 1,204 chunks.

---

## Known limits

**48 chunks exceed the model's window.** They're single paragraphs with no internal blank line, almost all long code blocks, so paragraph splitting can't help them. Their first 1,000 characters are indexed; the tail isn't. The real fix is an embedding model with a larger window — a model-choice decision, not a chunking one.

**Precision is not measured.** With one expected answer per query you can measure hit rate. Measuring precision means labelling every chunk as relevant or not for every query — 12,040 judgements for this corpus. Not done, and not claimed.

**The test queries were written by the same person who built the chunker.** Softer than queries written blind.

**Ten queries is a small sample.** Enough to catch a mode that's badly broken. Not enough to resolve a ten-point difference.

---

## Stack

Python · sentence-transformers (all-MiniLM-L6-v2, 384 dimensions, runs locally) · Postgres 17 · pgvector · HNSW index for vectors, GIN index for full text

Everything runs locally. No API keys, no per-query cost.