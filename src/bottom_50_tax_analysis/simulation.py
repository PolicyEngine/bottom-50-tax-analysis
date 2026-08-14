"""PolicyEngine-US microsimulation wrapper.

This module is imported lazily — the simulation stack is heavy and is an
**optional** dependency (``pip install bottom-50-tax-analysis[sim]``).
Calling :func:`extract_tax_unit_data` raises a helpful ImportError if the
packages are missing.

The wrapper extracts AGI, federal income tax, and (employee-side) payroll
tax for every tax unit, with the household weight mapped to the tax_unit
level so the percentile-share math in :mod:`shares` can use the weights
directly. For the "zero income tax below the 50th-percentile cutoff" reform
we use a static estimate (see :func:`shares.revenue_cost_of_zeroing_below`):
because the reform just forces ``income_tax = 0`` for the affected tax
units, the revenue cost is identical to the weighted sum of their
baseline ``income_tax``. Behavioural and state-tax interactions are not
modelled.
"""

from __future__ import annotations

import numpy as np


def _require_sim_stack() -> None:
    try:
        import policyengine_us  # noqa: F401
    except ImportError as exc:  # pragma: no cover — exercised only without [sim]
        raise ImportError(
            "policyengine-us is not installed. Install with:\n"
            "    uv pip install '.[sim]'\n"
            "or use the fallback path (``bottom50-generate`` without "
            "``--live``)."
        ) from exc


#: The certified microcosm release (default). ``microcosm.data.load`` resolves
#: ``latest.json`` on the ``policyengine/populace-us`` Hugging Face dataset
#: repo, reads the release manifest at the immutable release tag, verifies the
#: artifact's SHA-256, and refuses engine versions outside the release's
#: certification — so which release you got is recorded, not guessed.
MICROCOSM_DATASET = "microcosm_us_2024"

#: Frozen policyengine-us-data artifacts (that repo was archived in July
#: 2026; these files no longer change). Kept as escape hatches for
#: comparison runs only — see the README dataset caveat.
LEGACY_DATASETS = {
    "cps_2024": "hf://policyengine/policyengine-us-data/cps_2024.h5",
    "enhanced_cps_2024": "hf://policyengine/policyengine-us-data/enhanced_cps_2024.h5",
    "pooled_3_year_cps_2023": "hf://policyengine/policyengine-us-data/pooled_3_year_cps_2023.h5",
}

DATASETS = (MICROCOSM_DATASET, *LEGACY_DATASETS)

DEFAULT_DATASET = MICROCOSM_DATASET


def _certified_release_id() -> str:
    """The release id ``latest.json`` currently points at, for provenance.

    ``microcosm.data.load`` re-resolves the pointer itself immediately after
    this call; the id is informational (it names the release in
    ``results.json``), while the loader's own resolution is what gets
    SHA-verified and compatibility-checked.
    """
    from microcosm.data import resolve
    from microcosm.data.release import latest_release

    return latest_release(resolve("us", 2024).hf_repo).release_id


def _build_microsimulation(dataset: str):
    """Return ``(Microsimulation, release_id-or-None)`` for ``dataset``."""
    from policyengine_us import Microsimulation  # type: ignore[import-not-found]

    if dataset == MICROCOSM_DATASET:
        from microcosm.data import load

        release_id = _certified_release_id()
        return Microsimulation(dataset=load("us", 2024)), release_id
    if dataset in LEGACY_DATASETS:
        return Microsimulation(dataset=LEGACY_DATASETS[dataset]), None
    raise ValueError(f"Unknown dataset {dataset!r}. Choices: {sorted(DATASETS)}.")


def extract_tax_unit_data(
    year: int = 2026,
    *,
    filers_only: bool = True,
    dataset: str = DEFAULT_DATASET,
) -> dict[str, np.ndarray]:
    """Run the baseline US microsimulation and return per-tax-unit arrays.

    Parameters
    ----------
    year : int
        Calendar year for the simulation.
    filers_only : bool, default True
        If True, drop tax units where ``tax_unit_is_filer`` is False so the
        population matches IRS SOI (which only tabulates filed returns).
    dataset : str, default "microcosm_us_2024"
        Which dataset to use. The default loads the current certified
        microcosm release (CPS ASEC structure with IRS PUF tax detail,
        calibrated to IRS SOI income-tax targets), so both the totals and
        the top of the distribution are usable. ``cps_2024`` and
        ``enhanced_cps_2024`` load the frozen policyengine-us-data
        artifacts for comparison: plain CPS matches SOI totals but
        top-codes high incomes; the final enhanced build overshoots its
        revenue target ~1.86× (see the README dataset caveat).

    Returns
    -------
    dict
        AGI, federal income tax, employee payroll tax, weight, and
        population-scope metadata as numpy arrays, plus the certified
        release id under ``dataset_release`` (None for legacy datasets).
    """
    _require_sim_stack()
    sim, release_id = _build_microsimulation(dataset)
    agi = np.asarray(sim.calc("adjusted_gross_income", period=year), dtype=float)
    # ``income_tax`` is net of refundable credits — PE's standard measure,
    # what you'd use for a budget score. Can be negative for refund recipients.
    income_tax_net = np.asarray(sim.calc("income_tax", period=year), dtype=float)
    # ``income_tax_before_refundable_credits`` is the apples-to-apples match
    # for the IRS SOI "Total Income Tax" line that Tax Foundation
    # distributes by AGI percentile: regular tax + AMT + NIIT + other
    # surtaxes, after non-refundable credits, before refundable credits.
    income_tax_gross = np.asarray(
        sim.calc("income_tax_before_refundable_credits", period=year),
        dtype=float,
    )
    payroll_tax = np.asarray(sim.calc("employee_payroll_tax", period=year), dtype=float)
    weight = np.asarray(sim.calc("tax_unit_weight", period=year), dtype=float)
    is_filer = np.asarray(sim.calc("tax_unit_is_filer", period=year), dtype=bool)

    if filers_only:
        mask = is_filer
    else:
        mask = np.ones_like(is_filer, dtype=bool)

    return {
        "agi": agi[mask],
        "income_tax_gross": income_tax_gross[mask],
        "income_tax_net": income_tax_net[mask],
        "payroll_tax": payroll_tax[mask],
        "weight": weight[mask],
        "population_scope": "filers" if filers_only else "all_tax_units",
        "filer_share": float(weight[is_filer].sum() / weight.sum()),
        "dataset": dataset,
        "dataset_release": release_id,
    }
