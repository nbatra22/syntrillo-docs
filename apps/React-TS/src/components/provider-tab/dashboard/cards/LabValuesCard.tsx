import React, { useState } from 'react';
import { c } from '../theme';
import type { LabValue } from '../data/staticData';

interface Props {
  values: LabValue[];
}

const LabValuesCard: React.FC<Props> = ({ values }) => {
  const [open, setOpen] = useState(false);
  const [hovered, setHovered] = useState(false);

  return (
    <>
      <div
        onClick={() => setOpen(true)}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          backgroundColor: hovered ? c.bgCardHov : c.bgCard,
          border: `1px solid ${hovered ? c.borderHov : c.border}`,
          borderRadius: c.r,
          padding: '20px 24px',
          boxShadow: hovered ? c.shadowLg : c.shadow,
          transition: 'all 0.2s ease',
          cursor: 'pointer',
        }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ margin: 0, color: c.txt1, fontSize: '16px', fontWeight: 700, letterSpacing: '-0.01em' }}>
            Lab Values
          </h3>
          <span
            onClick={() => setOpen(true)}
            onMouseEnter={e => (e.currentTarget.style.opacity = '1')}
            onMouseLeave={e => (e.currentTarget.style.opacity = '0.5')}
            style={{
              color: c.accent,
              fontSize: '12px',
              fontWeight: 500,
              opacity: 0.5,
              cursor: 'pointer',
              transition: 'opacity 0.2s',
              userSelect: 'none',
            }}
          >
            Update Values →
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {values.map((v, i) => {
            const isLast = i === values.length - 1;
            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '9px 0',
                  borderBottom: isLast ? undefined : `1px solid ${c.divider}`,
                }}
              >
                <span style={{ color: c.txt2, fontSize: '13px' }}>{v.label}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {v.alert && (
                    <span style={{ color: c.amber, fontSize: '14px' }}>⚠</span>
                  )}
                  <span style={{ color: c.txt1, fontSize: '13px', fontWeight: 600 }}>{v.value}</span>
                  <span style={{ color: c.txt3, fontSize: '11px' }}>{v.unit}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Modal */}
      {open && (
        <div
          onClick={() => setOpen(false)}
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
              maxWidth: '560px',
              padding: '28px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ margin: 0, color: c.txt1, fontSize: '20px', fontWeight: 700 }}>Lab Values</h2>
              <button
                onClick={() => setOpen(false)}
                style={{
                  background: 'transparent', border: `1px solid ${c.border}`,
                  borderRadius: c.rSm, color: c.txt2, cursor: 'pointer',
                  width: '32px', height: '32px', fontSize: '20px', lineHeight: 1,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}
              >×</button>
            </div>
            <p style={{ color: c.txt3, fontSize: '14px', margin: 0 }}>update form here</p>
          </div>
        </div>
      )}
    </>
  );
};

export default LabValuesCard;
