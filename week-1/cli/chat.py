from google.genai import types

from cli.llm import complete, response_text
from cli.main import print_usage


def turn(role: str, text: str) -> types.Content:
    """One turn, in the shape generate_content expects.

    Roles are "user" and "model". The system prompt is not a turn;
    it goes to complete(..., system=...) as system_instruction.
    """
    return types.Content(role=role, parts=[types.Part(text=text)])


def main():
    history: list[types.Content] = []

    print("Type a message. Ctrl-C to quit.")

    while True:
        try:
            text = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text.strip():
            continue

        history.append(turn("user", text))

        response = complete(history)
        answer = response_text(response)

        print(f"\n{answer}")
        print_usage(response.usage_metadata)

        history.append(turn("model", answer))


if __name__ == "__main__":
    main()
