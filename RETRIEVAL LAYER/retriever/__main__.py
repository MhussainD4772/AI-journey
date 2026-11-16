import argparse

from retriever.search import hybrid_search, keyword_search, vector_search

MODES = {
    "vector": vector_search,
    "keyword": keyword_search,
    "hybrid": hybrid_search,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="retriever")
    parser.add_argument("query", nargs="+")
    parser.add_argument("--mode", choices=MODES, default="hybrid")
    parser.add_argument("--source", help="only search files whose path contains this")
    parser.add_argument("--limit", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    query = " ".join(args.query)

    results = MODES[args.mode](query, limit=args.limit, source=args.source)

    print(f'\n{args.mode}: "{query}"')
    if args.source:
        print(f"  filtered to: {args.source}")
    print()

    if not results:
        print("  no results\n")
        return

    for r in results:
        print(f"{r.score:.4f}  {r.source}")
        print(f"          {r.heading}")
        print()


if __name__ == "__main__":
    main()