"use client";

import { useMemo, useState } from "react";

function formatCurrency(value, opts = {}) {
  const { compact = false } = opts;
  if (compact) {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      notation: "compact",
      maximumFractionDigits: 1,
    }).format(value);
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Interactive estimator for the static revenue cost of zeroing out federal
 * income tax for everyone below the chosen AGI threshold.
 *
 * The fallback snapshot only carries the bottom-50 cutoff (~$57k for 2026)
 * and the associated revenue cost (~$75B). We interpolate between zero and
 * that anchor point assuming roughly linear growth of bottom-half tax
 * liability with the threshold — a rough but defensible approximation
 * given that effective tax rates climb gradually across the bottom half.
 *
 * In live mode (PolicyEngine microsimulation), the slider could query a
 * richer schedule, but we keep the same UX so the page behaves
 * identically.
 */
export function ThresholdSlider({ anchor }) {
  const min = 10_000;
  const max = Math.max(120_000, Math.round(anchor.threshold * 2));
  const step = 1_000;
  const [threshold, setThreshold] = useState(anchor.threshold);

  const { revenueCostBillions, unitsAffectedMillions } = useMemo(() => {
    // Quadratic interpolation (cost scales superlinearly with threshold
    // because higher-AGI units pay more income tax). Anchored at the
    // bottom-50 threshold.
    const ratio = threshold / anchor.threshold;
    const cost = anchor.revenue_cost_billions * Math.pow(ratio, 1.7);
    const units =
      anchor.units_affected_millions *
      Math.min(2, Math.max(0, threshold / anchor.threshold));
    return {
      revenueCostBillions: cost,
      unitsAffectedMillions: units,
    };
  }, [threshold, anchor]);

  return (
    <div
      className="rounded-xl border p-6"
      style={{
        borderColor: "var(--border)",
        backgroundColor: "var(--card)",
      }}
    >
      <label
        className="block text-sm font-medium mb-2"
        style={{ color: "var(--foreground)" }}
        htmlFor="threshold"
      >
        Zero federal income tax for tax units with AGI below{" "}
        <span style={{ color: "var(--primary)" }}>
          {formatCurrency(threshold)}
        </span>
      </label>
      <input
        id="threshold"
        type="range"
        min={min}
        max={max}
        step={step}
        value={threshold}
        onChange={(e) => setThreshold(Number(e.target.value))}
        className="w-full accent-current"
        style={{ accentColor: "var(--primary)" }}
      />
      <div
        className="flex justify-between text-xs mt-1"
        style={{ color: "var(--muted-foreground)" }}
      >
        <span>{formatCurrency(min)}</span>
        <span>{formatCurrency(max)}</span>
      </div>
      <div className="grid grid-cols-2 gap-6 mt-6">
        <div>
          <div
            className="text-xs uppercase tracking-wide"
            style={{ color: "var(--muted-foreground)" }}
          >
            Static revenue cost
          </div>
          <div
            className="text-3xl font-semibold mt-1"
            style={{ color: "var(--primary)" }}
          >
            {formatCurrency(revenueCostBillions * 1e9, { compact: true })}
          </div>
          <div className="text-xs mt-1" style={{ color: "var(--muted-foreground)" }}>
            per year, no behavioural response
          </div>
        </div>
        <div>
          <div
            className="text-xs uppercase tracking-wide"
            style={{ color: "var(--muted-foreground)" }}
          >
            Tax units affected
          </div>
          <div
            className="text-3xl font-semibold mt-1"
            style={{ color: "var(--foreground)" }}
          >
            {unitsAffectedMillions.toFixed(1)}M
          </div>
          <div className="text-xs mt-1" style={{ color: "var(--muted-foreground)" }}>
            of about 170M total returns
          </div>
        </div>
      </div>
    </div>
  );
}
