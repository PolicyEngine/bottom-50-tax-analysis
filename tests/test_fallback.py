"""Tests for the Tax Foundation / IRS SOI fallback data.

The fallback module supplies a frozen snapshot of headline numbers used when
the live microsimulation cannot run. These tests assert the shape and basic
plausibility of that snapshot.
"""

from __future__ import annotations

import math

from bottom_50_tax_analysis import fallback


def test_snapshot_year_recent():
    snap = fallback.tax_foundation_snapshot()
    assert snap["tax_year"] >= 2022


def test_bottom_50_share_near_3_percent():
    snap = fallback.tax_foundation_snapshot()
    assert 0.02 <= snap["income_tax"]["bottom_50_share"] <= 0.05


def test_shares_sum_to_one():
    snap = fallback.tax_foundation_snapshot()
    a = snap["income_tax"]["bottom_50_share"]
    b = snap["income_tax"]["top_50_share"]
    assert math.isclose(a + b, 1.0, abs_tol=1e-6)


def test_top_shares_monotone():
    snap = fallback.tax_foundation_snapshot()
    ts = snap["income_tax"]
    assert (
        ts["top_1_share"]
        <= ts["top_5_share"]
        <= ts["top_10_share"]
        <= ts["top_25_share"]
        <= ts["top_50_share"]
    )


def test_bottom_50_cutoff_in_reasonable_range():
    snap = fallback.tax_foundation_snapshot()
    cutoff = snap["income_tax"]["bottom_50_cutoff"]
    assert 30_000 <= cutoff <= 100_000


def test_payroll_inclusion_changes_distribution():
    snap = fallback.tax_foundation_snapshot()
    income_only = snap["income_tax"]["bottom_50_share"]
    income_plus_payroll = snap["income_plus_payroll"]["bottom_50_share"]
    # Adding payroll tax raises the bottom 50%'s share substantially.
    assert income_plus_payroll > income_only
    assert income_plus_payroll - income_only > 0.05
