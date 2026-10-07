# Token counting and cost

## Watch

There isn't a separate lecture for this. The counts are the same tokens as [tokenization](01-tokenization.md), and the bill is what a chat loop does to them, which [context windows](03-context_window_and_stop_sequence.md) already describes.

## The output-tokens-0 case

`response.usage_metadata` splits the response:

| Field | What it counts |
|---|---|
| `prompt_token_count` | Everything you sent |
| `candidates_token_count` | Visible answer text |
| `thoughts_token_count` | Thinking, before the visible answer |
| `total_token_count` | The sum |

Any of those can come back as `None` rather than `0` when that category wasn't used. The printer treats `None` as 0.

`max_output_tokens` is a ceiling on thinking plus the visible answer, not on the visible answer alone. If thinking uses the whole ceiling, generation stops before a single visible token. Then:

- `candidates_token_count` is 0
- there is no text part, so `response.text` raises and `response_text()` returns `""`
- `finish_reason` is `MAX_TOKENS`
- `thoughts_token_count` is not 0

A line that only prints `candidates_token_count` says the call was free of output. It was not. The published output price includes thinking tokens. `cli/main.py` prints a line when it sees this shape, and `call_cost_usd` adds the thought tokens at the output rate.

On `gemini-3.5-flash-lite` with `thinking_level=MINIMAL`, ordinary short answers do emit visible text, so the 0 does not show up on a normal call. It shows up when the cap is small relative to thinking. `thinking_level=MINIMAL` does not guarantee thinking is off.

## Rates

Published paid-tier rates for `gemini-3.5-flash-lite`, per 1,000,000 tokens:

| | USD |
|---|---|
| Input | 0.30 |
| Output, including thinking | 2.50 |

Source: [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing).

The free tier charges nothing. `print_usage` still prices every call at these published rates, then adds it to a process-wide session total. Both `python -m cli` and `python -m cli.chat` print the two numbers after every call. The session total resets when the process exits.

## Which call this repo makes

Counts are read from `response.usage_metadata` on `generate_content`. Not from an Interactions API usage object, and not from `response.usage`.
