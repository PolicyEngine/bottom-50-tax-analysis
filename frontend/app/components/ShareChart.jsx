"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";

function buildData(dist) {
  return [
    { group: "Bottom 50%", share: dist.bottom_50_share, kind: "bottom" },
    {
      group: "50th–75th",
      share: dist.top_50_share - dist.top_25_share,
      kind: "middle",
    },
    {
      group: "75th–90th",
      share: dist.top_25_share - dist.top_10_share,
      kind: "middle",
    },
    {
      group: "90th–95th",
      share: dist.top_10_share - dist.top_5_share,
      kind: "middle",
    },
    {
      group: "95th–99th",
      share: dist.top_5_share - dist.top_1_share,
      kind: "middle",
    },
    { group: "Top 1%", share: dist.top_1_share, kind: "top" },
  ];
}

function colorFor(kind) {
  if (kind === "bottom") return "var(--chart-3)";
  if (kind === "top") return "var(--chart-1)";
  return "var(--chart-2)";
}

export function ShareChart({ distribution }) {
  const data = buildData(distribution);
  return (
    <div className="w-full" style={{ height: 360 }}>
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
          <Bar dataKey="share" radius={[6, 6, 0, 0]}>
            {data.map((d) => (
              <Cell key={d.group} fill={colorFor(d.kind)} />
            ))}
            <LabelList
              dataKey="share"
              position="top"
              formatter={(v) => `${(v * 100).toFixed(1)}%`}
              style={{
                fontSize: 12,
                fontFamily: "var(--font-sans)",
                fill: "var(--foreground)",
              }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
