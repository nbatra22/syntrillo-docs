import React from 'react';
import { c } from '../theme';
import type { BPTimeSeriesPoint } from '../data/staticData';

interface Props {
  data: BPTimeSeriesPoint[];
}

const fmtDate = (iso: string): string => {
  const [, m, d] = iso.split('-');
  return `${parseInt(m)}/${parseInt(d)}`;
};

const BPGraphCard: React.FC<Props> = ({ data }) => {
  const W = 560, H = 180;
  const pad = { top: 16, right: 48, bottom: 32, left: 44 };
  const cw = W - pad.left - pad.right;
  const ch = H - pad.top - pad.bottom;

  const allVals = data.flatMap(d => [d.systolic, d.diastolic]);
  const rawMin = Math.min(...allVals);
  const rawMax = Math.max(...allVals);
  const minY = Math.floor((rawMin - 15) / 10) * 10;
  const maxY = Math.ceil((rawMax + 15) / 10) * 10;
  const range = maxY - minY;

  const xPos = (i: number): number =>
    data.length <= 1 ? cw / 2 : (i / (data.length - 1)) * cw;
  const yPos = (v: number): number => ch * (1 - (v - minY) / range);

  const sbpPath = data
    .map((d, i) => `${i === 0 ? 'M' : 'L'}${xPos(i).toFixed(1)},${yPos(d.systolic).toFixed(1)}`)
    .join(' ');
  const dbpPath = data
    .map((d, i) => `${i === 0 ? 'M' : 'L'}${xPos(i).toFixed(1)},${yPos(d.diastolic).toFixed(1)}`)
    .join(' ');

  const yStep = Math.ceil(range / 4 / 10) * 10 || 10;
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
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
        <h3 style={{ margin: 0, color: c.txt1, fontSize: '16px', fontWeight: 700, letterSpacing: '-0.01em' }}>
          BP Graph
        </h3>
        <div style={{ display: 'flex', gap: '14px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: c.txt3 }}>
            <span style={{ display: 'inline-block', width: '14px', height: '2px', backgroundColor: '#dc2626' }} />
            SBP
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: c.txt3 }}>
            <span style={{ display: 'inline-block', width: '14px', height: '2px', backgroundColor: c.accent }} />
            DBP
          </span>
        </div>
      </div>
      <p style={{ margin: '0 0 12px', color: c.txt3, fontSize: '11px' }}>Last 30 days</p>

      {data.length < 2 ? (
        <p style={{ color: c.txt3, textAlign: 'center', padding: '24px 0', fontSize: '13px' }}>
          No data available.
        </p>
      ) : (
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          <g transform={`translate(${pad.left},${pad.top})`}>
            {/* Y grid lines */}
            {yTicks.map(v => (
              <line key={v} x1={0} y1={yPos(v)} x2={cw} y2={yPos(v)} stroke={c.divider} strokeWidth={1} />
            ))}

            {/* Lines */}
            <path d={dbpPath} fill="none" stroke={c.accent} strokeWidth={1.5} strokeLinejoin="round" />
            <path d={sbpPath} fill="none" stroke="#dc2626" strokeWidth={1.5} strokeLinejoin="round" />

            {/* Dots */}
            {data.map((d, i) => (
              <circle key={`dbp-${i}`} cx={xPos(i)} cy={yPos(d.diastolic)} r={i === last ? 4 : 2} fill={c.accent} />
            ))}
            {data.map((d, i) => (
              <circle key={`sbp-${i}`} cx={xPos(i)} cy={yPos(d.systolic)} r={i === last ? 4 : 2} fill="#dc2626" />
            ))}

            {/* Most recent value labels */}
            <text x={xPos(last) + 7} y={yPos(data[last].systolic)} fontSize={10} fill="#dc2626" dominantBaseline="middle">
              {data[last].systolic}
            </text>
            <text x={xPos(last) + 7} y={yPos(data[last].diastolic)} fontSize={10} fill={c.accent} dominantBaseline="middle">
              {data[last].diastolic}
            </text>

            {/* Y-axis labels */}
            {yTicks.map(v => (
              <text key={v} x={-6} y={yPos(v)} textAnchor="end" fontSize={10} fill={c.txt3} dominantBaseline="middle">
                {v}
              </text>
            ))}

            {/* Y-axis unit */}
            <text transform={`translate(-32, ${ch / 2}) rotate(-90)`} textAnchor="middle" fontSize={9} fill={c.txt3}>
              mmHg
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

export default BPGraphCard;
