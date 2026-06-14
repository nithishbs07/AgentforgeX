import React, { useState } from "react";

// Types
interface ChartDataPoint {
  [key: string]: any;
}

interface LineChartProps {
  data: ChartDataPoint[];
  xKey: string;
  yKeys: string[];
  colors: string[];
  yLabel?: string;
  minY?: number;
  maxY?: number;
}

export const LineChart: React.FC<LineChartProps> = ({
  data,
  xKey,
  yKeys,
  colors,
  yLabel = "",
  minY,
  maxY
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return (
      <div style={{ display: "flex", height: "180px", alignItems: "center", justifyContent: "center", color: "#6b7280" }}>
        No data available
      </div>
    );
  }

  // Dimension settings
  const width = 500;
  const height = 250;
  const paddingLeft = 55;
  const paddingRight = 20;
  const paddingTop = 20;
  const paddingBottom = 40;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  // Find range of Y
  let resolvedMinY = minY !== undefined ? minY : 0;
  let resolvedMaxY = maxY !== undefined ? maxY : 1.0;

  if (minY === undefined || maxY === undefined) {
    let allYValues: number[] = [];
    data.forEach((d) => {
      yKeys.forEach((key) => {
        if (typeof d[key] === "number") {
          allYValues.push(d[key]);
        }
      });
    });
    
    if (allYValues.length > 0) {
      const actualMin = Math.min(...allYValues);
      const actualMax = Math.max(...allYValues);
      
      if (minY === undefined) resolvedMinY = Math.max(0, actualMin - (actualMax - actualMin) * 0.1);
      if (maxY === undefined) resolvedMaxY = actualMax + (actualMax - actualMin) * 0.1 || 1.0;
    }
  }

  const yRange = resolvedMaxY - resolvedMinY || 1;

  // Calculate points
  const pointsList = yKeys.map((yKey) => {
    return data.map((d, index) => {
      const val = typeof d[yKey] === "number" ? d[yKey] : 0;
      const x = paddingLeft + (index / Math.max(1, data.length - 1)) * chartWidth;
      const y = paddingTop + chartHeight - ((val - resolvedMinY) / yRange) * chartHeight;
      return { x, y, value: val, label: d[xKey], key: yKey };
    });
  });

  // Grid lines
  const gridLines = 4;
  const gridValues = Array.from({ length: gridLines + 1 }, (_, i) => {
    return resolvedMinY + (i / gridLines) * yRange;
  });

  return (
    <div style={{ position: "relative", width: "100%" }}>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="100%" style={{ overflow: "visible" }}>
        <defs>
          {yKeys.map((key, i) => (
            <linearGradient key={`grad-${key}`} id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={colors[i]} stopOpacity="0.45" />
              <stop offset="100%" stopColor={colors[i]} stopOpacity="0.0" />
            </linearGradient>
          ))}
        </defs>

        {/* Grid lines & Y-Axis Labels */}
        {gridValues.map((val, idx) => {
          const y = paddingTop + chartHeight - (idx / gridLines) * chartHeight;
          return (
            <g key={`grid-${idx}`}>
              <line
                x1={paddingLeft}
                y1={y}
                x2={width - paddingRight}
                y2={y}
                stroke="#1e293b"
                strokeWidth={1}
                strokeDasharray="4 4"
              />
              <text
                x={paddingLeft - 10}
                y={y + 4}
                fill="#9ca3af"
                fontSize={10}
                textAnchor="end"
              >
                {val >= 10 ? Math.round(val) : val.toFixed(2)}
              </text>
            </g>
          );
        })}

        {/* X-Axis labels (every few points) */}
        {data.map((d, index) => {
          const showLabel = 
            data.length <= 10 || 
            index === 0 || 
            index === data.length - 1 || 
            (data.length > 10 && index % Math.floor(data.length / 5) === 0);
          
          if (!showLabel) return null;
          
          const x = paddingLeft + (index / Math.max(1, data.length - 1)) * chartWidth;
          let labelText = d[xKey];
          if (labelText && labelText.includes("T")) {
            // Simplify ISO timestamp to HH:MM
            try {
              const timePart = labelText.split("T")[1];
              labelText = timePart.substring(0, 5);
            } catch {}
          }
          
          return (
            <text
              key={`x-lbl-${index}`}
              x={x}
              y={height - 15}
              fill="#9ca3af"
              fontSize={10}
              textAnchor="middle"
            >
              {labelText}
            </text>
          );
        })}

        {/* Paths & Gradients */}
        {pointsList.map((points, pathIdx) => {
          if (points.length === 0) return null;
          
          // Construct path string
          const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
          
          // Closed path for gradient fill
          const areaD = `${pathD} L ${points[points.length - 1].x} ${paddingTop + chartHeight} L ${points[0].x} ${paddingTop + chartHeight} Z`;

          return (
            <g key={`line-group-${pathIdx}`}>
              {/* Gradient Area */}
              <path d={areaD} fill={`url(#grad-${yKeys[pathIdx]})`} />
              
              {/* Stroke Line */}
              <path
                d={pathD}
                fill="none"
                stroke={colors[pathIdx]}
                strokeWidth={2.5}
                strokeLinecap="round"
              />
            </g>
          );
        })}

        {/* Interactive hover overlays */}
        {data.map((_, index) => {
          const x = paddingLeft + (index / Math.max(1, data.length - 1)) * chartWidth;
          return (
            <g key={`hover-zone-${index}`}>
              {/* Invisible wide vertical hit box */}
              <rect
                x={x - (chartWidth / Math.max(1, data.length - 1)) / 2}
                y={paddingTop}
                width={chartWidth / Math.max(1, data.length - 1)}
                height={chartHeight}
                fill="transparent"
                style={{ cursor: "pointer" }}
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
              />
              {hoveredIndex === index && (
                <line
                  x1={x}
                  y1={paddingTop}
                  x2={x}
                  y2={paddingTop + chartHeight}
                  stroke="#4f46e5"
                  strokeWidth={1.5}
                  strokeDasharray="2 2"
                />
              )}
            </g>
          );
        })}

        {/* Hover points */}
        {hoveredIndex !== null && pointsList.map((points, pathIdx) => {
          const p = points[hoveredIndex];
          if (!p) return null;
          return (
            <circle
              key={`h-dot-${pathIdx}`}
              cx={p.x}
              cy={p.y}
              r={5}
              fill="#0b0f19"
              stroke={colors[pathIdx]}
              strokeWidth={3}
            />
          );
        })}
      </svg>

      {/* Tooltip Overlay */}
      {hoveredIndex !== null && (
        <div style={{
          position: "absolute",
          top: "10px",
          left: "60px",
          backgroundColor: "rgba(17, 24, 39, 0.95)",
          border: "1px solid #334155",
          borderRadius: "8px",
          padding: "8px 12px",
          fontSize: "12px",
          color: "#f3f4f6",
          zIndex: 10,
          boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)",
          backdropFilter: "blur(4px)",
          pointerEvents: "none"
        }}>
          <div style={{ color: "#9ca3af", fontWeight: 600, marginBottom: "4px" }}>
            {data[hoveredIndex][xKey] && data[hoveredIndex][xKey].includes("T")
              ? new Date(data[hoveredIndex][xKey]).toLocaleString()
              : `Point ${hoveredIndex + 1}`}
          </div>
          {yKeys.map((key, i) => (
            <div key={key} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: colors[i] }}></span>
              <span style={{ textTransform: "capitalize", color: "#d1d5db" }}>
                {key.replace(/_ms|_score|before_|after_/g, " ").trim()}:
              </span>
              <span style={{ fontWeight: "bold" }}>
                {typeof data[hoveredIndex][key] === "number" 
                  ? data[hoveredIndex][key].toFixed(3) 
                  : data[hoveredIndex][key]}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};


interface BarChartProps {
  data: { range: string; count: number }[];
  color: string;
  yLabel?: string;
}

export const BarChart: React.FC<BarChartProps> = ({
  data,
  color,
  yLabel = ""
}) => {
  if (!data || data.length === 0) {
    return (
      <div style={{ display: "flex", height: "180px", alignItems: "center", justifyContent: "center", color: "#6b7280" }}>
        No data available
      </div>
    );
  }

  const width = 400;
  const height = 200;
  const paddingLeft = 40;
  const paddingRight = 15;
  const paddingTop = 15;
  const paddingBottom = 35;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const maxCount = Math.max(...data.map(d => d.count), 1);
  const barWidth = (chartWidth / data.length) * 0.65;
  const gap = (chartWidth / data.length) * 0.35;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="100%" style={{ overflow: "visible" }}>
      <defs>
        <linearGradient id={`bar-grad-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="1" />
          <stop offset="100%" stopColor={color} stopOpacity="0.3" />
        </linearGradient>
      </defs>

      {/* Grid Lines */}
      {Array.from({ length: 4 }).map((_, idx) => {
        const y = paddingTop + chartHeight - (idx / 3) * chartHeight;
        const val = Math.round((idx / 3) * maxCount);
        return (
          <g key={`bg-${idx}`}>
            <line
              x1={paddingLeft}
              y1={y}
              x2={width - paddingRight}
              y2={y}
              stroke="#1e293b"
              strokeWidth={1}
            />
            <text
              x={paddingLeft - 8}
              y={y + 3}
              fill="#9ca3af"
              fontSize={10}
              textAnchor="end"
            >
              {val}
            </text>
          </g>
        );
      })}

      {/* Bars */}
      {data.map((d, idx) => {
        const x = paddingLeft + idx * (barWidth + gap) + gap / 2;
        const rectHeight = (d.count / maxCount) * chartHeight;
        const y = paddingTop + chartHeight - rectHeight;

        return (
          <g key={`bar-${idx}`} style={{ cursor: "pointer" }}>
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={rectHeight}
              rx={3}
              fill={`url(#bar-grad-${color.replace("#", "")})`}
              style={{ transition: "all 0.2s" }}
            />
            
            {/* Value on top of bar */}
            {d.count > 0 && (
              <text
                x={x + barWidth / 2}
                y={y - 5}
                fill="#ffffff"
                fontSize={9}
                fontWeight="bold"
                textAnchor="middle"
              >
                {d.count}
              </text>
            )}

            {/* Label below bar */}
            <text
              x={x + barWidth / 2}
              y={height - 10}
              fill="#9ca3af"
              fontSize={10}
              textAnchor="middle"
            >
              {d.range}
            </text>
          </g>
        );
      })}
    </svg>
  );
};


interface PieChartProps {
  data: { name: string; value: number; color: string }[];
}

export const PieChart: React.FC<PieChartProps> = ({ data }) => {
  const total = data.reduce((acc, item) => acc + item.value, 0);

  if (total === 0) {
    return (
      <div style={{ display: "flex", height: "180px", alignItems: "center", justifyContent: "center", color: "#6b7280" }}>
        No data available
      </div>
    );
  }

  // Draw donut chart using svg paths
  let accumulatedPercent = 0;

  const getCoordinatesForPercent = (percent: number) => {
    const x = Math.cos(2 * Math.PI * percent);
    const y = Math.sin(2 * Math.PI * percent);
    return [x, y];
  };

  const slices = data.map((item) => {
    const percent = item.value / total;
    const [startX, startY] = getCoordinatesForPercent(accumulatedPercent);
    accumulatedPercent += percent;
    const [endX, endY] = getCoordinatesForPercent(accumulatedPercent);

    if (percent === 1) {
      return {
        isFull: true,
        color: item.color,
        name: item.name,
        value: item.value,
        percent: percent * 100
      };
    }

    const largeArcFlag = percent > 0.5 ? 1 : 0;
    
    // SVG path definition
    const pathData = [
      `M ${startX * 50} ${startY * 50}`, // Move to outer start
      `A 50 50 0 ${largeArcFlag} 1 ${endX * 50} ${endY * 50}`, // Arc to outer end
      `L ${endX * 30} ${endY * 30}`, // Line to inner end
      `A 30 30 0 ${largeArcFlag} 0 ${startX * 30} ${startY * 30}`, // Arc back to inner start
      "Z" // Close path
    ].join(" ");

    return {
      isFull: false,
      pathData,
      color: item.color,
      name: item.name,
      value: item.value,
      percent: percent * 100
    };
  });

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "15px" }}>
      {/* SVG Canvas */}
      <div style={{ width: "130px", height: "130px" }}>
        <svg viewBox="-60 -60 120 120" style={{ transform: "rotate(-90deg)", width: "100%", height: "100%" }}>
          {slices.map((slice, idx) => {
            if (slice.isFull) {
              return (
                <circle
                  key={`full-${idx}`}
                  cx="0"
                  cy="0"
                  r="40"
                  fill="none"
                  stroke={slice.color}
                  strokeWidth="20"
                />
              );
            }
            return (
              <path
                key={`slice-${idx}`}
                d={slice.pathData}
                fill={slice.color}
                style={{ transition: "all 0.3s" }}
              />
            );
          })}
        </svg>
      </div>

      {/* Legend */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
        {data.map((item, idx) => {
          const percent = total > 0 ? (item.value / total) * 100 : 0;
          return (
            <div key={`legend-${idx}`} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px" }}>
              <span style={{
                width: "12px",
                height: "12px",
                borderRadius: "3px",
                backgroundColor: item.color,
                display: "inline-block",
                flexShrink: 0
              }}></span>
              <span style={{ color: "#d1d5db", whiteSpace: "nowrap" }}>{item.name}:</span>
              <span style={{ fontWeight: "bold", marginLeft: "auto" }}>
                {item.value} ({percent.toFixed(0)}%)
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
