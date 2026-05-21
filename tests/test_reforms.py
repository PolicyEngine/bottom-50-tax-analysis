"""Tests for the policy-reform definition."""

from __future__ import annotations

from bottom_50_tax_analysis import reforms


def test_zero_below_threshold_is_a_callable_factory():
    factory = reforms.zero_income_tax_below
    reform = factory(threshold=54_000, year=2026)
    assert isinstance(reform, dict)


def test_reform_dict_includes_threshold():
    reform = reforms.zero_income_tax_below(threshold=54_000, year=2026)
    # The reform stores the threshold under a known key so the simulation
    # wrapper can pick it up. Implementation may use a custom variable.
    assert reform["bottom_50_cutoff"] == 54_000
    assert reform["year"] == 2026


def test_describe_returns_human_readable_summary():
    summary = reforms.describe(threshold=54_000, year=2026)
    assert "54,000" in summary or "54000" in summary
    assert "2026" in summary
