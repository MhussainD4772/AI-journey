from types import SimpleNamespace

from cli.cost import call_cost_usd


def usage(prompt=0, visible=0, thoughts=0):
    return SimpleNamespace(
        prompt_token_count=prompt,
        candidates_token_count=visible,
        thoughts_token_count=thoughts,
    )


def test_published_rates_for_a_million_tokens():
    assert call_cost_usd(usage(prompt=1_000_000)) == 0.30
    assert call_cost_usd(usage(visible=1_000_000)) == 2.50


def test_thoughts_are_billed_when_visible_output_is_zero():
    # The output-tokens-0 case: nothing was printed, thinking still costs.
    cost = call_cost_usd(usage(prompt=100, visible=0, thoughts=400))
    assert cost == (100 * 0.30 + 400 * 2.50) / 1_000_000


def test_none_counts_are_treated_as_zero():
    empty = SimpleNamespace(
        prompt_token_count=None,
        candidates_token_count=None,
        thoughts_token_count=None,
    )
    assert call_cost_usd(empty) == 0.0
