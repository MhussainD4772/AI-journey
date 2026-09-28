# Context Windows and Stop Sequences

Two separate things, both about limits.

---

## Context window: the model has no memory

Every API call sends the **entire conversation**. Your system prompt, every previous user message, every previous model reply, and the new message. All of it, every time.

The model is **stateless**. It does not remember your last call. "Conversation" is an illusion maintained by your code resending the whole transcript on each turn.

The **context window** is the maximum number of tokens that transcript can be. Current models run from ~128k up to ~1M depending on the model. **Input and output share it** — if the window is 200k and your input is 199k, you have 1k left to generate into.

### Three consequences

**1. Cost grows quadratically in a chat loop.**

Turn 1 you send 100 tokens. Turn 10 you send everything from turns 1–9 plus the new message. A long conversation gets expensive not because the last message is big, but because you keep resending the first one.

```
turn 1:  send 100 tokens
turn 2:  send 250 tokens   (turn 1 + reply + new message)
turn 3:  send 500 tokens
turn 10: send ~5000 tokens
```

**2. Overflow is a hard error, not a graceful trim.**

Exceed the window and you get a 400 back. Your loop has to decide what to drop — oldest messages, or a summary of them. That is your problem to solve, not the API's.

**3. Long context degrades before it breaks.**

Models are measurably worse at using information buried in the **middle** of a very long input than at the start or end. A 1M-token window does not mean 1M tokens of reliable attention.

Putting the important content at the very start or very end of a long prompt is a real technique, not superstition.

---

## Stop sequences: telling it when to shut up

The model generates token by token with no plan. It stops for one of three reasons:

**1. It emits a special end-of-turn token** — its own decision that it is finished.

**2. It hits `max_tokens`**, your hard cap.

This is a **guillotine, not an instruction.** Output gets cut mid-word. It is a cost safety limit, not a length control. To control length you ask in the prompt; `max_tokens` exists so you are not billed for a runaway.

**3. It generates one of your stop sequences.**

A stop sequence is a string you supply. The moment the model produces it, generation halts immediately, and **the stop sequence itself is not included** in what you get back.

### Why stop sequences matter

Models over-generate. You ask for one example and get the example plus "Would you like another?" Or you set up a pattern like:

```
Q: What is the capital of France?
A:
```

The model writes the answer, then cheerfully invents the next `Q:` and answers that too.

Setting `"\nQ:"` as a stop sequence cuts it off the instant it starts.

---

## Always check why it stopped

The response includes a field — `finish_reason` or `stop_reason` depending on the provider — with values like:

| Value | Meaning |
|---|---|
| `stop` / `end_turn` | Natural end, the model finished |
| `length` / `max_tokens` | Hit your cap, **output is truncated** |
| stop-sequence indication | One of your stop strings fired |

**Check this field.** A response truncated by `max_tokens` looks like a complete response in your string variable — it just has a sentence that trails off. If you are parsing it, you will get confusing failures unless you check why it ended.

Never trust the text without checking the stop reason.

---

## Summary

- The model is stateless; you resend the entire conversation every call.
- Input and output share one token budget — the context window.
- Chat loops cost more per turn because history accumulates.
- Overflow is a 400 error; trimming history is your job.
- Information in the middle of a long prompt is used less reliably than at the edges.
- `max_tokens` truncates mid-word — it is a cost cap, not a length instruction.
- Stop sequences halt generation immediately and are excluded from the output.
- Always check the stop reason before using the text.