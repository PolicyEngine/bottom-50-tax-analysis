"""Pure-numpy percentile share math.

The functions here are independent of PolicyEngine — they accept a population
of tax units (AGI, tax paid, survey weight) and compute weighted percentile
cutoffs, quintile shares, and revenue-cost estimates.

Why pure numpy? So the same code can be unit-tested against hand-computed
results (see ``tests/test_shares.py``) and reused in either the live
microsimulation path or the Tax Foundation fallback path.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypedDict

import numpy as np

ArrayLike = Sequence[float] | np.ndarray


class Distribution(TypedDict):
    bottom_50_share: float
    top_50_share: float
    top_25_share: float
    top_10_share: float
    top_5_share: float
    top_1_share: float
    bottom_50_cutoff: float
    top_25_cutoff: float
    top_10_cutoff: float
    top_5_cutoff: float
    top_1_cutoff: float
    quintile_shares: list[float]
    quintile_cutoffs: list[float]
    total_tax: float
    total_weight: float


def _validate(agi: np.ndarray, tax: np.ndarray, weight: np.ndarray) -> None:
    if not (len(agi) == len(tax) == len(weight)):
        raise ValueError(
            f"length mismatch: agi={len(agi)}, tax={len(tax)}, weight={len(weight)}"
        )
    if len(agi) == 0:
        raise ValueError("empty input")
    if (weight < 0).any():
        raise ValueError("weights must be non-negative")


def percentile_cutoff(agi: ArrayLike, weight: ArrayLike, percentile: float) -> float:
    """Weighted percentile of AGI."""
    agi_arr = np.asarray(agi, dtype=float)
    w = np.asarray(weight, dtype=float)
    order = np.argsort(agi_arr)
    agi_sorted = agi_arr[order]
    w_sorted = w[order]
    cum = np.cumsum(w_sorted)
    target = (percentile / 100.0) * cum[-1]
    idx = int(np.searchsorted(cum, target))
    idx = min(idx, len(agi_sorted) - 1)
    return float(agi_sorted[idx])


def compute_distribution(
    *,
    agi: ArrayLike,
    tax: ArrayLike,
    weight: ArrayLike,
) -> Distribution:
    """Weighted distribution of tax across the AGI percentiles.

    Parameters
    ----------
    agi : array-like
        AGI for each tax unit.
    tax : array-like
        Tax paid for each tax unit (federal income tax, or income + payroll).
    weight : array-like
        Survey weight for each tax unit.

    Returns
    -------
    Distribution
        Shares (fraction of total tax) and AGI cutoffs at each percentile.
    """
    agi_arr = np.asarray(agi, dtype=float)
    tax_arr = np.asarray(tax, dtype=float)
    w = np.asarray(weight, dtype=float)
    _validate(agi_arr, tax_arr, w)

    order = np.argsort(agi_arr)
    agi_sorted = agi_arr[order]
    tax_sorted = tax_arr[order]
    w_sorted = w[order]
    cum_w = np.cumsum(w_sorted)
    total_w = float(cum_w[-1])
    weighted_tax = tax_sorted * w_sorted
    cum_tax = np.cumsum(weighted_tax)
    total_tax = float(cum_tax[-1])

    def _cutoff(percentile: float) -> float:
        target = (percentile / 100.0) * total_w
        idx = int(np.searchsorted(cum_w, target))
        idx = min(idx, len(agi_sorted) - 1)
        return float(agi_sorted[idx])

    def _tax_at_or_below_percentile(percentile: float) -> float:
        # Interpolate cumulative tax against cumulative weight so the
        # percentile shares are well-defined even when a single tax unit
        # straddles the percentile boundary (the standard treatment used by
        # weighted-quantile libraries).
        target = (percentile / 100.0) * total_w
        return float(np.interp(target, cum_w, cum_tax))

    if total_tax == 0:
        # Degenerate case: tax-free world. Define shares as zero except the
        # bottom 50%, which by convention holds 0/0 = 0 here.
        zero_dist: Distribution = {
            "bottom_50_share": 0.0,
            "top_50_share": 0.0,
            "top_25_share": 0.0,
            "top_10_share": 0.0,
            "top_5_share": 0.0,
            "top_1_share": 0.0,
            "bottom_50_cutoff": _cutoff(50),
            "top_25_cutoff": _cutoff(75),
            "top_10_cutoff": _cutoff(90),
            "top_5_cutoff": _cutoff(95),
            "top_1_cutoff": _cutoff(99),
            "quintile_shares": [0.0] * 5,
            "quintile_cutoffs": [_cutoff(p) for p in (20, 40, 60, 80, 100)],
            "total_tax": 0.0,
            "total_weight": total_w,
        }
        return zero_dist

    bottom_50_tax = _tax_at_or_below_percentile(50)
    top_50_tax = total_tax - bottom_50_tax
    top_25_tax = total_tax - _tax_at_or_below_percentile(75)
    top_10_tax = total_tax - _tax_at_or_below_percentile(90)
    top_5_tax = total_tax - _tax_at_or_below_percentile(95)
    top_1_tax = total_tax - _tax_at_or_below_percentile(99)

    quintile_shares = []
    prev = 0.0
    for p in (20, 40, 60, 80, 100):
        here = _tax_at_or_below_percentile(p)
        quintile_shares.append((here - prev) / total_tax)
        prev = here

    return {
        "bottom_50_share": bottom_50_tax / total_tax,
        "top_50_share": top_50_tax / total_tax,
        "top_25_share": top_25_tax / total_tax,
        "top_10_share": top_10_tax / total_tax,
        "top_5_share": top_5_tax / total_tax,
        "top_1_share": top_1_tax / total_tax,
        "bottom_50_cutoff": _cutoff(50),
        "top_25_cutoff": _cutoff(75),
        "top_10_cutoff": _cutoff(90),
        "top_5_cutoff": _cutoff(95),
        "top_1_cutoff": _cutoff(99),
        "quintile_shares": quintile_shares,
        "quintile_cutoffs": [_cutoff(p) for p in (20, 40, 60, 80, 100)],
        "total_tax": total_tax,
        "total_weight": total_w,
    }


def revenue_cost_of_zeroing_below(
    *,
    agi: ArrayLike,
    tax: ArrayLike,
    weight: ArrayLike,
    threshold: float,
) -> float:
    """Static revenue cost of zeroing tax for units with AGI < threshold.

    Behavioural responses are not modelled.
    """
    agi_arr = np.asarray(agi, dtype=float)
    tax_arr = np.asarray(tax, dtype=float)
    w = np.asarray(weight, dtype=float)
    _validate(agi_arr, tax_arr, w)
    mask = agi_arr < threshold
    return float((tax_arr[mask] * w[mask]).sum())


def affected_below(
    *,
    agi: ArrayLike,
    tax: ArrayLike,
    weight: ArrayLike,
    threshold: float,
) -> dict[str, float]:
    """Number of tax units and average tax cut for the zero-below reform."""
    agi_arr = np.asarray(agi, dtype=float)
    tax_arr = np.asarray(tax, dtype=float)
    w = np.asarray(weight, dtype=float)
    _validate(agi_arr, tax_arr, w)
    mask = agi_arr < threshold
    units_affected = float(w[mask].sum())
    total_cut = float((tax_arr[mask] * w[mask]).sum())
    avg_cut = total_cut / units_affected if units_affected > 0 else 0.0
    return {
        "units_affected": units_affected,
        "total_cut": total_cut,
        "average_tax_cut": avg_cut,
    }
