from google import genai
from google.genai import types

from cli import config

_client = genai.Client(api_key=config.API_KEY)


def complete(
    contents,
    system: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    stop: list[str] | None = None,
    thinking_level: str | None = None,
    seed: int | None = None,
):
    """
    Send a prompt (or a conversation) to the model and return the response object.

    `contents` is a string for one-shot, or a list of turns for a conversation.
    Returns the raw response, NOT a string — token counts live on it.
    """

    # Every sampling parameter now sits on one config object.
    # None means "not set", and the SDK omits it from the request.
    gen_config = types.GenerateContentConfig(
        temperature=temperature if temperature is not None else config.TEMPERATURE,
        max_output_tokens=max_tokens if max_tokens is not None else config.MAX_TOKENS,
        stop_sequences=stop,
        system_instruction=system,
        seed=seed,
        thinking_config=types.ThinkingConfig(
            thinking_level=thinking_level if thinking_level is not None else config.THINKING_LEVEL,
        ),
    )

    return _client.models.generate_content(
        model=config.MODEL,
        contents=contents,
        config=gen_config,
    )