"use client";

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

export function ComparisonTable({ incomeDist, incomePlusPayroll, source }) {
  const rows = [
    {
      label: "Bottom 50% share",
      income: incomeDist.bottom_50_share,
      combined: incomePlusPayroll.bottom_50_share,
    },
    {
      label: "Top 50% share",
      income: incomeDist.top_50_share,
      combined: incomePlusPayroll.top_50_share,
    },
    {
      label: "Top 25% share",
      income: incomeDist.top_25_share,
      combined: incomePlusPayroll.top_25_share,
    },
    {
      label: "Top 10% share",
      income: incomeDist.top_10_share,
      combined: incomePlusPayroll.top_10_share,
    },
    {
      label: "Top 5% share",
      income: incomeDist.top_5_share,
      combined: incomePlusPayroll.top_5_share,
    },
    {
      label: "Top 1% share",
      income: incomeDist.top_1_share,
      combined: incomePlusPayroll.top_1_share,
    },
    {
      label: "Bottom 50% AGI cutoff",
      income: formatCurrency(incomeDist.bottom_50_cutoff),
      combined: formatCurrency(incomePlusPayroll.bottom_50_cutoff),
      raw: true,
    },
    {
      label: "Top 1% AGI cutoff",
      income: formatCurrency(incomeDist.top_1_cutoff),
      combined: formatCurrency(incomePlusPayroll.top_1_cutoff),
      raw: true,
    },
  ];

  return (
    <div
      className="rounded-xl border overflow-hidden"
      style={{
        borderColor: "var(--border)",
        backgroundColor: "var(--card)",
      }}
    >
      <table className="w-full text-sm">
        <thead>
          <tr style={{ backgroundColor: "var(--muted)" }}>
            <th
              className="text-left px-4 py-3 font-medium"
              style={{ color: "var(--muted-foreground)" }}
            >
              Group
            </th>
            <th
              className="text-right px-4 py-3 font-medium"
              style={{ color: "var(--muted-foreground)" }}
            >
              Income tax only
            </th>
            <th
              className="text-right px-4 py-3 font-medium"
              style={{ color: "var(--muted-foreground)" }}
            >
              Income + payroll
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr
              key={r.label}
              style={{
                borderTop: "1px solid var(--border)",
                backgroundColor:
                  i % 2 === 0 ? "var(--card)" : "var(--secondary)",
              }}
            >
              <td className="px-4 py-3" style={{ color: "var(--foreground)" }}>
                {r.label}
              </td>
              <td
                className="text-right px-4 py-3 font-medium"
                style={{ color: "var(--foreground)" }}
              >
                {r.raw ? r.income : formatShare(r.income)}
              </td>
              <td
                className="text-right px-4 py-3 font-medium"
                style={{ color: "var(--foreground)" }}
              >
                {r.raw ? r.combined : formatShare(r.combined)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div
        className="px-4 py-3 text-xs"
        style={{
          borderTop: "1px solid var(--border)",
          color: "var(--muted-foreground)",
          backgroundColor: "var(--muted)",
        }}
      >
        {source}
      </div>
    </div>
  );
}
