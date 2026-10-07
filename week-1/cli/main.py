import argparse

from cli.cost import add_to_session, call_cost_usd
from cli.llm import complete, response_text


def print_usage(usage):
    """Token counts for one call, then what that call cost and the session total."""
    # These come back as None rather than 0 when a category is unused.
    prompt = usage.prompt_token_count or 0
    visible = usage.candidates_token_count or 0
    thoughts = usage.thoughts_token_count or 0
    total = usage.total_token_count or 0
    rows = [
        ("input tokens", prompt),
        ("output tokens", visible),
        ("thought tokens", thoughts),
        ("total tokens", total),
    ]
    print()
    for label, value in rows:
        print(f"{label:<16}{value:>12}")

    # The output-tokens-0 case: thinking consumed max_output_tokens, so the
    # visible candidate is empty. The printer shows 0. The bill does not.
    if visible == 0 and thoughts > 0:
        print(
            f"output tokens is 0 because no visible text was emitted. "
            f"{thoughts} thought tokens are still billed as output."
        )

    cost = call_cost_usd(usage)
    session = add_to_session(cost)
    print(f"{'this call':<16}{_usd(cost):>12}")
    print(f"{'session total':<16}{_usd(session):>12}")


def _usd(amount: float) -> str:
    return f"${amount:.8f}"


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

    print(f"\n{response_text(response)}")
    print_usage(response.usage_metadata)


if __name__ == "__main__":
    main()
