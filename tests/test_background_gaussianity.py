"""Testes das estatísticas de gaussianidade, sintéticos e sem cubo real."""

import numpy as np

from hypermix import excess_kurtosis, skewness


def test_excess_kurtosis_is_near_zero_for_gaussian_data():
    rng = np.random.default_rng(0)
    x = rng.standard_normal((200000, 3))

    kurt = excess_kurtosis(x)

    assert kurt.shape == (3,)
    assert np.abs(kurt).max() < 0.1


def test_excess_kurtosis_is_positive_for_heavy_tails():
    rng = np.random.default_rng(1)
    # mistura: mesmo com marginais normais, a mistura de escalas gera cauda pesada
    core = rng.standard_normal((100000, 1))
    tail = rng.standard_normal((5000, 1)) * 8.0
    x = np.concatenate([core, tail], axis=0)

    assert excess_kurtosis(x)[0] > 5.0


def test_skewness_detects_asymmetry_and_vanishes_for_symmetric_data():
    rng = np.random.default_rng(2)
    symmetric = rng.standard_normal((200000, 1))
    positive = rng.exponential(size=(200000, 1))

    assert abs(skewness(symmetric)[0]) < 0.05
    assert skewness(positive)[0] > 1.5


def test_statistics_are_computed_per_band_independently():
    rng = np.random.default_rng(3)
    quiet = rng.standard_normal((50000, 1))
    heavy = rng.standard_normal((50000, 1)) * rng.choice([1.0, 10.0], (50000, 1))
    x = np.concatenate([quiet, heavy], axis=1)

    kurt = excess_kurtosis(x)

    # Mistura de escalas 1 e 10 com peso igual tem excesso teorico de cerca de 2,9.
    assert abs(kurt[0]) < 0.2
    assert kurt[1] > 2.0
