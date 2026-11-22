"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface BarDatum {
  label: string;
  value: number;
  key?: string;
}

interface SingleSeriesBarChartProps {
  title: string;
  data: BarDatum[];
  colorVar: string; // ej. "var(--chart-mana)"
  valueLabel: string;
  onBarClick?: (item: BarDatum) => void;
  height?: number;
}

export function SingleSeriesBarChart({
  title,
  data,
  colorVar,
  valueLabel,
  onBarClick,
  height = 200,
}: SingleSeriesBarChartProps) {
  if (data.length === 0) {
    return (
      <div className="rounded-sm border p-4" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
        <h3 className="font-head text-xs font-extrabold uppercase tracking-wide mb-2" style={{ color: "var(--ink-muted)" }}>
          {title}
        </h3>
        <p className="text-sm" style={{ color: "var(--ink-muted)" }}>
          Sin datos.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-sm border p-4" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
      <h3 className="font-head text-xs font-extrabold uppercase tracking-wide mb-3" style={{ color: "var(--ink-muted)" }}>
        {title}
        {onBarClick && (
          <span className="ml-2 font-normal normal-case tracking-normal" style={{ color: "var(--ink-muted)" }}>
            (haz clic en una barra para ver las cartas)
          </span>
        )}
      </h3>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 20, right: 8, bottom: 0, left: 0 }} barCategoryGap="20%">
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
            cursor={false}
            contentStyle={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 4,
              color: "var(--foreground)",
              fontSize: 13,
            }}
            labelStyle={{ color: "var(--ink-secondary)" }}
            formatter={(value) => [`${value ?? 0}`, valueLabel]}
          />
          <Bar
            dataKey="value"
            fill={colorVar}
            radius={[2, 2, 0, 0]}
            maxBarSize={24}
            isAnimationActive={false}
            onClick={onBarClick ? (datum) => onBarClick(datum as unknown as BarDatum) : undefined}
            onMouseDown={onBarClick ? (_data, _index, event) => event?.preventDefault() : undefined}
            style={{ cursor: onBarClick ? "pointer" : undefined }}
            background={onBarClick ? { fill: "transparent" } : undefined}
          >
            <LabelList
              dataKey="value"
              position="top"
              style={{ fill: "var(--ink-secondary)", fontSize: 11, fontWeight: 600 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
