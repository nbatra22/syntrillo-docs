import React, { useState } from 'react';
import { c } from '../theme';

// ── Configurable score ranges ────────────────────────────────────
// Adjust these when real data ranges are confirmed from the backend
const RISK_SCORE_MAX     = 20;   // lower is better
const PRIORITY_SCORE_MAX = 100;  // higher is worse
// ─────────────────────────────────────────────────────────────────

interface Props {
  riskScore: number;
  priorityScore: number;
  onClick: () => void;
}

// severity: 0 = best, 1 = worst
const severityColor = (severity: number) => {
  if (severity < 0.30) return '#16a34a';  // green
  if (severity < 0.60) return '#d97706';  // amber
  if (severity < 0.80) return '#ea580c';  // orange
  return '#dc2626';                        // red
};

const severityLabel = (severity: number) => {
  if (severity < 0.30) return 'Low';
  if (severity < 0.60) return 'Moderate';
  if (severity < 0.80) return 'High';
  return 'Critical';
};

// ── SVG Gauge ────────────────────────────────────────────────────
interface GaugeProps {
  value: number;
  max: number;
  higherIsBad: boolean;
}

const Gauge: React.FC<GaugeProps> = ({ value, max, higherIsBad }) => {
  const pct      = Math.min(Math.max(value / max, 0), 1);
  const severity = higherIsBad ? pct : 1 - pct;
  const color    = severityColor(severity);

  const cx = 60, cy = 58, r = 42;
  const circumference = 2 * Math.PI * r;         // ≈ 263.9
  const arcLength     = 0.75 * circumference;     // 270° arc ≈ 197.9
  const gapLength     = circumference - arcLength;
  // Fill tracks severity so green (low severity) = small bar, red (high) = full arc
  const filled        = severity * arcLength;

  return (
    <svg viewBox="0 0 120 105" style={{ width: '100%', maxWidth: '150px' }}>
      {/* Background track */}
      <circle
        cx={cx} cy={cy} r={r}
        fill="none"
        stroke="rgba(15, 37, 80, 0.08)"
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={`${arcLength} ${gapLength}`}
        transform={`rotate(135, ${cx}, ${cy})`}
      />
      {/* Filled arc */}
      <circle
        cx={cx} cy={cy} r={r}
        fill="none"
        stroke={color}
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={`${filled} ${circumference - filled}`}
        transform={`rotate(135, ${cx}, ${cy})`}
        style={{ transition: 'stroke-dasharray 0.6s ease, stroke 0.4s ease' }}
      />
      {/* Score value */}
      <text
        x={cx} y={cy + 8}
        textAnchor="middle"
        fontSize="20"
        fontWeight="800"
        fill={color}
      >
        {value}
      </text>
    </svg>
  );
};

// ── Individual score card ─────────────────────────────────────────
interface ScoreCardProps {
  label: string;
  value: number;
  max: number;
  higherIsBad: boolean;
  onClick: () => void;
}

const ScoreCard: React.FC<ScoreCardProps> = ({ label, value, max, higherIsBad, onClick }) => {
  const [hovered, setHovered] = useState(false);

  const pct      = Math.min(Math.max(value / max, 0), 1);
  const severity = higherIsBad ? pct : 1 - pct;
  const color    = severityColor(severity);
  const badge    = severityLabel(severity);

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        backgroundColor: hovered ? c.bgCardHov : c.bgCard,
        border: `1px solid ${hovered ? c.borderHov : c.border}`,
        borderRadius: c.r,
        padding: '16px 12px 14px',
        boxShadow: hovered ? c.shadowLg : c.shadow,
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '6px',
      }}
    >
      {/* Card label */}
      <p style={{
        margin: 0,
        color: c.txt1,
        fontSize: '12px',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
        textAlign: 'center',
      }}>
        {label}
      </p>

      {/* Gauge graphic */}
      <Gauge value={value} max={max} higherIsBad={higherIsBad} />

      {/* Severity badge */}
      <span style={{
        padding: '2px 10px',
        borderRadius: c.rXs,
        backgroundColor: `${color}18`,
        color: color,
        fontSize: '11px',
        fontWeight: 700,
        border: `1px solid ${color}40`,
      }}>
        {badge}
      </span>

      {/* View details hint */}
      <span style={{
        color: c.accent,
        fontSize: '11px',
        fontWeight: 500,
        opacity: hovered ? 1 : 0.35,
        transition: 'opacity 0.2s',
        marginTop: '2px',
      }}>
        View Details →
      </span>
    </div>
  );
};

// ── Exported composite component ──────────────────────────────────
const RiskScoreCards: React.FC<Props> = ({ riskScore, priorityScore, onClick }) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
      <ScoreCard
        label="Risk Score"
        value={riskScore}
        max={RISK_SCORE_MAX}
        higherIsBad={true}
        onClick={onClick}
      />
      <ScoreCard
        label="Priority Score"
        value={priorityScore}
        max={PRIORITY_SCORE_MAX}
        higherIsBad={true}
        onClick={onClick}
      />
    </div>
  );
};

export default RiskScoreCards;
