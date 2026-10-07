"""Temperature rescaling of a next-token distribution.

The model emits one distribution. Temperature does not change those scores.
It divides the logits by T before softmax. Given the probabilities at T=1,
that is the same as raising each probability to 1/T and renormalising,
because a logit is log(p) plus a constant that cancels in the softmax.
"""


def apply_temperature(probs: dict[str, float], temperature: float) -> dict[str, float]:
    """Return the distribution after applying `temperature` to a T=1 distribution.

    Temperature 0 is greedy decoding: the highest-probability token gets 1
    and every other token gets 0. Ties keep the first max key in dict order.
    """
    if not probs:
        return {}
    if temperature < 0:
        raise ValueError("temperature must be >= 0")
    if temperature == 0:
        winner = max(probs, key=probs.get)
        return {token: 1.0 if token == winner else 0.0 for token in probs}

    powered = {token: probability ** (1.0 / temperature) for token, probability in probs.items()}
    total = sum(powered.values())
    if total == 0:
        return {token: 0.0 for token in probs}
    return {token: value / total for token, value in powered.items()}
