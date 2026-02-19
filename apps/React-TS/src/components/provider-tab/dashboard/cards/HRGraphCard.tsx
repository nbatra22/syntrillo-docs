import React from 'react';
import { c } from '../theme';
import type { HRTimeSeriesPoint } from '../data/staticData';

interface HeartRate {
  current: number;
  currentDate: string;
  avgResting: number;
  baselineDateRange: string;
}

interface Props {
  heartRate: HeartRate;
  data: HRTimeSeriesPoint[];
}

const fmtDate = (iso: string): string => {
  const [, m, d] = iso.split('-');
  return `${parseInt(m)}/${parseInt(d)}`;
};

const HRGraphCard: React.FC<Props> = ({ heartRate, data }) => {
  const W = 560, H = 140;
  const pad = { top: 12, right: 44, bottom: 28, left: 40 };
  const cw = W - pad.left - pad.right;
  const ch = H - pad.top - pad.bottom;

  const vals = data.map(d => d.value);
  const rawMin = Math.min(...vals);
  const rawMax = Math.max(...vals);
  const minY = Math.floor((rawMin - 5) / 5) * 5;
  const maxY = Math.ceil((rawMax + 5) / 5) * 5;
  const range = maxY - minY || 10;

  const xPos = (i: number): number =>
    data.length <= 1 ? cw / 2 : (i / (data.length - 1)) * cw;
  const yPos = (v: number): number => ch * (1 - (v - minY) / range);

  const path = data
    .map((d, i) => `${i === 0 ? 'M' : 'L'}${xPos(i).toFixed(1)},${yPos(d.value).toFixed(1)}`)
    .join(' ');

  const yStep = Math.ceil(range / 3 / 5) * 5 || 5;
  const yTicks: number[] = [];
  for (let v = minY; v <= maxY + 0.5; v += yStep) yTicks.push(Math.round(v));

  const last = data.length - 1;
  const lblStep = Math.max(1, Math.floor(data.length / 4));
  const showLbl = (i: number) =>
    i === 0 || i === last || (i % lblStep === 0 && i < last - 1);

  return (
    <div style={{
      backgroundColor: c.bgCard,
      border: `1px solid ${c.border}`,
      borderRadius: c.r,
      padding: '20px 24px',
      boxShadow: c.shadow,
    }}>
      <h3 style={{ margin: '0 0 16px', color: c.txt1, fontSize: '16px', fontWeight: 700, letterSpacing: '-0.01em' }}>
        Heart Rate
      </h3>

      {/* Numerical measurements — two stats side by side */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <div style={{ flex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <span style={{ color: c.txt2, fontSize: '13px' }}>Heart Rate</span>
          <span style={{ color: c.txt1, fontSize: '26px', fontWeight: 800, letterSpacing: '-0.02em' }}>
            {heartRate.current.toFixed(2)}
          </span>
        </div>
        <div style={{ width: '1px', backgroundColor: c.divider, alignSelf: 'stretch' }} />
        <div style={{ flex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', paddingLeft: '8px' }}>
          <span style={{ color: c.txt2, fontSize: '13px' }}>Avg. Resting Heart Rate</span>
          <span style={{ color: c.txt1, fontSize: '26px', fontWeight: 800, letterSpacing: '-0.02em' }}>
            {heartRate.avgResting.toFixed(2)}
          </span>
        </div>
      </div>

      <div style={{ borderTop: `1px solid ${c.divider}`, margin: '0 0 12px' }} />

      {/* Line graph */}
      {data.length < 2 ? (
        <p style={{ color: c.txt3, textAlign: 'center', padding: '16px 0', fontSize: '13px' }}>
          No data available.
        </p>
      ) : (
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          <g transform={`translate(${pad.left},${pad.top})`}>
            {/* Y grid lines */}
            {yTicks.map(v => (
              <line key={v} x1={0} y1={yPos(v)} x2={cw} y2={yPos(v)} stroke={c.divider} strokeWidth={1} />
            ))}

            {/* Line */}
            <path d={path} fill="none" stroke={c.accent} strokeWidth={1.5} strokeLinejoin="round" />

            {/* Dots */}
            {data.map((d, i) => (
              <circle key={i} cx={xPos(i)} cy={yPos(d.value)} r={i === last ? 4 : 2} fill={c.accent} />
            ))}

            {/* Most recent value label */}
            <text x={xPos(last) + 7} y={yPos(data[last].value)} fontSize={10} fill={c.accent} dominantBaseline="middle">
              {data[last].value.toFixed(1)}
            </text>

            {/* Y-axis labels */}
            {yTicks.map(v => (
              <text key={v} x={-6} y={yPos(v)} textAnchor="end" fontSize={10} fill={c.txt3} dominantBaseline="middle">
                {v}
              </text>
            ))}

            {/* Y-axis unit */}
            <text transform={`translate(-28, ${ch / 2}) rotate(-90)`} textAnchor="middle" fontSize={9} fill={c.txt3}>
              BPM
            </text>

            {/* X-axis line */}
            <line x1={0} y1={ch} x2={cw} y2={ch} stroke={c.border} strokeWidth={1} />

            {/* X-axis labels */}
            {data.map((d, i) => showLbl(i) ? (
              <text key={i} x={xPos(i)} y={ch + 14} textAnchor="middle" fontSize={9} fill={c.txt3}>
                {fmtDate(d.date)}
              </text>
            ) : null)}
          </g>
        </svg>
      )}
    </div>
  );
};

export default HRGraphCard;
