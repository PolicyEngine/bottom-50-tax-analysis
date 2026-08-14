# Bottom-50 federal tax analysis

Microsimulation of the federal income tax burden by income percentile, using
[PolicyEngine-US](https://github.com/PolicyEngine/policyengine-us).

## Background

On CNBC (May 20, 2026), Jeff Bezos referenced the often-cited statistic that
"the bottom 50% of earners pay 3% of federal income tax." That figure comes
from the IRS Statistics of Income (SOI) tables, summarised annually by the
[Tax Foundation](https://taxfoundation.org/data/all/federal/latest-federal-income-tax-data-2025/).

The headline is accurate as far as it goes, but it is also incomplete:

- It covers **only the individual income tax**, not payroll (FICA) taxes,
  which fall most heavily on low- and middle-income workers.
- The "bottom 50%" is a moving target — the AGI cutoff was about
  \$50,339 for tax year 2022 and roughly \$54,000 for 2023; this repo
  projects the cutoff forward to 2026 with PolicyEngine-US on the
  certified microcosm dataset.
- Zeroing-out federal income tax for the bottom 50% is sometimes floated as
  a policy idea. This repo estimates the revenue cost, the number of tax
  units affected, and the per-household tax cut.

## What this repo contains

| Path | Purpose |
| --- | --- |
| `src/bottom_50_tax_analysis/` | Python package: percentile-share math, reform definitions, simulation wrapper, CLI |
| `tests/` | pytest unit tests (TDD-first) |
| `data/results.json` | Generated outputs consumed by the frontend |
| `frontend/` | Next.js 14 + Tailwind 4 + `@policyengine/ui-kit` interactive app |
| `.github/workflows/` | CI for the Python package + frontend |

## Quick start

### Run the Python package

Requires Python 3.11–3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv pip install -e ".[dev]"
uv run pytest                       # run tests
uv run bottom50-generate            # emit data/results.json (fallback mode)
uv pip install ".[sim]"             # add policyengine-us
uv run bottom50-generate --live     # emit data/results.json (live microsim)
```

`--live` runs the PolicyEngine-US microsimulation on the certified
microcosm dataset (the first run downloads and SHA-verifies the release
artifact from the public `policyengine/populace-us` Hugging Face dataset
repo). Without it, the CLI uses bundled Tax Foundation / IRS SOI 2023
fallback numbers so the frontend can build in CI without microdata access.

### Run the frontend

```bash
cd frontend
bun install
bun run dev
```

## Methodology

For each tax unit in the certified microcosm US dataset (resolved,
SHA-verified, and engine-version-checked by `microcosm-data`; the release
id is recorded in `results.json`), simulated for 2026:

1. Filter to `tax_unit_is_filer == True` so the population matches IRS
   SOI's tabulation, which is based on filed returns only. Non-filers
   otherwise pull the median AGI down and depress the bottom-50 share.
   Pass `--include-non-filers` to `bottom50-generate` to use the full
   population.
2. Compute `adjusted_gross_income`, `income_tax`, and
   `employee_payroll_tax + self_employment_payroll_tax`.
3. Sort by AGI, compute weighted percentile ranks.
4. Aggregate weighted tax totals into quintiles and top X% buckets.
5. Report the static revenue cost of zeroing out federal income tax for
   tax units below the 50th-percentile AGI cutoff, with no behavioural
   response.

Percentile math lives in `shares.py` as pure numpy on `(agi, tax, weight)`
arrays — weighted cumulative sums with interpolation at percentile
boundaries — so it unit-tests against hand-computed populations
(`tests/test_shares.py`) independently of the simulation stack.

## Caveats

- **Dataset choice matters a lot.** Gross federal income tax on filed
  returns (`income_tax_before_refundable_credits`, the SOI-comparable
  line), measured from this repo's own pipeline under the pinned
  `policyengine-us` 1.764.6:

  | Year | `microcosm_us_2024` (default) | `cps_2024` (frozen) | Reference points |
  | ---: | ---: | ---: | :--- |
  | 2024 | $2,363B | $1,905B | IRS SOI liability target: $2,359B · CBO receipts: $2,426B |
  | 2025 | $2,514B | $2,099B | CBO receipts: $2,656B |
  | 2026 | $2,716B | $2,246B | CBO receipts: $2,751B |

  (The third frozen artifact, `enhanced_cps_2024`, measured $4,503B /
  $4,719B / $5,101B across 2024–26 when this repo was built in May 2026
  — the ~1.86× CBO overshoot described below — and is left out of the
  table.)

  The `enhanced_cps_2024` is built by combining the plain Census CPS
  with cloned records from the IRS Public Use File (PUF) and reweighting
  to IRS SOI and CBO targets via L0-sparse optimisation
  (`policyengine_us_data/datasets/cps/enhanced_cps.py`). The intent is to
  hit the CBO target — but the final published build overshoots it by
  ~1.86× across every year tested. That was a **calibration regression
  introduced in the May 19–20 2026 (1.115.x) builds**, tracked in
  [policyengine-us-data#1107](https://github.com/PolicyEngine/policyengine-us-data/issues/1107):
  the recalibration let a handful of synthetic top-tail records carry
  extreme weight (one record with AGI ≈ $1.8B contributed ~$409B of
  national AGI on its own), which also inflated top-concentrated
  deductions ~9×.

  That regression was never fixed in `policyengine-us-data` — the repo
  was **archived in July 2026** with the broken `enhanced_cps_2024.h5`
  frozen as the final artifact. The successor certified US dataset lives
  in [PolicyEngine/microcosm](https://github.com/PolicyEngine/microcosm)
  (formerly populace), which restored pinned US fiscal calibration
  targets (SOI income tax / AGI, plus a macro-realism gate) in
  [microcosm#44](https://github.com/PolicyEngine/microcosm/pull/44)
  (merged June 2026).

  **This repo now defaults to the certified microcosm release**
  (`microcosm_us_2024`). `microcosm.data.load` resolves `latest.json` on
  the `policyengine/populace-us` Hugging Face repo, reads the release
  manifest at its immutable tag, SHA-256-verifies the artifact, and
  refuses engine versions outside the release's certification — so
  `results.json` records exactly which release produced it (and reruns
  may resolve a newer release than the checked-in results; bump the
  engine pins in `pyproject.toml` when the certification moves).

  The release's hard calibration anchor is the IRS SOI **liability**
  total — CBO receipts were de-anchored to a macro-only reference in
  [microcosm#79](https://github.com/PolicyEngine/microcosm/pull/79).
  The checked-in release's diagnostics land **+0.12%** from the 2024
  target, and this repo's own 2024 run reproduces it ($2,363B vs the
  $2,359B target). That target is TY2022-vintage valued at 2024
  ([microcosm#116](https://github.com/PolicyEngine/microcosm/issues/116)
  tracks aging it), so read projected-year totals against CBO receipts
  only loosely.

  Distributionally, the release calibrates national totals (its
  national SOI surface has AGI-bracket splits only for taxable
  interest), so the share of tax by AGI percentile is an emergent
  outcome, not a target. At 2026 it lands close to SOI 2023 through
  most of the distribution — bottom-50 share 2.4% vs 3.0%, top-25
  within ~1pp, top-10 within ~1.4pp, top-5 within ~3.5pp — while the
  top-1% share (28.4%) still reads well below SOI's 40.4%. Keep that
  gap in mind for statements about the very top (the years and law also
  differ, 2026 vs 2023). The top tail is at least populated now: max
  AGI in the certified release is ~$14.9M at 2026, versus the ~$3.3M
  top-code that made `cps_2024`'s top-1% share (22.5%) unusable for
  top-end statements.

  The frozen `policyengine-us-data` artifacts stay available as explicit
  comparison escape hatches: `--dataset cps_2024` (top-coded tail) and
  `--dataset enhanced_cps_2024` (the broken final build — not
  recommended).
- **Tax-definition alignment.** The repo uses
  `income_tax_before_refundable_credits` for the SOI comparison: regular
  tax + AMT + NIIT + cap-gains tax, after non-refundable credits, before
  refundable. This is the line that maps to Tax Foundation's "Total
  Income Tax".
- **Population.** Default filters to `tax_unit_is_filer == True` (~97%
  of microcosm tax units; ~81% of Enhanced CPS / ~89% of plain CPS) so
  the comparison population matches IRS SOI, which tabulates filed
  returns only.
- Behavioural responses are not modelled. The "zero out tax below the
  50th percentile" revenue cost is a static estimate.
- Payroll-tax incidence is debated. The repo reports the employee-side
  share (statutory incidence); economic incidence (incl. employer side)
  would roughly double payroll's contribution to the bottom 50%'s burden.

## License

AGPL-3.0-or-later. Data inputs are governed by the licences of the underlying
sources (IRS SOI, Census CPS, and the microcosm-published population
dataset).
