"""End-to-end tests for the CLI that emits ``data/results.json``."""

from __future__ import annotations

import json
import subprocess
import sys


def test_cli_emits_valid_json_in_fallback_mode(tmp_path):
    out = tmp_path / "results.json"
    cmd = [
        sys.executable,
        "-m",
        "bottom_50_tax_analysis.cli",
        "--output",
        str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(out.read_text())
    assert payload["mode"] == "fallback"
    assert "income_tax" in payload
    assert "income_plus_payroll" in payload
    assert payload["income_tax"]["bottom_50_share"] > 0


def test_cli_payload_has_metadata(tmp_path):
    out = tmp_path / "results.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "bottom_50_tax_analysis.cli",
            "--output",
            str(out),
        ],
        check=True,
    )
    payload = json.loads(out.read_text())
    assert "generated_at" in payload
    assert "version" in payload
    assert payload["version"]  # nonempty


def test_build_payload_live_carries_tax_foundation_snapshot(monkeypatch):
    # The live payload must include the IRS SOI 2023 snapshot so the frontend
    # can render the PE-vs-SOI comparison panel without re-fetching it.
    import numpy as np

    from bottom_50_tax_analysis import cli, simulation

    def fake_extract(year, *, filers_only=True, dataset="cps_2024"):
        # 5 tax units, ascending AGI. The bottom two receive net refunds
        # (refundable EITC/CTC > positive liability) so net bottom-50 share
        # comes out negative; gross income tax (before refundable credits)
        # stays non-negative for everyone.
        return {
            "agi": np.array([10_000.0, 30_000, 60_000, 120_000, 500_000]),
            "income_tax_gross": np.array([100.0, 400, 4_000, 14_000, 120_000]),
            "income_tax_net": np.array([-2_000.0, -100, 1_000, 10_000, 100_000]),
            "payroll_tax": np.array([750.0, 2_300, 4_600, 9_200, 18_000]),
            "weight": np.array([1.0, 1, 1, 1, 1]),
            "population_scope": "filers" if filers_only else "all_tax_units",
            "filer_share": 0.82,
            "dataset": dataset,
        }

    monkeypatch.setattr(simulation, "extract_tax_unit_data", fake_extract)
    payload = cli.build_payload(live=True, year=2026)
    assert payload["mode"] == "live"
    assert "tax_foundation_2023" in payload
    assert "income_tax" in payload["tax_foundation_2023"]
    assert payload["tax_foundation_2023"]["tax_year"] == 2023
    assert payload["tax_foundation_2023"]["income_tax"]["bottom_50_share"] == 0.03
    # Gross PE income tax must be non-negative for the bottom 50% even when
    # net (refundable-credit-inclusive) values are negative.
    assert payload["income_tax"]["bottom_50_share"] >= 0
    assert payload["income_tax_net"]["bottom_50_share"] < 0
    # Filer scope is on by default and surfaced in the payload.
    assert payload["population_scope"] == "filers"
    assert "filer_share_of_all_tax_units" in payload


def test_build_payload_respects_include_non_filers(monkeypatch):
    import numpy as np

    from bottom_50_tax_analysis import cli, simulation

    seen = {}

    def fake_extract(year, *, filers_only=True, dataset="cps_2024"):
        seen["filers_only"] = filers_only
        seen["dataset"] = dataset
        return {
            "agi": np.array([1.0, 2, 3, 4, 5]),
            "income_tax_gross": np.array([0.0, 1, 2, 3, 4]),
            "income_tax_net": np.array([0.0, 1, 2, 3, 4]),
            "payroll_tax": np.array([0.1, 0.2, 0.3, 0.4, 0.5]),
            "weight": np.array([1.0, 1, 1, 1, 1]),
            "population_scope": "filers" if filers_only else "all_tax_units",
            "filer_share": 0.82,
            "dataset": dataset,
        }

    monkeypatch.setattr(simulation, "extract_tax_unit_data", fake_extract)
    payload = cli.build_payload(live=True, year=2026, filers_only=False)
    assert seen["filers_only"] is False
    assert payload["population_scope"] == "all_tax_units"
