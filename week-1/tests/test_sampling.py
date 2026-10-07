import pytest

from cli.sampling import apply_temperature


BASE = {"Paris": 0.70, "located": 0.20, "the": 0.10}


def test_temperature_one_is_unchanged():
    scaled = apply_temperature(BASE, 1.0)
    for token, probability in BASE.items():
        assert scaled[token] == pytest.approx(probability)


def test_temperature_zero_is_greedy():
    assert apply_temperature(BASE, 0) == {"Paris": 1.0, "located": 0.0, "the": 0.0}


def test_temperature_two_flattens_without_dropping_tokens():
    scaled = apply_temperature(BASE, 2.0)
    assert set(scaled) == set(BASE)
    assert scaled["Paris"] == pytest.approx(0.5229, abs=1e-3)
    assert scaled["located"] == pytest.approx(0.2795, abs=1e-3)
    assert scaled["the"] == pytest.approx(0.1976, abs=1e-3)
    assert sum(scaled.values()) == pytest.approx(1.0)


def test_a_near_certain_token_survives_temperature_two():
    scaled = apply_temperature({"42": 0.99, "other": 0.01}, 2.0)
    assert scaled["42"] > 0.90


def test_negative_temperature_is_rejected():
    with pytest.raises(ValueError):
        apply_temperature(BASE, -1)
