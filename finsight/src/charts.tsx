
import type { AnalysisTimelineDay } from "./api";
import { compactMoney, money } from "./format";

interface BalanceChartProps {
  timeline: AnalysisTimelineDay[];
  reserve: number;
  startBalance: number;
}

export function BalanceChart({
  timeline,
  reserve,
  startBalance,
}: BalanceChartProps) {
  if (timeline.length === 0) {
    return <p className="muted">No timeline data available.</p>;
  }

  const width = 760;
  const height = 280;
  const pad = { top: 24, right: 24, bottom: 34, left: 16 };

  const values = [
    startBalance,
    reserve,
    ...timeline.map((day) => day.closing_balance),
  ];
  const max = Math.max(...values);
  const min = Math.min(...values);
  const span = max - min || 1;

  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;

  const x = (index: number) =>
    pad.left + (index / Math.max(timeline.length - 1, 1)) * innerW;
  const y = (value: number) =>
    pad.top + innerH - ((value - min) / span) * innerH;

  const points = timeline.map((day, index) => ({
    px: x(index),
    py: y(day.closing_balance),
    day,
  }));

  const linePath = points
    .map(
      (point, index) =>
        `${index === 0 ? "M" : "L"} ${point.px.toFixed(2)} ${point.py.toFixed(2)}`
    )
    .join(" ");

  const areaPath = `${linePath} L ${points[points.length - 1].px.toFixed(
    2
  )} ${(pad.top + innerH).toFixed(2)} L ${points[0].px.toFixed(2)} ${(
    pad.top + innerH
  ).toFixed(2)} Z`;

  const reserveY = y(reserve);
  const minimum = points.reduce(
    (lowest, point) =>
      point.day.closing_balance < lowest.day.closing_balance ? point : lowest,
    points[0]
  );

  const gridLines = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
    value: min + span * (1 - ratio),
    y: pad.top + innerH * ratio,
  }));

  return (
    <div className="chart-wrap">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="balance-chart"
        role="img"
        aria-label="Projected 30-day balance"
      >
        <defs>
          <linearGradient id="balanceFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="balanceStroke" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#06b6d4" />
          </linearGradient>
        </defs>

        {gridLines.map((line) => (
          <g key={line.y}>
            <line
              x1={pad.left}
              y1={line.y}
              x2={width - pad.right}
              y2={line.y}
              className="chart-grid"
            />
            <text x={pad.left} y={line.y - 4} className="chart-axis-label">
              {compactMoney(line.value)}
            </text>
          </g>
        ))}

        <line
          x1={pad.left}
          y1={reserveY}
          x2={width - pad.right}
          y2={reserveY}
          className="chart-reserve"
        />
        <text
          x={width - pad.right}
          y={reserveY - 6}
          textAnchor="end"
          className="chart-reserve-label"
        >
          Reserve {compactMoney(reserve)}
        </text>

        <path d={areaPath} fill="url(#balanceFill)" />
        <path d={linePath} fill="none" stroke="url(#balanceStroke)" strokeWidth="3" />

        <circle
          cx={minimum.px}
          cy={minimum.py}
          r="5"
          className={
            minimum.day.closing_balance < reserve
              ? "chart-point risk"
              : "chart-point"
          }
        />

        {timeline.map((day, index) =>
          day.day % 5 === 0 || day.day === 1 || day.day === timeline.length ? (
            <text
              key={day.day}
              x={x(index)}
              y={height - 12}
              textAnchor="middle"
              className="chart-axis-label"
            >
              {day.day}
            </text>
          ) : null
        )}
      </svg>
      <p className="chart-caption">
        Lowest projected balance {money(minimum.day.closing_balance)} on day{" "}
        {minimum.day.day}.
      </p>
    </div>
  );
}

interface CategoryBarsProps {
  items: {
    category: string;
    total: number;
    count: number;
    share: number;
  }[];
}

export function CategoryBars({ items }: CategoryBarsProps) {
  if (items.length === 0) {
    return <p className="muted">No purchases to break down yet.</p>;
  }

  return (
    <div className="cat-bars">
      {items.map((item, index) => (
        <div className="cat-bar-row" key={item.category}>
          <div className="cat-bar-head">
            <span className="cat-name">
              {item.category}
              <span className="cat-count">×{item.count}</span>
            </span>
            <span className="cat-total">{money(item.total)}</span>
          </div>
          <div className="cat-bar-track">
            <div
              className="cat-bar-fill"
              style={{
                width: `${Math.max(item.share, 4)}%`,
                animationDelay: `${index * 70}ms`,
              }}
            />
          </div>
          <span className="cat-share">{item.share}%</span>
        </div>
      ))}
    </div>
  );
}
