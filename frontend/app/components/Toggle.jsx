"use client";

export function Toggle({ options, value, onChange, ariaLabel }) {
  return (
    <div
      className="inline-flex rounded-lg border p-1"
      style={{
        borderColor: "var(--border)",
        backgroundColor: "var(--muted)",
      }}
      role="tablist"
      aria-label={ariaLabel}
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(opt.value)}
            className="px-4 py-2 rounded-md text-sm font-medium transition-colors"
            style={{
              backgroundColor: active ? "var(--background)" : "transparent",
              color: active ? "var(--primary)" : "var(--muted-foreground)",
              boxShadow: active ? "0 1px 2px rgb(0 0 0 / 0.04)" : "none",
            }}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
