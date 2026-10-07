# Tokenization

## Watch

- [Let's build the GPT Tokenizer](https://www.youtube.com/watch?v=zduSFxRajkE) — Karpathy, the merge rules in full.
- [Deep Dive into LLMs like ChatGPT, tokenization](https://www.youtube.com/watch?v=7xTGNNLPyMI&t=467s) — from 7:47.
- [Same video, spelling and counting](https://www.youtube.com/watch?v=7xTGNNLPyMI&t=7271s) — from 2:01:11.

## Which call this repo makes

`cli/llm.py` calls `models.generate_content`. It does not call the Interactions API (`client.interactions`, server-side history, `output_text`, `.steps`). Token counts come back on `response.usage_metadata`: `prompt_token_count`, `candidates_token_count`, `thoughts_token_count`. The system prompt is a `system_instruction` argument, not a role in the contents list. Contents roles are `"user"` and `"model"`.

## What the tokenizer is

A separate, non-neural piece of software that sits in front of the model. It converts a string into a list of integers, and converts the model's output integers back into a string.

The model never sees text. It consumes integers and emits integers.

The tokenizer is frozen: it is trained once, before the model, and never changes afterwards. The model's weights are learned against that specific vocabulary, so the two cannot be swapped independently.

```
"the cat sat"  ->  tokenizer  ->  [1820, 8415, 7731]  ->  model
model  ->  [1820, 8415, 7731]  ->  tokenizer  ->  "the cat sat"
```

## How the vocabulary is built — byte-pair encoding (BPE)

1. Start with a large text corpus and a vocabulary containing the 256 possible byte values.
2. Count every adjacent pair of symbols in the corpus.
3. Take the most frequent pair, add it to the vocabulary as a single new symbol, and replace every occurrence of that pair with it.
4. Repeat from step 2, roughly 100,000–200,000 times.

The result is an **ordered list of merge rules**. Encoding text at runtime is just replaying those rules greedily, in the order they were learned. This makes encoding deterministic — the same string always produces the same token IDs.

Starting from raw **bytes** rather than characters has two consequences:

- Nothing is ever out-of-vocabulary. Any UTF-8 input encodes, because worst case it falls back to individual bytes.
- Anything rare in the merge corpus never earned a merge, so it is represented as many small pieces.

## What drives token count

Frequency in the merge corpus. Not length, not meaning, not complexity.

| Input | Behaviour |
|---|---|
| Common English words | Usually one token each |
| Rare words, proper nouns, typos | Split into several tokens |
| Non-Latin scripts (Arabic, Hindi, Thai) | Commonly 2–4x the tokens of equivalent English |
| Code | Mid-range — indentation and keywords have dedicated tokens, identifiers get chopped |
| Emoji | Often several tokens each |

Rough rule for English prose: **~4 characters per token, ~0.75 tokens per word.** This rule does not transfer to code, other languages, or structured data.

Practical implication: the same meaning costs different amounts depending on the language it is written in. A multilingual product has uneven per-user cost for reasons that have nothing to do with the users.

## Leading whitespace

Whitespace attaches to the **front** of the following token. `" the"` and `"the"` are different tokens with different IDs.

A prompt that ends with a trailing space forces the model to continue from a token boundary it rarely saw during training, and output quality degrades.

**Rule: never end a prompt with a trailing space or a partial word.**

## Why models fail at letter-level tasks

`strawberry` may be a small number of tokens. Once it is, the individual letters are gone — the model receives integers, not characters. There is no `r` available to count.

Same root cause for:

- Reversing strings
- Some arithmetic (digits are grouped into chunks that do not align with place value)
- Exact character positions within a long span

This is a **mechanical limitation of the input representation, not a reasoning failure.** It is the main signal for deciding what to send to a model versus what to do in plain code: character-level work belongs in Python.

### Why `strawberry` specifically no longer demonstrates it

The strawberry example is stale as of 2026. Three things changed:

1. It became the most famous LLM failure on the internet, so the answer is now widely present in training data and post-training. The model recalls rather than counts.
2. Reasoning models spell the word out in their chain of thought first (`s-t-r-a-w-b-e-r-r-y`), which converts the problem into one over separate tokens, where counting works.
3. Chat products frequently route this class of question to a code tool, which just runs `"strawberry".count("r")`.

A current demonstration needs a string that cannot be memorised, with a non-reasoning model and no tools:

```
How many 'r' in qzlmxrrvtbrqxwrz? Answer immediately.
```

Two failures are tangled together in that test:

- **Tokenization** — no characters available to inspect.
- **Counting** — maintaining a running tally over a long sequence is independently weak, and shows up even with items the model can see clearly.

To separate them, give the letters pre-spaced: `q z l m x r r v t b r q x w r z`. Tokenization is largely neutralised there, so any remaining error is the tally weakness.

## Special tokens

The vocabulary contains IDs that do not correspond to text: end-of-turn, start-of-message, role boundaries. Chat APIs insert these automatically around the messages you send.

Consequences:

- A chat request always costs slightly more tokens than the visible text.
- On `generate_content`, the system instruction and the user/model turns are **structurally distinct**, not just concatenated strings. That structure is what a system prompt's extra weight actually rests on. The Interactions API is a different endpoint and is not what this repo calls.

## Tokenizers are family-specific

OpenAI, Anthropic, and open-weight models use different vocabularies. Token counts are not portable between them.

- OpenAI: `tiktoken`, with the encoding matching the specific model.
- Anthropic: the count-tokens API endpoint.

Counting with one family's tokenizer and billing against another's produces errors in the 10–20% range.

## Summary

- Text never reaches the model; integers do.
- The vocabulary is built by repeatedly merging the most frequent adjacent pair, starting from bytes.
- Token count tracks corpus frequency, not length or meaning.
- Whitespace binds to the following token; never end a prompt with a space.
- Letter-level tasks fail because the letters are not in the input.
- Token counts are model-family-specific.