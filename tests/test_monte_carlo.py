
import numpy as np
import pandas as pd
import pytest

from src.monte_carlo_simulation import (
    calculate_risk_metrics,
    make_positive_semidefinite,
)

INITIAL_PORTFOLIO = 10_000.0


# ============================================================
# 1. COVARIANCE MATRIX TESTS
# ============================================================

def test_covariance_matrix_is_symmetric():
    covariance = np.array([
        [0.04, 0.01],
        [0.02, 0.09],
    ])

    result = make_positive_semidefinite(covariance)

    assert np.allclose(result, result.T, atol=1e-10)


def test_covariance_matrix_is_positive_semidefinite():
    covariance = np.array([
        [0.04, 0.01],
        [0.01, 0.09],
    ])

    result = make_positive_semidefinite(covariance)
    eigenvalues = np.linalg.eigvalsh(result)

    assert eigenvalues.min() >= -1e-10


def test_covariance_matrix_has_correct_shape():
    covariance = np.array([
        [0.04, 0.01],
        [0.01, 0.09],
    ])

    result = make_positive_semidefinite(covariance)

    assert result.shape == covariance.shape


def test_covariance_matrix_with_negative_eigenvalue_is_corrected():
    # This symmetric matrix has one negative eigenvalue.
    covariance = np.array([
        [1.0, 2.0],
        [2.0, 1.0],
    ])

    result = make_positive_semidefinite(covariance)

    assert np.allclose(result, result.T, atol=1e-10)
    assert np.linalg.eigvalsh(result).min() >= -1e-10


# ============================================================
# 2. VALUE AT RISK AND EXPECTED SHORTFALL TESTS
# ============================================================

def test_risk_metrics_have_95_and_99_percent_levels():
    terminal_values = np.array([
        7_000, 8_000, 8_500, 9_000, 9_500,
        10_000, 10_500, 11_000, 12_000, 13_000,
    ], dtype=float)

    result = calculate_risk_metrics(
        terminal_values,
        INITIAL_PORTFOLIO,
    )

    assert result["Confidence_Level"].tolist() == [0.95, 0.99]
    assert len(result) == 2


def test_expected_shortfall_is_at_least_var():
    rng = np.random.default_rng(42)

    terminal_values = rng.lognormal(
        mean=np.log(INITIAL_PORTFOLIO),
        sigma=0.25,
        size=10_000,
    )

    result = calculate_risk_metrics(
        terminal_values,
        INITIAL_PORTFOLIO,
    )

    for _, row in result.iterrows():
        assert (
            row["Expected_Shortfall_Loss_Amount"]
            >= row["VaR_Loss_Amount"] - 1e-8
        )


def test_risk_metrics_are_finite():
    terminal_values = np.array([
        8_000, 9_000, 9_500, 10_000, 10_500,
        11_000, 12_000, 13_000, 14_000, 15_000,
    ], dtype=float)

    result = calculate_risk_metrics(
        terminal_values,
        INITIAL_PORTFOLIO,
    )

    numeric_values = result.select_dtypes(
        include="number"
    ).to_numpy()

    assert np.isfinite(numeric_values).all()


def test_var_and_expected_shortfall_are_consistent():
    terminal_values = np.linspace(
        5_000,
        15_000,
        10_001,
    )

    result = calculate_risk_metrics(
        terminal_values,
        INITIAL_PORTFOLIO,
    )

    for _, row in result.iterrows():
        assert (
            row["Expected_Shortfall_Loss_Amount"]
            >= row["VaR_Loss_Amount"] - 1e-8
        )

        assert np.isclose(
            row["VaR_Loss_Amount"],
            -row["VaR_Return_Threshold"] * INITIAL_PORTFOLIO,
        )


# ============================================================
# 3. INVALID INPUT TESTS
# These require validation in calculate_risk_metrics().
# ============================================================

@pytest.mark.parametrize(
    "terminal_values",
    [
        np.array([8_000, 9_000, np.nan, 11_000]),
        np.array([8_000, 9_000, np.inf, 11_000]),
        np.array([8_000, 9_000, -np.inf, 11_000]),
    ],
)
def test_non_finite_terminal_values_are_rejected(terminal_values):
    with pytest.raises(ValueError):
        calculate_risk_metrics(
            terminal_values,
            INITIAL_PORTFOLIO,
        )


def test_negative_terminal_values_are_rejected():
    terminal_values = np.array([
        8_000, 9_000, -100, 11_000,
    ], dtype=float)

    with pytest.raises(ValueError):
        calculate_risk_metrics(
            terminal_values,
            INITIAL_PORTFOLIO,
        )


@pytest.mark.parametrize(
    "terminal_values",
    [
        np.array([], dtype=float),
        np.array([[8_000, 9_000], [10_000, 11_000]]),
    ],
)
def test_empty_or_non_1d_terminal_values_are_rejected(terminal_values):
    with pytest.raises(ValueError):
        calculate_risk_metrics(
            terminal_values,
            INITIAL_PORTFOLIO,
        )


@pytest.mark.parametrize(
    "initial_value",
    [
        0,
        -1,
        np.nan,
        np.inf,
        -np.inf,
    ],
)
def test_invalid_initial_portfolio_value_is_rejected(initial_value):
    terminal_values = np.array([
        8_000, 9_000, 10_000, 11_000,
    ], dtype=float)

    with pytest.raises(ValueError):
        calculate_risk_metrics(
            terminal_values,
            initial_value,
        )


# ============================================================
# 4. REPRODUCIBILITY TESTS
# ============================================================

def test_same_seed_produces_same_random_samples():
    rng1 = np.random.default_rng(42)
    rng2 = np.random.default_rng(42)

    samples1 = rng1.standard_normal((100, 5))
    samples2 = rng2.standard_normal((100, 5))

    assert np.array_equal(samples1, samples2)


def test_different_seeds_produce_different_random_samples():
    rng1 = np.random.default_rng(42)
    rng2 = np.random.default_rng(123)

    samples1 = rng1.standard_normal((100, 5))
    samples2 = rng2.standard_normal((100, 5))

    assert not np.array_equal(samples1, samples2)
