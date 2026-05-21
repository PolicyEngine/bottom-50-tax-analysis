"""Tax Foundation / IRS SOI fallback data.

Used when the live PolicyEngine-US microsimulation cannot run (e.g. in CI
without microdata access). All numbers are frozen snapshots of published
reports; update by editing this file and bumping ``snapshot_version``.

Sources:
    - Tax Foundation, "Summary of the Latest Federal Income Tax Data, 2025
      Update" (using IRS SOI 2023 individual income tax data, published
      March 2025).
    - IRS Statistics of Income, Table 1 (individual income tax shares).
    - Tax Policy Center, Briefing Book: "Who pays federal payroll taxes?"
      (used to back out the income+payroll combined distribution).
"""

from __future__ import annotations

from typing import Any

snapshot_version = "2025-03-tax-foundation"


def tax_foundation_snapshot() -> dict[str, Any]:
    """Headline numbers from the most recent published tax-share tables."""
    return {
        "tax_year": 2023,
        "source": (
            "IRS SOI 2023 (via Tax Foundation, Mar 2025); payroll-tax "
            "distribution derived from TPC Briefing Book."
        ),
        "snapshot_version": snapshot_version,
        # Federal individual income tax only.
        "income_tax": {
            "bottom_50_share": 0.03,
            "top_50_share": 0.97,
            "top_25_share": 0.872,
            "top_10_share": 0.720,
            "top_5_share": 0.607,
            "top_1_share": 0.404,
            "bottom_50_cutoff": 50_339,
            "top_25_cutoff": 99_857,
            "top_10_cutoff": 169_800,
            "top_5_cutoff": 252_840,
            "top_1_cutoff": 663_164,
            "average_tax_rate_top_1": 0.262,
            "average_tax_rate_bottom_50": 0.034,
            "total_tax_billions": 2_140.0,
        },
        # Federal individual income tax + employee-side payroll (FICA) tax.
        # Combining payroll tax — which is roughly flat up to the Social
        # Security wage base — substantially raises the bottom 50%'s share.
        "income_plus_payroll": {
            "bottom_50_share": 0.13,
            "top_50_share": 0.87,
            "top_25_share": 0.74,
            "top_10_share": 0.59,
            "top_5_share": 0.49,
            "top_1_share": 0.30,
            "bottom_50_cutoff": 50_339,
            "top_25_cutoff": 99_857,
            "top_10_cutoff": 169_800,
            "top_5_cutoff": 252_840,
            "top_1_cutoff": 663_164,
            "total_tax_billions": 3_700.0,
        },
        # Static estimate of revenue lost if federal income tax is zeroed
        # for everyone with AGI below the bottom-50 cutoff. Bottom 50% paid
        # ~3% of $2.14T = roughly $64B in 2023; we use a 2026 projection
        # below.
        "zero_below_bottom_50": {
            "tax_year": 2026,
            "threshold": 57_000,
            "revenue_cost_billions": 75.0,
            "units_affected_millions": 86.0,
            "average_tax_cut_dollars": 870.0,
            "note": (
                "Projected from 2023 SOI: ~$64B income tax paid by bottom "
                "50%, inflated by ~4% nominal wage growth/year through "
                "2026."
            ),
        },
    }
