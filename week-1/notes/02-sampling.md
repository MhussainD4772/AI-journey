# Sampling

## Watch

- [Deep Dive into LLMs like ChatGPT, inference](https://www.youtube.com/watch?v=7xTGNNLPyMI&t=1561s) — from 26:01. One token is sampled, appended, and the model runs again.

## Which call this repo makes

The picker settings are fields on `GenerateContentConfig`, passed by `cli/llm.py`: `temperature`, `top_p`, `top_k`, `seed`. Top-candidate log probabilities are requested with `response_logprobs=True` and `logprobs=5`. This is `models.generate_content`, not the Interactions API.

## Where the model's answer comes from

The model does not write sentences. It does one thing repeatedly: **look at the text so far, and rate every possible next token.**

Given `"The capital of France is"`, it goes through its entire vocabulary (~200,000 tokens) and assigns each one a score:

```
" Paris"     8.2
" located"   4.1
" the"       3.9
" banana"   -2.7
...and 199,996 more
```

These raw scores are called **logits**. They can be negative, they can be any size, and an individual value means nothing on its own. Only the **gaps between them** matter.

## Turning scores into percentages

Raw scores aren't usable. You want "Paris: 92%, located: 3%." Converting a list of arbitrary scores into percentages that sum to 100% is a standard maths operation called **softmax**.

Scores in, percentages out, they add up to 1. That's the whole job.

One property matters: **softmax exaggerates.** It is not proportional. A score that is somewhat higher becomes a *lot* more likely. Widening the gap between two scores more than widens the probability gap. This property is what temperature exploits.

Result:

```
" Paris"     92%
" located"    3%
" the"        2%
...
```

## The model stops here

The model has produced a list of percentages. **It has not chosen anything.**

Something separate then picks one token from that list, appends it to the text, and runs the model again from scratch for the next token. That picker is not part of the neural network — it's ordinary code in the inference server, maybe twenty lines.

That picker is what **sampling** means.

**The key consequence: temperature and top-p are settings on the picker, not on the model.** The model produces identical scores at temperature 0 and temperature 2. You are not changing what the model thinks. You are changing how willing the picker is to pass over the model's favourite and take something further down the list.

---

## Temperature

A dial on the picker that reshapes the list *before* it picks.

**Mechanism:** divide every raw score by the temperature number, then convert to percentages as usual.

- Dividing by a **small** number (below 1) makes scores bigger and — because softmax exaggerates gaps — the leader pulls further ahead. The list gets more lopsided.
- Dividing by a **large** number (above 1) squashes scores together. The leader's advantage shrinks. The list flattens.

**Concretely**, with three tokens at 70% / 20% / 10%:

| Temperature | Result | Effect |
|---|---|---|
| 0 | 100% / 0% / 0% | Favourite always wins. Called **greedy decoding**. |
| 0.5 | ~87% / 9% / 4% | Favourite almost always wins |
| 1.0 | 70% / 20% / 10% | Unchanged — the model's own opinion |
| 2.0 | ~47% / 28% / 25% | Third place went from 1-in-10 to 1-in-4 |

### What people get wrong

High temperature does **not** make the model more creative. The model did not change. What changed is that the picker now regularly selects options the model rated as *worse*.

Sometimes "worse" is an unusual word choice, which reads as creative. Sometimes it's a wrong fact or a broken bracket. **Same mechanism — you cannot get one without the other.**

Temperature applies **per token, independently**. At temperature 1.5 over a 300-token answer, that's 300 separate chances to take a bad option. Errors compound, because one odd word forces the next sentence to accommodate it. This is why high temperature doesn't degrade gracefully — output is fine, fine, fine, then nonsense.

### Where to set it

| Use | Temperature |
|---|---|
| Extraction, classification, anything you'll parse | 0 |
| Code | 0 – 0.3 |
| Summarising, explaining, analysis | 0.3 – 0.7 |
| Brainstorming, fiction, wanting variety | 0.8 – 1.0 |
| Above 1.0 | Diagnostic only — to watch it break |

Default with no opinion: **0 for anything with a right answer, 0.7 for anything else.**

---

## Top-p (nucleus sampling)

Solves a different problem from temperature.

The list is ~200,000 tokens long. Below the handful of sensible options is an enormous tail of garbage — each at 0.00001%, but there are 199,000 of them. Collectively the tail is a few percent. So every single token carries a real chance of pulling something absurd out of the bin.

Temperature does not fix this. It rescales the whole list, tail included.

**Mechanism:** sort the list highest to lowest. Add up percentages going down. Stop when the running total reaches p. Discard everything below that line. Pick from what survives.

At p = 0.9 after `"The capital of France is"`:

```
" Paris"     92%   → running total 92%  ✓ stop
" located"    3%   → discarded
" the"        2%   → discarded
...everything else discarded
```

One token survives. The answer is Paris, guaranteed.

At the same p = 0.9 after `"He opened the door and saw"`:

```
" a"          8%
" the"        7%
" his"        6%
" nothing"    4%
...
```

Nothing dominates, so you go ~60 tokens deep before accumulating 90%. Sixty tokens survive.

**That is the entire point.** Same setting, but it kept 1 token in one case and 60 in the other. The cutoff adapts to how confident the model is at that specific position. When the model knows the answer, top-p enforces it. When the position is genuinely open, top-p allows variety.

### Top-k, for context

The older approach: keep the top k tokens, always. `k=40` means 40 survive regardless of the situation.

Wrong in both directions — 40 is absurdly permissive after "The capital of France is", and arbitrarily restrictive in an open-ended position. Fixed number, varying situation. Top-p replaced it for this reason. You'll see top-k in older code and open-weight tooling; it isn't needed.

### Using both dials

Top-p cuts first, temperature reshapes what survives. They interact unintuitively, so tuning both at once means you won't know which one caused what.

**Rule: tune temperature, leave top-p at its default** (usually 1.0). Return to top-p only for a specific problem with rare garbage tokens.

---

## Why temperature 0 still isn't reproducible

Temperature 0 means "always take the highest-scoring token." Same input, same model, no randomness in the picker. It should be identical every time.

It isn't. The reason is not in the model — it's in the hardware.

### 1. Computers are bad at adding up

Computers store decimals approximately. Consequently, adding numbers in a different order gives slightly different answers — `(a + b) + c` can differ from `a + (b + c)` in the far decimal places. Normal floating-point behaviour, not an AI thing.

Producing those scores involves billions of additions on a GPU, split across thousands of parallel units. The order they finish in varies run to run. The score for `" Paris"` might come out `8.2000001` once and `8.1999998` the next.

Usually irrelevant. But if two tokens are nearly tied — `8.2000001` vs `8.2000000` — a wobble in the 7th decimal flips which is highest. "Always take the highest" then takes the other one.

One different token early changes every token after it, because each choice depends on everything before it. A flip at word 5 can produce a completely different paragraph.

### 2. You're sharing the GPU

The dominant cause on a hosted API. Your request is bundled with other users' requests and processed together for efficiency. The size and composition of that bundle changes the shape of the maths being done, which changes the order things get added, which changes the last decimal places.

The same prompt is genuinely more reproducible at 3am than at peak hours.

### 3. The backend changes without telling you

Providers patch models, change how they're compressed for speed, and move to different hardware. A model name today is not bit-for-bit the same as last month. Where the provider offers dated version strings, **pin them** — you'll at least be told when it changes.

### Seeds

Some APIs accept a `seed` parameter. It fixes the randomness **in the picker**. Real, but it only removes the randomness you'd get *above* temperature 0. It does nothing about the three causes above.

A seed moves you from "different every time" to "usually the same." Not the same as reproducible.

---

## What `gemini-3.5-flash-lite` actually did

Measured 7 Oct 2026, in `experiments/02-sampling.ipynb`. The mechanism above is how sampling works. This model does not apply it.

**Logprobs are refused.** `response_logprobs=True, logprobs=5` returns `400 Logprobs is not enabled for this model`. There is no top-5 list to print. Google does not return logprobs for Gemini 3.x. The temperature formula in the notebook is checked against the notes' 70/20/10 example, because the API will not hand back a distribution to check it against.

**Temperature does not change the draw.** Prompt: "Reply with one random integer from 0 to 99999. Digits only." Seed 7 produced `48216` at temperature 0, at temperature 1 (twice), and at temperature 2 (twice). Seed 99 produced `48291`. The seed fixes the pick. Temperature does not resize the bins — if it did, the same seed at temperature 2 would land on a different token. Unseeded temperature 0 was also not greedy: four draws were four-ish different integers, not one repeated winner.

**`top_p` did not change the draw either.** Same seed, `top_p=1.0` and `top_p=0.5`, both `48216`. Cutoff and flattening are different operations on paper (the notebook shows that on 70/20/10). On this model both knobs are accepted and ignored. Google's Gemini 3.x guide says to remove `temperature`, `top_p`, and `top_k` from requests. `complete()` still sends them so this is visible: a 200 does not mean the setting was used. `config.TEMPERATURE` is 0.7, and that default is filled in whenever the caller passes `None`.

**The "42" case.** `6*7` came back `42` at temperature 0 and at temperature 2. The formula says a 99% token is still about 91% after temperature 2, so it would survive a real rescaling. Here it survives because temperature is not applied. The formula and the bug agree on the outcome and disagree on the cause. The seed experiment is the one that separates them.

---

## What this means for building

Build as if output is non-deterministic, always, at every setting.

- **Don't write tests asserting exact output strings.** They'll pass for a week, then fail.
- **Don't cache** on the assumption that the same input yields the same output.
- **Don't build a feature** whose correctness requires an identical string back.

If a design needs an exact repeatable answer, the fix isn't a parameter — it's **storing the output you got** rather than expecting to regenerate it.

---

## Summary

- The model outputs a score (logit) for every token in the vocabulary, converted to percentages by softmax.
- The model never chooses. A separate picker does, and sampling settings configure the picker.
- Temperature reshapes the list: low = lopsided toward the favourite, high = flattened. Temperature 0 = always take the top.
- High temperature isn't creativity; it's willingness to take options the model rated worse. Applied per token, so errors compound.
- Top-p discards the long tail of garbage, with a cutoff that adapts to the model's confidence at that position.
- Tune temperature, leave top-p alone.
- Nothing is reproducible, even at temperature 0, because of floating-point ordering, shared-GPU batching, and silent backend changes.
- On `gemini-3.5-flash-lite` specifically, `temperature` and `top_p` are accepted and ignored. A seed fixes the draw. Logprobs are refused with a 400. See the measured section above.