from cli.llm import complete
from cli.main import print_usage


def user_step(text):
    """One turn of yours, in the shape the API expects."""
    return {"type": "user_input", "content": [{"type": "text", "text": text}]}


def main():
    history = []

    print("Type a message. Ctrl-C to quit.")

    while True:
        try:
            text = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text.strip():
            continue

        history.append(user_step(text))

        response = complete(history)

        print(f"\n{response.output_text}")
        print_usage(response.usage)

        # The model's own steps go back into history exactly as received.
        # model_dump() turns each step object back into a plain dict.
        for step in response.steps:
            history.append(step.model_dump())


if __name__ == "__main__":
    main()