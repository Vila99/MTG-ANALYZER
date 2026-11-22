"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface SingleSeriesBarChartProps {
  title: string;
  data: { label: string; value: number }[];
  colorVar: string; // ej. "var(--chart-mana)"
  valueLabel: string;
}

export function SingleSeriesBarChart({ title, data, colorVar, valueLabel }: SingleSeriesBarChartProps) {
  if (data.length === 0) {
    return (
      <div className="rounded-lg border p-4" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
        <h3 className="text-sm font-semibold mb-2" style={{ color: "var(--foreground)" }}>
          {title}
        </h3>
        <p className="text-sm" style={{ color: "var(--ink-muted)" }}>
          Sin datos.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border p-4" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
      <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--foreground)" }}>
        {title}
      </h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }} barCategoryGap="20%">
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" strokeDasharray="0" />
          <XAxis
            dataKey="label"
            tick={{ fill: "var(--ink-muted)", fontSize: 12 }}
            axisLine={{ stroke: "var(--chart-axis)" }}
            tickLine={false}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fill: "var(--ink-muted)", fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={28}
          />
          <Tooltip
            cursor={{ fill: "var(--surface-muted)" }}
            contentStyle={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              color: "var(--foreground)",
              fontSize: 13,
            }}
            labelStyle={{ color: "var(--ink-secondary)" }}
            formatter={(value) => [`${value ?? 0}`, valueLabel]}
          />
          <Bar
            dataKey="value"
            fill={colorVar}
            radius={[4, 4, 0, 0]}
            maxBarSize={24}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
