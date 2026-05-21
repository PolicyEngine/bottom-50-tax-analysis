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
