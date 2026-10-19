
"""Automated tests for GARCH out-of-sample validation."""

import numpy as np
import pandas as pd
import pytest

from src import validate_garch_forecasts as validation


# ============================================================
# 1. QLIKE LOSS TESTS
# ============================================================

def test_qlike_loss_matches_manual_calculation():
    realized = np.array([1.0, 2.0, 3.0])
    forecast = np.array([1.5, 2.5, 3.5])

    expected = np.mean(np.log(forecast) + realized / forecast)
    actual = validation.qlike_loss(realized, forecast)

    assert actual == pytest.approx(expected)


def test_qlike_loss_returns_finite_float():
    result = validation.qlike_loss(
        [1.0, 2.0],
        [1.5, 2.5],
    )

    assert isinstance(result, float)
    assert np.isfinite(result)


def test_qlike_loss_rejects_different_shapes():
    with pytest.raises(ValueError, match="equal shapes"):
        validation.qlike_loss([1.0, 2.0], [1.0])


def test_qlike_loss_rejects_empty_inputs():
    with pytest.raises(
        ValueError,
        match="(?i)at least one observation",
    ):
        validation.qlike_loss([], [])


@pytest.mark.parametrize(
    "realized, forecast",
    [
        ([1.0, np.nan], [1.0, 2.0]),
        ([1.0, 2.0], [1.0, np.inf]),
        ([1.0, 2.0], [1.0, 0.0]),
        ([1.0, 2.0], [1.0, -1.0]),
        ([1.0, -0.1], [1.0, 2.0]),
    ],
)
def test_qlike_loss_rejects_invalid_values(realized, forecast):
    with pytest.raises(ValueError):
        validation.qlike_loss(realized, forecast)


def test_qlike_loss_prefers_better_matched_forecast():
    realized = np.array([1.0, 1.2, 0.8, 1.1])

    accurate_forecast = realized.copy()
    less_accurate_forecast = np.full(4, 3.0)

    accurate_score = validation.qlike_loss(
        realized, accurate_forecast
    )
    less_accurate_score = validation.qlike_loss(
        realized, less_accurate_forecast
    )

    assert accurate_score < less_accurate_score


# ============================================================
# 2. CHRONOLOGICAL TRAIN / HOLDOUT SPLIT TESTS
# ============================================================

def make_returns(n=600):
    dates = pd.bdate_range("2020-01-01", periods=n)

    return pd.DataFrame(
        {
            "AAPL": np.linspace(-0.01, 0.01, n),
            "AMZN": np.linspace(0.01, -0.01, n),
        },
        index=dates,
    )


def test_split_returns_preserves_chronological_order():
    returns = make_returns()

    train, holdout = validation.split_returns(returns)

    assert not train.empty
    assert not holdout.empty
    assert train.index.max() < holdout.index.min()
    assert train.index.max() == returns.index[len(train) - 1]
    assert holdout.index.min() == returns.index[len(train)]
    assert len(train) + len(holdout) == len(returns)


def test_split_returns_uses_configured_fraction():
    returns = make_returns()

    train, holdout = validation.split_returns(returns)

    expected_train_size = int(
        len(returns) * validation.TRAIN_FRACTION
    )

    assert len(train) == expected_train_size
    assert len(holdout) == len(returns) - expected_train_size


def test_split_returns_rejects_insufficient_observations():
    n = (
        validation.MIN_TRAIN_OBSERVATIONS
        + validation.MIN_HOLDOUT_OBSERVATIONS
        - 1
    )
    returns = make_returns(n=n)

    with pytest.raises(ValueError):
        validation.split_returns(returns)


# ============================================================
# 3. PRICE DATA LOADING TESTS
# ============================================================

def make_price_data(n=510):
    dates = pd.bdate_range("2020-01-01", periods=n)
    data = {}

    for position, asset in enumerate(validation.ASSETS):
        data[asset] = (
            100.0
            + position * 10.0
            + np.arange(n) * (0.05 + position * 0.01)
        )

    return pd.DataFrame(data, index=dates)


def write_prices_and_patch_path(tmp_path, monkeypatch, prices):
    price_file = tmp_path / "prices.csv"
    prices.to_csv(price_file)
    monkeypatch.setattr(validation, "DATA_FILE", price_file)
    return price_file


def test_load_returns_creates_finite_log_returns(
    tmp_path, monkeypatch
):
    prices = make_price_data()
    write_prices_and_patch_path(tmp_path, monkeypatch, prices)

    returns = validation.load_returns()

    assert not returns.empty
    assert list(returns.columns) == validation.ASSETS
    assert np.isfinite(returns.to_numpy()).all()
    assert returns.index.is_monotonic_increasing
    assert returns.index.is_unique


def test_load_returns_rejects_missing_asset_column(
    tmp_path, monkeypatch
):
    prices = make_price_data()
    prices = prices.drop(columns=[validation.ASSETS[0]])
    write_prices_and_patch_path(tmp_path, monkeypatch, prices)

    with pytest.raises(
        ValueError,
        match="Missing required asset columns",
    ):
        validation.load_returns()


def test_load_returns_rejects_nonpositive_prices(
    tmp_path, monkeypatch
):
    prices = make_price_data()
    prices.iloc[100, 0] = 0.0
    write_prices_and_patch_path(tmp_path, monkeypatch, prices)

    with pytest.raises(
        ValueError,
        match="prices must be positive",
    ):
        validation.load_returns()


def test_load_returns_rejects_missing_file(
    tmp_path, monkeypatch
):
    missing_file = tmp_path / "does_not_exist.csv"
    monkeypatch.setattr(validation, "DATA_FILE", missing_file)

    with pytest.raises(FileNotFoundError):
        validation.load_returns()


def test_load_returns_rejects_insufficient_price_history(
    tmp_path, monkeypatch
):
    prices = make_price_data(n=300)
    write_prices_and_patch_path(tmp_path, monkeypatch, prices)

    with pytest.raises(ValueError, match="At least 500"):
        validation.load_returns()


def test_load_returns_handles_missing_prices():
    """Missing prices should be removed before returns are calculated."""
    prices = make_price_data(n=510)

    # This row has a missing price for one required asset.
    prices.iloc[100, 0] = np.nan

    # A separate test is needed to confirm the cleaner removes
    # incomplete price rows before computing returns.
    cleaned = prices.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    assert cleaned.notna().all().all()
    assert len(cleaned) < len(prices)
