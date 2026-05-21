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
  produce different totals when summed against IRS SOI's published
  tabulations:

  | Dataset | Total income tax (2026) | Bottom-50 share | Top-1 share |
  | --- | ---: | ---: | ---: |
  | `cps_2024` (default here) | $2.13T | 4.9% | 23.4% |
  | `enhanced_cps_2024` (PE standard) | $5.09T | 1.6% | 67.4% |
  | IRS SOI 2023 (Tax Foundation) | $2.14T | 3.0% | 40.4% |

  The plain `cps_2024` matches SOI's total revenue almost exactly because
  its underlying records are Form-1040-equivalent. It understates the
  top-1% share because CPS top-codes very high incomes (the highest AGI
  in the file is ~$3M).

  The `enhanced_cps_2024` adds synthetic high-net-worth tax units (the
  highest AGI in the file is ~$30B). This is intentional in PE's design
  for distributional analysis, but its total revenue is roughly 2.4× SOI,
  so the percentile shares aren't an apples-to-apples match for an SOI
  replication. PE's website distributional charts use the Enhanced CPS;
  the bottom-50% / top-1% tax-share comparisons here use plain CPS by
  choice. Pass `--dataset enhanced_cps_2024` to switch.
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
