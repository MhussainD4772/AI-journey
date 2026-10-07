"""Per-call cost from the published Gemini Developer API paid-tier rates.

The free tier charges $0. Calls are still priced at the published paid rates
so a running session total is what this traffic would cost in production.
"""

from cli import config

# USD per 1,000,000 tokens. Output includes thinking tokens.
# https://ai.google.dev/gemini-api/docs/pricing  (gemini-3.5-flash-lite, paid)
_USD_PER_MILLION = {
    "gemini-3.5-flash-lite": {"input": 0.30, "output": 2.50},
}

_session_usd = 0.0


def _rates() -> tuple[float, float]:
    try:
        row = _USD_PER_MILLION[config.MODEL]
    except KeyError as exc:
        raise KeyError(
            f"No published rate recorded for {config.MODEL}. "
            "Add it to cli/cost.py before pricing a call."
        ) from exc
    return row["input"] / 1_000_000, row["output"] / 1_000_000


def call_cost_usd(usage) -> float:
    """Price one response's usage_metadata.

    `candidates_token_count` is the visible answer. It is 0 when the model
    spent the output budget on thinking and emitted no text. Those thought
    tokens are still output tokens on the pricing page, so they are billed.
    Missing counts arrive as None, not 0.
    """
    prompt = usage.prompt_token_count or 0
    visible = usage.candidates_token_count or 0
    thoughts = usage.thoughts_token_count or 0
    input_rate, output_rate = _rates()
    return prompt * input_rate + (visible + thoughts) * output_rate


def add_to_session(cost: float) -> float:
    global _session_usd
    _session_usd += cost
    return _session_usd


def session_total_usd() -> float:
    return _session_usd
