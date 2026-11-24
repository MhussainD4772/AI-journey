from golden import GOLDEN
from search import hybrid_search, keyword_search, vector_search

MODES = {
    "vector": vector_search,
    "keyword": keyword_search,
    "hybrid": hybrid_search,
}

KS = (1, 3, 5)


def rank_of(results, paper_id: str) -> int | None:
    """1-based position of the first result from the right paper."""
    for i, r in enumerate(results, start=1):
        if r.paper_id == paper_id:
            return i
    return None


def main() -> None:
    answerable = [(q, p) for q, p, _ in GOLDEN if p is not None]

    hits = {mode: {k: 0 for k in KS} for mode in MODES}
    reciprocal = {mode: 0.0 for mode in MODES}

    for question, paper in answerable:
        print(f'\n"{question[:65]}"')
        print(f"  want  {paper}")

        for name, search in MODES.items():
            results = search(question, limit=max(KS))
            rank = rank_of(results, paper)

            if rank is not None:
                reciprocal[name] += 1 / rank
                for k in KS:
                    if rank <= k:
                        hits[name][k] += 1

            top = results[0].paper_id if results else "(nothing)"
            print(f"  {name:<8} rank {str(rank or '-'):<4} top: {top}")

    n = len(answerable)
    print(f"\n\n{n} answerable questions\n")
    print(f"{'mode':<10}" + "".join(f"{'@' + str(k):>8}" for k in KS) + f"{'MRR':>8}")
    for name in MODES:
        row = "".join(f"{hits[name][k] / n:>8.0%}" for k in KS)
        print(f"{name:<10}{row}{reciprocal[name] / n:>8.2f}")


if __name__ == "__main__":
    main()