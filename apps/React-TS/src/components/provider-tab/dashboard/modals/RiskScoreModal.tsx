import React from 'react';
import { c } from '../theme';

interface Props {
  riskScore: number;
  priorityScore: number;
  onClose: () => void;
}

const RiskScoreModal: React.FC<Props> = ({ riskScore, priorityScore, onClose }) => {
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        backgroundColor: c.bgOverlay,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '24px',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          backgroundColor: c.bgCard,
          border: `1px solid ${c.border}`,
          borderRadius: c.r,
          boxShadow: c.shadowLg,
          width: '100%',
          maxWidth: '500px',
          padding: '32px',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
          <h2 style={{ margin: 0, color: c.txt1, fontSize: '20px', fontWeight: 700, letterSpacing: '-0.01em' }}>
            Risk Score Details
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: `1px solid ${c.border}`,
              borderRadius: c.rSm,
              color: c.txt2,
              cursor: 'pointer',
              width: '32px', height: '32px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '20px', lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        {/* Score cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '24px' }}>
          <div style={{
            backgroundColor: c.bgMain,
            border: `1px solid ${c.border}`,
            borderRadius: c.rSm,
            padding: '20px',
            textAlign: 'center',
          }}>
            <p style={{ margin: '0 0 10px', color: c.txt3, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.07em', fontWeight: 600 }}>
              Risk Score
            </p>
            <p style={{ margin: 0, color: c.accent, fontSize: '40px', fontWeight: 800, lineHeight: 1, letterSpacing: '-0.02em' }}>
              {riskScore}
            </p>
          </div>
          <div style={{
            backgroundColor: c.bgMain,
            border: `1px solid ${c.border}`,
            borderRadius: c.rSm,
            padding: '20px',
            textAlign: 'center',
          }}>
            <p style={{ margin: '0 0 10px', color: c.txt3, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.07em', fontWeight: 600 }}>
              Priority Score
            </p>
            <p style={{ margin: 0, color: c.amber, fontSize: '40px', fontWeight: 800, lineHeight: 1, letterSpacing: '-0.02em' }}>
              {priorityScore}
            </p>
          </div>
        </div>

        {/* Placeholder breakdown */}
        <div style={{
          padding: '16px 20px',
          backgroundColor: c.bgMain,
          border: `1px solid ${c.divider}`,
          borderRadius: c.rSm,
          color: c.txt3,
          fontSize: '13px',
          textAlign: 'center',
          lineHeight: 1.6,
        }}>
          Detailed risk factor breakdown will appear here once connected to the backend.
        </div>
      </div>
    </div>
  );
};

export default RiskScoreModal;
