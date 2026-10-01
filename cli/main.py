import argparse

from cli.llm import complete


def print_usage(usage):
    """Token counts for one call, lined up in a column."""
    # These come back as None rather than 0 when a category is unused.
    rows = [
        ("input tokens", usage.prompt_token_count),
        ("output tokens", usage.candidates_token_count),
        ("thought tokens", usage.thoughts_token_count),
        ("total tokens", usage.total_token_count),
    ]
    print()
    for label, value in rows:
        print(f"{label:<16}{value or 0:>6}")


def parse_args():
    parser = argparse.ArgumentParser(prog="cli")

    # nargs="+" collects every leftover word into a list, which keeps
    # the old behaviour of not needing quotes around a plain prompt.
    parser.add_argument("prompt", nargs="+")

    parser.add_argument("--temperature", type=float)
    parser.add_argument("--system")
    parser.add_argument("--max-tokens", type=int)

    # append lets you pass --stop more than once to build a list.
    parser.add_argument("--stop", action="append")

    return parser.parse_args()


def main():
    args = parse_args()

    response = complete(
        " ".join(args.prompt),
        system=args.system,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        stop=args.stop,
    )

    print(f"\n{response.text}")
    print_usage(response.usage_metadata)


if __name__ == "__main__":
    main()