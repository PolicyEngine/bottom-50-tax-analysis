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
  projects the cutoff forward to 2026 with PolicyEngine's calibrated Enhanced
  CPS.
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

`--live` runs the PolicyEngine-US Enhanced CPS microsimulation. Without it,
the CLI uses bundled Tax Foundation / IRS SOI 2023 fallback numbers so the
frontend can build in CI without microdata access.

### Run the frontend

```bash
cd frontend
bun install
bun run dev
```

## Methodology

For each tax unit in the PolicyEngine-US Enhanced CPS dataset (uprated to
2026):

1. Filter to `tax_unit_is_filer == True` so the population matches IRS
   SOI's tabulation, which is based on filed returns only. Non-filers
   otherwise pull the median AGI down and depress the bottom-50 share.
   Pass `--include-non-filers` to `bottom50-generate` to use the full
   Enhanced CPS population.
2. Compute `adjusted_gross_income`, `income_tax`, and
   `employee_payroll_tax + self_employment_payroll_tax`.
3. Sort by AGI, compute weighted percentile ranks.
4. Aggregate weighted tax totals into quintiles and top X% buckets.
5. Report the static revenue cost of zeroing out federal income tax for
   tax units below the 50th-percentile AGI cutoff, with no behavioural
   response.

Per the PolicyEngine microsimulation skill, all aggregates use
`MicroSeries.sum()` / `.mean()` on the weighted series — no manual weight
arithmetic.

## Caveats

- **Dataset choice matters a lot.** PE-US ships several datasets, and they
  produce different `income_tax_positive` totals (the variable PE
  calibrates against CBO's projected federal individual-income-tax
  receipts):

  | Year | CBO target | `enhanced_cps_2024` | `cps_2024` |
  | ---: | ---: | ---: | ---: |
  | 2024 | $2,426B | $4,503B (1.86×) | $1,905B (0.79×) |
  | 2025 | $2,656B | $4,719B (1.78×) | $1,992B (0.75×) |
  | 2026 | $2,751B | $5,101B (1.85×) | $2,134B (0.78×) |

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

  The default for this repo therefore remains `cps_2024` — permanently,
  as far as the frozen artifacts go — because (a) its total is ~$2.13T,
  which matches the IRS SOI 2023 figure of $2.14T essentially exactly,
  and (b) shares at the bottom of the distribution come out close to
  SOI. The CPS top-codes very high incomes (max AGI in the file is
  ~$3.3M), so the top-1% share is undershot — that's a known CPS
  limitation. Pass `--dataset enhanced_cps_2024` to use the frozen PE
  artifact anyway (not recommended). Migrating this repo to the
  microcosm-certified dataset via the `policyengine.py` interface is the
  eventual fix for the top-tail undershoot.
- **Tax-definition alignment.** The repo uses
  `income_tax_before_refundable_credits` for the SOI comparison: regular
  tax + AMT + NIIT + cap-gains tax, after non-refundable credits, before
  refundable. This is the line that maps to Tax Foundation's "Total
  Income Tax".
- **Population.** Default filters to `tax_unit_is_filer == True` (~81%
  of Enhanced CPS / ~89% of plain CPS tax units) so the comparison
  population matches IRS SOI, which tabulates filed returns only.
- Behavioural responses are not modelled. The "zero out tax below the
  50th percentile" revenue cost is a static estimate.
- Payroll-tax incidence is debated. The repo reports the employee-side
  share (statutory incidence); economic incidence (incl. employer side)
  would roughly double payroll's contribution to the bottom 50%'s burden.

## License

AGPL-3.0-or-later. Data inputs are governed by the licences of the underlying
sources (IRS SOI, Census CPS, PolicyEngine Enhanced CPS).
