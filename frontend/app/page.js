"use client";

import { useState } from "react";
import data from "../data/results.json";
import { ComparisonTable } from "./components/ComparisonTable";
import { ShareChart } from "./components/ShareChart";
import { ThresholdSlider } from "./components/ThresholdSlider";
import { Toggle } from "./components/Toggle";

function buildTaxOptions(data) {
  const opts = [
    { label: "Income tax (gross)", value: "income_tax" },
    { label: "Income + payroll", value: "income_plus_payroll" },
  ];
  if (data.income_tax_net) {
    opts.splice(1, 0, {
      label: "Income tax (net of refundable credits)",
      value: "income_tax_net",
    });
  }
  return opts;
}

const VIEW_BLURB = {
  income_tax:
    "Gross federal individual income tax — positive tax liability only, the headline measure used by the Tax Foundation and IRS SOI.",
  income_tax_net:
    "Net federal income tax, including refundable credits (EITC, refundable CTC). When refunds are counted, the bottom 50% is close to tax-neutral or a net beneficiary.",
  income_plus_payroll:
    "Gross income tax plus employee-side payroll (FICA) tax. Payroll tax is roughly flat up to the wage base, so adding it sharply raises the bottom 50%'s share.",
};

export default function Home() {
  const taxOptions = buildTaxOptions(data);
  const [taxView, setTaxView] = useState("income_tax");
  const distribution = data[taxView];
  const blurb = VIEW_BLURB[taxView];

  return (
    <main className="min-h-screen" style={{ backgroundColor: "var(--background)" }}>
      <div className="max-w-5xl mx-auto px-6 py-12 md:py-16">
        <header className="mb-12">
          <div
            className="text-xs uppercase tracking-wide mb-3"
            style={{ color: "var(--primary)" }}
          >
            PolicyEngine analysis
          </div>
          <h1
            className="text-4xl md:text-5xl font-semibold leading-tight tracking-tight"
            style={{ color: "var(--foreground)" }}
          >
            How much federal tax does the bottom 50% really pay?
          </h1>
          <p
            className="mt-6 text-lg max-w-3xl"
            style={{ color: "var(--muted-foreground)" }}
          >
            On May 20, 2026, Jeff Bezos cited the statistic that the bottom
            half of US earners pays roughly 3% of federal income tax. The
            number comes from the IRS Statistics of Income tables and is
            accurate as far as it goes — but federal taxes are not only the
            individual income tax.
          </p>
        </header>

        <section className="mb-12">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
            <div>
              <h2
                className="text-2xl font-semibold"
                style={{ color: "var(--foreground)" }}
              >
                Share of federal tax paid by income group
              </h2>
              <p
                className="text-sm mt-1 max-w-2xl"
                style={{ color: "var(--muted-foreground)" }}
              >
                {blurb}
              </p>
            </div>
            <Toggle
              options={taxOptions}
              value={taxView}
              onChange={setTaxView}
              ariaLabel="Tax view"
            />
          </div>
          <ShareChart distribution={distribution} />
        </section>

        <section className="mb-12 grid md:grid-cols-2 gap-6">
          <div>
            <h2
              className="text-2xl font-semibold mb-2"
              style={{ color: "var(--foreground)" }}
            >
              What if we zero out federal income tax for the bottom 50%?
            </h2>
            <p
              className="text-sm"
              style={{ color: "var(--muted-foreground)" }}
            >
              A static estimate of the revenue cost of forgiving federal
              income tax for every tax unit below a given AGI threshold.
              Drag the slider to explore other thresholds. Behavioural
              responses and interactions with refundable credits are not
              modelled.
            </p>
          </div>
          <ThresholdSlider anchor={data.zero_below_bottom_50} />
        </section>

        <section className="mb-12">
          <h2
            className="text-2xl font-semibold mb-4"
            style={{ color: "var(--foreground)" }}
          >
            Income tax vs income + payroll tax: side by side
          </h2>
          <ComparisonTable
            incomeDist={data.income_tax}
            incomePlusPayroll={data.income_plus_payroll}
            source={data.source}
          />
        </section>

        <section
          className="rounded-xl border p-6"
          style={{
            borderColor: "var(--border)",
            backgroundColor: "var(--muted)",
          }}
        >
          <h2
            className="text-lg font-semibold mb-3"
            style={{ color: "var(--foreground)" }}
          >
            Methodology
          </h2>
          <ul
            className="text-sm space-y-2 list-disc pl-5"
            style={{ color: "var(--muted-foreground)" }}
          >
            <li>
              Data mode: <strong>{data.mode}</strong> (
              {data.mode === "live"
                ? "live PolicyEngine-US microsimulation"
                : "Tax Foundation / IRS SOI fallback snapshot — install with [sim] extras and pass --live to regenerate"}
              ).
            </li>
            <li>
              Income-tax shares reflect federal individual income tax (the
              headline figure cited by commentators). Combined shares add
              employee-side payroll tax (Social Security + Medicare).
            </li>
            <li>
              The bottom-50 AGI cutoff is taken directly from the
              distribution. For the live path, it comes from the calibrated
              Enhanced CPS; for the fallback path, from IRS SOI 2023.
            </li>
            <li>
              The &ldquo;zero income tax below threshold&rdquo; estimate is static — the
              static revenue cost equals the baseline income tax paid by all
              tax units below the threshold. Behavioural responses, state
              tax interactions, and changes to refundable credit refunds
              are not modelled.
            </li>
            <li>
              Generated{" "}
              <time dateTime={data.generated_at}>
                {new Date(data.generated_at).toUTCString()}
              </time>{" "}
              by bottom-50-tax-analysis v{data.version}.
            </li>
          </ul>
        </section>

        <footer
          className="mt-12 pt-6 text-xs flex flex-col md:flex-row gap-2 md:gap-6"
          style={{
            borderTop: "1px solid var(--border)",
            color: "var(--muted-foreground)",
          }}
        >
          <span>
            Built by{" "}
            <a
              href="https://policyengine.org"
              style={{ color: "var(--primary)" }}
            >
              PolicyEngine
            </a>
            .
          </span>
          <a
            href="https://github.com/PolicyEngine/bottom-50-tax-analysis"
            style={{ color: "var(--primary)" }}
          >
            Source on GitHub
          </a>
          <a
            href="https://taxfoundation.org/data/all/federal/latest-federal-income-tax-data-2025/"
            style={{ color: "var(--primary)" }}
          >
            Tax Foundation summary
          </a>
        </footer>
      </div>
    </main>
  );
}
