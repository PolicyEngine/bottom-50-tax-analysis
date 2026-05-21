"""Tests for percentile-share aggregation.

These tests describe the contract of ``shares.compute_distribution``:
given (AGI, tax, weight) for every tax unit, return:

- the weighted AGI cutoff for any percentile,
- the share of total tax paid by the bottom-N% / top-N% buckets,
- the share of total tax paid by income quintile.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from bottom_50_tax_analysis import shares


class TestPercentileCutoff:
    def test_median_of_uniform_population_is_in_middle(self, uniform_population):
        cutoff = shares.percentile_cutoff(
            uniform_population["agi"],
            uniform_population["weight"],
            percentile=50,
        )
        # AGIs are 1000..100000 in steps of 1000; weighted median is 50_500.
        assert 49_000 <= cutoff <= 52_000

    def test_p99_is_near_top(self, uniform_population):
        cutoff = shares.percentile_cutoff(
            uniform_population["agi"],
            uniform_population["weight"],
            percentile=99,
        )
        assert cutoff >= 98_000

    def test_zero_weight_units_are_ignored(self):
        agi = np.array([10.0, 20, 30, 40, 50])
        weight = np.array([1.0, 0, 0, 0, 1])
        cutoff = shares.percentile_cutoff(agi, weight, percentile=50)
        # Only units 1 and 5 (AGI 10 and 50) count; median is between them.
        assert 10 <= cutoff <= 50


class TestBottomTopShares:
    def test_uniform_pop_bottom_50_share_under_flat_tax(self, uniform_population):
        # Flat tax: share of tax = share of AGI. Bottom 50% of a uniform 1..100
        # distribution holds (1+2+...+50)/(1+2+...+100) = 1275/5050 ≈ 25.25%.
        dist = shares.compute_distribution(
            agi=uniform_population["agi"],
            tax=uniform_population["income_tax"],
            weight=uniform_population["weight"],
        )
        assert math.isclose(dist["bottom_50_share"], 0.2525, abs_tol=0.01)
        assert math.isclose(
            dist["top_50_share"] + dist["bottom_50_share"], 1.0, abs_tol=1e-6
        )

    def test_progressive_pop_top_10_share_high(self, progressive_population):
        # With 10 equally-weighted units, "top 10%" is the single richest
        # unit, which holds 935 of 1000 in tax: 93.5%.
        dist = shares.compute_distribution(
            agi=progressive_population["agi"],
            tax=progressive_population["income_tax"],
            weight=progressive_population["weight"],
        )
        assert dist["top_10_share"] >= 0.90

    def test_progressive_pop_top_1_share_interpolates(self, progressive_population):
        # The top 1% straddles the richest unit (which spans 10% of the
        # population); interpolating gives 1/10 of its tax share = 9.35%.
        dist = shares.compute_distribution(
            agi=progressive_population["agi"],
            tax=progressive_population["income_tax"],
            weight=progressive_population["weight"],
        )
        assert 0.08 <= dist["top_1_share"] <= 0.11

    def test_returns_expected_buckets(self, uniform_population):
        dist = shares.compute_distribution(
            agi=uniform_population["agi"],
            tax=uniform_population["income_tax"],
            weight=uniform_population["weight"],
        )
        for key in (
            "bottom_50_share",
            "top_50_share",
            "top_25_share",
            "top_10_share",
            "top_5_share",
            "top_1_share",
            "bottom_50_cutoff",
            "top_25_cutoff",
            "top_10_cutoff",
            "top_5_cutoff",
            "top_1_cutoff",
            "total_tax",
        ):
            assert key in dist, f"missing key: {key}"

    def test_top_shares_are_monotone(self, uniform_population):
        dist = shares.compute_distribution(
            agi=uniform_population["agi"],
            tax=uniform_population["income_tax"],
            weight=uniform_population["weight"],
        )
        # The top 1% must pay less in total tax than the top 5%, and so on.
        assert (
            dist["top_1_share"]
            <= dist["top_5_share"]
            <= dist["top_10_share"]
            <= dist["top_25_share"]
            <= dist["top_50_share"]
        )

    def test_quintile_shares_sum_to_one(self, uniform_population):
        dist = shares.compute_distribution(
            agi=uniform_population["agi"],
            tax=uniform_population["income_tax"],
            weight=uniform_population["weight"],
        )
        total = sum(dist["quintile_shares"])
        assert math.isclose(total, 1.0, abs_tol=1e-6)
        assert len(dist["quintile_shares"]) == 5


class TestZeroTaxBelowThreshold:
    def test_cost_equals_tax_paid_by_units_below_threshold(self, uniform_population):
        cost = shares.revenue_cost_of_zeroing_below(
            agi=uniform_population["agi"],
            tax=uniform_population["income_tax"],
            weight=uniform_population["weight"],
            threshold=50_500,  # The 50th-percentile cutoff in this fixture.
        )
        # AGIs 1k..50k pay 10% tax = 100 + 200 + ... + 5000 = 127_500.
        expected = sum(i * 100 for i in range(1, 51))  # = 127_500
        assert math.isclose(cost, expected, rel_tol=1e-6)

    def test_units_affected_counts_only_below_threshold(self, uniform_population):
        result = shares.affected_below(
            agi=uniform_population["agi"],
            tax=uniform_population["income_tax"],
            weight=uniform_population["weight"],
            threshold=50_500,
        )
        assert result["units_affected"] == 50
        # 50 units paying $100..$5000 in tax — average $2,550.
        assert math.isclose(result["average_tax_cut"], 2_550.0, rel_tol=1e-6)

    def test_zero_threshold_yields_zero_cost(self, uniform_population):
        cost = shares.revenue_cost_of_zeroing_below(
            agi=uniform_population["agi"],
            tax=uniform_population["income_tax"],
            weight=uniform_population["weight"],
            threshold=0,
        )
        assert cost == 0.0


class TestInputValidation:
    def test_mismatched_lengths_raise(self):
        with pytest.raises(ValueError):
            shares.compute_distribution(
                agi=np.array([1.0, 2, 3]),
                tax=np.array([1.0, 2]),
                weight=np.array([1.0, 1, 1]),
            )

    def test_negative_weights_raise(self):
        with pytest.raises(ValueError):
            shares.compute_distribution(
                agi=np.array([1.0, 2, 3]),
                tax=np.array([1.0, 2, 3]),
                weight=np.array([1.0, -1, 1]),
            )

    def test_empty_input_raises(self):
        with pytest.raises(ValueError):
            shares.compute_distribution(
                agi=np.array([]),
                tax=np.array([]),
                weight=np.array([]),
            )
