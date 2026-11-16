from retriever.queries import QUERIES
from retriever.search import hybrid_search, keyword_search, vector_search

MODES = {
    "vector": vector_search,
    "keyword": keyword_search,
    "hybrid": hybrid_search,
}

KS = (1, 3, 5)


def hit_at(results, expected: str, k: int) -> bool:
    """Did the expected file appear in the top k?"""
    return any(r.source == expected for r in results[:k])


def main() -> None:
    hits = {mode: {k: 0 for k in KS} for mode in MODES}

    for query, expected in QUERIES:
        print(f'\n"{query}"')
        print(f"  want  {expected}")

        for name, search in MODES.items():
            results = search(query, limit=max(KS))

            marks = []
            for k in KS:
                if hit_at(results, expected, k):
                    hits[name][k] += 1
                    marks.append(f"@{k}")

            status = " ".join(marks) if marks else "MISS"
            got = results[0].source if results else "(nothing)"
            print(f"  {name:<8} {status:<14} top: {got}")

    n = len(QUERIES)
    print(f"\n\nhit rate over {n} queries\n")
    print(f"{'mode':<10}" + "".join(f"{'@' + str(k):>8}" for k in KS))
    for name in MODES:
        row = "".join(f"{hits[name][k] / n:>8.0%}" for k in KS)
        print(f"{name:<10}{row}")


if __name__ == "__main__":
    main()