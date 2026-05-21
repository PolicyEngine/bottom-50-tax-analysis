"""CLI: emit ``data/results.json`` for the Next.js frontend.

Usage::

    bottom50-generate --output data/results.json
    bottom50-generate --live --output data/results.json

The ``--live`` flag runs the PolicyEngine-US microsimulation. Without it the
CLI emits the Tax Foundation fallback snapshot so the frontend can build in
CI without microdata access.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__, fallback, reforms, shares


def _build_fallback_payload(threshold: float, year: int) -> dict[str, Any]:
    snap = fallback.tax_foundation_snapshot()
    return {
        "mode": "fallback",
        "version": __version__,
        "snapshot_version": fallback.snapshot_version,
        "generated_at": datetime.now(UTC).isoformat(),
        "year": year,
        "source": snap["source"],
        "income_tax": snap["income_tax"],
        "income_plus_payroll": snap["income_plus_payroll"],
        "zero_below_bottom_50": snap["zero_below_bottom_50"],
        "reform_description": reforms.describe(
            threshold=snap["zero_below_bottom_50"]["threshold"],
            year=year,
        ),
    }


def _build_live_payload(year: int) -> dict[str, Any]:
    from . import simulation  # lazy import

    import numpy as np

    data = simulation.extract_tax_unit_data(year=year)
    # PolicyEngine's ``income_tax`` is net of refundable credits and can be
    # negative for tax units that receive refunds. The Tax Foundation
    # headline ("bottom 50% pays 3%") uses positive tax liability only.
    # Report both so the frontend can show the gap.
    net_income_tax = data["income_tax"]
    gross_income_tax = np.clip(data["income_tax"], 0, None)

    net_income_dist = shares.compute_distribution(
        agi=data["agi"],
        tax=net_income_tax,
        weight=data["weight"],
    )
    gross_income_dist = shares.compute_distribution(
        agi=data["agi"],
        tax=gross_income_tax,
        weight=data["weight"],
    )
    combined_dist = shares.compute_distribution(
        agi=data["agi"],
        tax=gross_income_tax + data["payroll_tax"],
        weight=data["weight"],
    )
    threshold = gross_income_dist["bottom_50_cutoff"]
    affected = shares.affected_below(
        agi=data["agi"],
        tax=gross_income_tax,
        weight=data["weight"],
        threshold=threshold,
    )
    return {
        "mode": "live",
        "version": __version__,
        "snapshot_version": "live-policyengine-us",
        "generated_at": datetime.now(UTC).isoformat(),
        "year": year,
        "source": "PolicyEngine-US Enhanced CPS, calibrated 2026",
        "income_tax": gross_income_dist,
        "income_tax_net": net_income_dist,
        "income_plus_payroll": combined_dist,
        "zero_below_bottom_50": {
            "tax_year": year,
            "threshold": threshold,
            "revenue_cost_billions": affected["total_cut"] / 1e9,
            "units_affected_millions": affected["units_affected"] / 1e6,
            "average_tax_cut_dollars": affected["average_tax_cut"],
        },
        "reform_description": reforms.describe(threshold=threshold, year=year),
    }


def build_payload(*, live: bool, year: int) -> dict[str, Any]:
    """Build the JSON payload — exposed for testing."""
    if live:
        return _build_live_payload(year=year)
    return _build_fallback_payload(threshold=57_000, year=year)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit data/results.json for the frontend."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/results.json"),
        help="Where to write the JSON.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Run the live PolicyEngine-US microsimulation. Requires "
            "'pip install .[sim]'."
        ),
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2026,
        help="Calendar year to simulate.",
    )
    args = parser.parse_args(argv)

    payload = build_payload(live=args.live, year=args.year)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {args.output} ({payload['mode']} mode)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
