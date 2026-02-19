import React, { useState } from 'react';
import { c } from '../theme';
import type { BloodPressureSummary } from '../data/staticData';

interface Props {
  summary: BloodPressureSummary;
  onClick: () => void;
}

const BloodPressureCard: React.FC<Props> = ({ summary, onClick }) => {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        backgroundColor: hovered ? c.bgCardHov : c.bgCard,
        border: `1px solid ${hovered ? c.borderHov : c.border}`,
        borderRadius: c.r,
        padding: '20px 24px',
        boxShadow: hovered ? c.shadowLg : c.shadow,
        cursor: 'pointer',
        transition: 'all 0.2s ease',
      }}
    >
      {/* Card header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h3 style={{ margin: 0, color: c.txt1, fontSize: '16px', fontWeight: 700, letterSpacing: '-0.01em' }}>
          Blood Pressure
        </h3>
        <span style={{
          color: c.accent, fontSize: '12px', fontWeight: 500,
          opacity: hovered ? 1 : 0.5, transition: 'opacity 0.2s',
        }}>
          View Details →
        </span>
      </div>

      {/* Status badge */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px' }}>
        <div style={{
          backgroundColor: c.redBg,
          border: `1px solid ${c.redBd}`,
          borderRadius: c.rXs,
          padding: '4px 10px',
          color: c.red,
          fontSize: '12px',
          fontWeight: 600,
          letterSpacing: '0.01em',
        }}>
          {summary.status}
        </div>
      </div>

      {/* Target vs Actual table */}
      <div style={{
        border: `1px solid ${c.divider}`,
        borderRadius: c.rSm,
        overflow: 'hidden',
        fontSize: '13px',
      }}>
        {/* Column headers */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
          <div style={{
            padding: '8px 14px',
            backgroundColor: 'rgba(91, 158, 249, 0.07)',
            color: c.txt3,
            fontWeight: 700,
            fontSize: '11px',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            borderBottom: `1px solid ${c.divider}`,
            textDecoration: 'underline',
          }}>
            Target
          </div>
          <div style={{
            padding: '8px 14px',
            backgroundColor: 'rgba(91, 158, 249, 0.07)',
            color: c.txt3,
            fontWeight: 700,
            fontSize: '11px',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            borderBottom: `1px solid ${c.divider}`,
            borderLeft: `1px solid ${c.divider}`,
            textDecoration: 'underline',
          }}>
            Actual
          </div>
        </div>

        {/* Data rows */}
        {summary.targets.map((t, i) => {
          const isLast = i === summary.targets.length - 1;
          return (
            <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
              <div style={{
                padding: '8px 14px',
                color: c.txt2,
                borderBottom: isLast ? undefined : `1px solid ${c.divider}`,
                lineHeight: 1.4,
              }}>
                {t.label}: {t.target}
              </div>
              <div style={{
                padding: '8px 14px',
                color: t.met ? c.green : c.red,
                borderLeft: `1px solid ${c.divider}`,
                borderBottom: isLast ? undefined : `1px solid ${c.divider}`,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontWeight: 500,
                lineHeight: 1.4,
              }}>
                <span style={{ fontSize: '14px', flexShrink: 0 }}>{t.met ? '✓' : '✗'}</span>
                {t.actual}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default BloodPressureCard;
