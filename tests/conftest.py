"""Shared fixtures for the bottom-50 tax analysis tests."""

from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture
def uniform_population():
    """100 tax units of equal weight with AGIs spaced 1k..100k and a 10% flat tax.

    Useful because the percentile shares can be computed by hand:
    bottom 50% holds AGIs 1..50, top 50% holds 51..100, etc.
    """
    agi = np.arange(1_000, 101_000, 1_000, dtype=float)
    income_tax = agi * 0.10
    payroll_tax = agi * 0.0765
    weight = np.ones_like(agi)
    return {
        "agi": agi,
        "income_tax": income_tax,
        "payroll_tax": payroll_tax,
        "weight": weight,
    }


@pytest.fixture
def progressive_population():
    """A small population with a sharply progressive distribution.

    10 tax units. The top unit holds 90% of AGI.
    """
    agi = np.array([1.0, 1, 1, 1, 1, 1, 1, 1, 1, 91.0]) * 1_000
    income_tax = np.array([0.0, 0, 0, 0, 0, 5, 10, 20, 30, 935.0])
    payroll_tax = agi * 0.0765
    weight = np.ones_like(agi)
    return {
        "agi": agi,
        "income_tax": income_tax,
        "payroll_tax": payroll_tax,
        "weight": weight,
    }
