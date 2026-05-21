"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Legend,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";

const BUCKETS = [
  { key: "bottom_50_share", label: "Bottom 50%" },
  { key: "top_25_share", label: "Top 25%" },
  { key: "top_10_share", label: "Top 10%" },
  { key: "top_5_share", label: "Top 5%" },
  { key: "top_1_share", label: "Top 1%" },
];

function formatShare(v) {
  if (v == null) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

function formatCurrency(v) {
  if (v == null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(v);
}

function buildChartData(pe, soi) {
  return BUCKETS.map(({ key, label }) => ({
    group: label,
    PolicyEngine: pe[key],
    "IRS SOI 2023": soi[key],
  }));
}

export function PolicyEngineVsSOIPanel({ peDist, soi, peYear, soiYear }) {
  const data = buildChartData(peDist, soi.income_tax);

  return (
    <div
      className="rounded-xl border p-6"
      style={{
        borderColor: "var(--border)",
        backgroundColor: "var(--card)",
      }}
    >
      <div className="mb-6">
        <h3
          className="text-lg font-semibold"
          style={{ color: "var(--foreground)" }}
        >
          PolicyEngine ({peYear}) vs IRS SOI ({soiYear})
        </h3>
        <p
          className="text-sm mt-1"
          style={{ color: "var(--muted-foreground)" }}
        >
          Both series report gross federal individual income tax (regular tax
          + AMT + NIIT + cap-gains tax, after non-refundable credits, before
          refundable credits) on filed returns. PE is uprated to {peYear}{" "}
          from the plain Census CPS — its total revenue ($2.13T) matches
          the IRS SOI {soiYear} tabulation ($2.14T) to within 1%.
        </p>
        <p
          className="text-sm mt-2"
          style={{ color: "var(--muted-foreground)" }}
        >
          PE understates the top-1% share because the Census CPS top-codes
          very high incomes (the highest AGI in this dataset is ~$3.3M).
          PolicyEngine&rsquo;s default <code>enhanced_cps_2024</code>{" "}
          combines the CPS with the IRS Public Use File and reweights to
          IRS SOI and CBO aggregate targets — but at present it{" "}
          <strong>overshoots its own CBO target by ~1.86×</strong> in 2024,
          2025, and 2026 (e.g. $5.1T vs the CBO 2026 target of $2.75T).
          That&rsquo;s a calibration regression in the upstream dataset,
          not an intentional measurement of a different concept. For an
          SOI replication, plain CPS is the closer match here; pass{" "}
          <code>--dataset enhanced_cps_2024</code> to see the alternative.
        </p>
      </div>

      <div className="w-full" style={{ height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 24, right: 16, bottom: 8, left: 8 }}
          >
            <CartesianGrid
              stroke="var(--border)"
              strokeDasharray="3 3"
              vertical={false}
            />
            <XAxis
              dataKey="group"
              tick={{
                fontSize: 12,
                fontFamily: "var(--font-sans)",
                fill: "var(--muted-foreground)",
              }}
              axisLine={{ stroke: "var(--border)" }}
              tickLine={false}
            />
            <YAxis
              tickFormatter={(v) => `${Math.round(v * 100)}%`}
              domain={[0, "auto"]}
              tick={{
                fontSize: 12,
                fontFamily: "var(--font-sans)",
                fill: "var(--muted-foreground)",
              }}
              axisLine={false}
              tickLine={false}
            />
            <Legend
              wrapperStyle={{
                fontSize: 12,
                fontFamily: "var(--font-sans)",
                color: "var(--foreground)",
              }}
            />
            <Bar dataKey="PolicyEngine" radius={[4, 4, 0, 0]}>
              {data.map((d) => (
                <Cell key={`pe-${d.group}`} fill="var(--chart-1)" />
              ))}
              <LabelList
                dataKey="PolicyEngine"
                position="top"
                formatter={(v) => `${(v * 100).toFixed(1)}%`}
                style={{
                  fontSize: 11,
                  fontFamily: "var(--font-sans)",
                  fill: "var(--foreground)",
                }}
              />
            </Bar>
            <Bar dataKey="IRS SOI 2023" radius={[4, 4, 0, 0]}>
              {data.map((d) => (
                <Cell key={`soi-${d.group}`} fill="var(--chart-2)" />
              ))}
              <LabelList
                dataKey="IRS SOI 2023"
                position="top"
                formatter={(v) => `${(v * 100).toFixed(1)}%`}
                style={{
                  fontSize: 11,
                  fontFamily: "var(--font-sans)",
                  fill: "var(--foreground)",
                }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <table className="w-full text-sm mt-6">
        <thead>
          <tr>
            <th
              className="text-left px-3 py-2 font-medium"
              style={{
                color: "var(--muted-foreground)",
                borderBottom: "1px solid var(--border)",
              }}
            >
              Statistic
            </th>
            <th
              className="text-right px-3 py-2 font-medium"
              style={{
                color: "var(--muted-foreground)",
                borderBottom: "1px solid var(--border)",
              }}
            >
              PolicyEngine {peYear}
            </th>
            <th
              className="text-right px-3 py-2 font-medium"
              style={{
                color: "var(--muted-foreground)",
                borderBottom: "1px solid var(--border)",
              }}
            >
              IRS SOI {soiYear}
            </th>
            <th
              className="text-right px-3 py-2 font-medium"
              style={{
                color: "var(--muted-foreground)",
                borderBottom: "1px solid var(--border)",
              }}
            >
              Difference
            </th>
          </tr>
        </thead>
        <tbody>
          {BUCKETS.map(({ key, label }) => {
            const pe = peDist[key];
            const sv = soi.income_tax[key];
            const diff = pe - sv;
            return (
              <tr
                key={key}
                style={{ borderBottom: "1px solid var(--border)" }}
              >
                <td className="px-3 py-2" style={{ color: "var(--foreground)" }}>
                  {label} share
                </td>
                <td
                  className="text-right px-3 py-2 font-medium"
                  style={{ color: "var(--foreground)" }}
                >
                  {formatShare(pe)}
                </td>
                <td
                  className="text-right px-3 py-2 font-medium"
                  style={{ color: "var(--foreground)" }}
                >
                  {formatShare(sv)}
                </td>
                <td
                  className="text-right px-3 py-2 font-medium"
                  style={{
                    color:
                      Math.abs(diff) < 0.005
                        ? "var(--muted-foreground)"
                        : "var(--foreground)",
                  }}
                >
                  {(diff * 100 > 0 ? "+" : "") + (diff * 100).toFixed(1)} pp
                </td>
              </tr>
            );
          })}
          <tr style={{ borderBottom: "1px solid var(--border)" }}>
            <td className="px-3 py-2" style={{ color: "var(--foreground)" }}>
              Bottom 50% AGI cutoff
            </td>
            <td
              className="text-right px-3 py-2 font-medium"
              style={{ color: "var(--foreground)" }}
            >
              {formatCurrency(peDist.bottom_50_cutoff)}
            </td>
            <td
              className="text-right px-3 py-2 font-medium"
              style={{ color: "var(--foreground)" }}
            >
              {formatCurrency(soi.income_tax.bottom_50_cutoff)}
            </td>
            <td
              className="text-right px-3 py-2"
              style={{ color: "var(--muted-foreground)" }}
            >
              {peDist.bottom_50_cutoff > soi.income_tax.bottom_50_cutoff
                ? "PE higher"
                : "SOI higher"}
            </td>
          </tr>
          <tr>
            <td className="px-3 py-2" style={{ color: "var(--foreground)" }}>
              Top 1% AGI cutoff
            </td>
            <td
              className="text-right px-3 py-2 font-medium"
              style={{ color: "var(--foreground)" }}
            >
              {formatCurrency(peDist.top_1_cutoff)}
            </td>
            <td
              className="text-right px-3 py-2 font-medium"
              style={{ color: "var(--foreground)" }}
            >
              {formatCurrency(soi.income_tax.top_1_cutoff)}
            </td>
            <td
              className="text-right px-3 py-2"
              style={{ color: "var(--muted-foreground)" }}
            >
              {peDist.top_1_cutoff > soi.income_tax.top_1_cutoff
                ? "PE higher"
                : "SOI higher"}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
