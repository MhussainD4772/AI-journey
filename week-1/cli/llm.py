import time

from google import genai
from google.genai import types
from google.genai.errors import ClientError

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
    top_p: float | None = None,
    top_k: int | None = None,
    logprobs: int | None = None,
    response_logprobs: bool | None = None,
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
        top_p=top_p,
        top_k=top_k,
        logprobs=logprobs,
        response_logprobs=response_logprobs,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        thinking_config=types.ThinkingConfig(
            thinking_level=thinking_level if thinking_level is not None else config.THINKING_LEVEL,
        ),
    )

    # Free tier is 15 requests/minute on this model. The SDK's own retry
    # gives up before the server's retryDelay elapses, so wait it out here.
    for attempt in range(6):
        try:
            return _client.models.generate_content(
                model=config.MODEL,
                contents=contents,
                config=gen_config,
            )
        except ClientError as exc:
            if exc.code != 429 or attempt == 5:
                raise
            time.sleep(_retry_seconds(exc))


def _retry_seconds(exc: ClientError) -> float:
    details = exc.details if isinstance(exc.details, dict) else {}
    error = details.get("error", details)
    for item in error.get("details", []) if isinstance(error, dict) else []:
        delay = item.get("retryDelay") if isinstance(item, dict) else None
        if isinstance(delay, str) and delay.endswith("s"):
            try:
                return min(float(delay[:-1]) + 0.5, 65)
            except ValueError:
                break
    return 8


def response_text(response) -> str:
    """Visible text. Empty when the candidate has no text part.

    That happens when thinking tokens consume the whole max_output_tokens
    budget: candidates_token_count comes back 0 and `.text` raises.
    """
    try:
        return response.text or ""
    except ValueError:
        return ""