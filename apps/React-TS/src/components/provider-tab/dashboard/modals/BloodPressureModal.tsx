import React from 'react';
import { c } from '../theme';
import type { BloodPressureDetail, BPCellStatus } from '../data/staticData';

interface Props {
  detail: BloodPressureDetail;
  onClose: () => void;
}

const cellStyle = (status?: BPCellStatus): React.CSSProperties => {
  const base: React.CSSProperties = {
    padding: '10px 16px',
    textAlign: 'center',
    fontSize: '14px',
    fontWeight: 500,
  };
  if (status === 'good') return { ...base, backgroundColor: 'rgba(22, 163, 74, 0.14)',  color: c.green, fontWeight: 700 };
  if (status === 'bad')  return { ...base, backgroundColor: 'rgba(220, 38, 38, 0.12)',   color: c.red,   fontWeight: 700 };
  if (status === 'warn') return { ...base, backgroundColor: 'rgba(180, 83, 9, 0.12)',    color: c.amber, fontWeight: 700 };
  return { ...base, color: c.txt2 };
};

const BloodPressureModal: React.FC<Props> = ({ detail, onClose }) => {
  const { periods, rows, source } = detail;

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
          maxWidth: '780px',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* ── Fixed header (never scrolls) ── */}
        <div style={{
          padding: '24px 28px 18px',
          borderBottom: `1px solid ${c.divider}`,
          flexShrink: 0,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}>
          <div>
            <span style={{ color: c.accent, fontSize: '13px', cursor: 'pointer' }}>
              ↓ Download
            </span>
            <h2 style={{ margin: '6px 0 4px', color: c.txt1, fontSize: '22px', fontWeight: 700, letterSpacing: '-0.01em' }}>
              Blood Pressure
            </h2>
            <p style={{ margin: 0, color: c.txt3, fontSize: '13px' }}>{source}</p>
          </div>
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
              flexShrink: 0,
            }}
          >
            ×
          </button>
        </div>

        {/* ── Scrollable table area ── */}
        <div style={{ overflowY: 'auto', overflowX: 'auto', flex: 1 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '500px' }}>

            {/* Sticky column headers */}
            <thead style={{ position: 'sticky', top: 0, zIndex: 2 }}>
              <tr>
                <th style={{
                  padding: '12px 16px', textAlign: 'left',
                  color: c.txt3, fontWeight: 600, fontSize: '13px', width: '32%',
                  backgroundColor: c.bgCard,
                  boxShadow: `0 1px 0 ${c.divider}`,
                }}>
                  Title
                </th>
                {(['baseline', 'prior', 'latest'] as const).map(period => (
                  <th key={period} style={{
                    padding: '12px 16px', textAlign: 'center',
                    color: c.txt2, fontWeight: 600, fontSize: '13px',
                    backgroundColor: c.bgCard,
                    boxShadow: `0 1px 0 ${c.divider}, -1px 0 0 ${c.divider}`,
                  }}>
                    <span style={{ textTransform: 'capitalize' }}>{period}</span>
                    <br />
                    <span style={{ color: c.txt3, fontWeight: 400, fontSize: '11px' }}>
                      {periods[period].dateRange}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {rows.map((row, i) => (
                <tr key={i} style={{ borderBottom: `1px solid ${c.divider}` }}>
                  <td style={{ padding: '10px 16px', color: c.txt2, fontSize: '14px', fontWeight: 500 }}>
                    {row.title}
                  </td>
                  <td style={{ ...cellStyle(row.baseline.status), borderLeft: `1px solid ${c.divider}` }}>
                    {row.baseline.value}
                  </td>
                  <td style={{ ...cellStyle(row.prior.status), borderLeft: `1px solid ${c.divider}` }}>
                    {row.prior.value}
                  </td>
                  <td style={{ ...cellStyle(row.latest.status), borderLeft: `1px solid ${c.divider}` }}>
                    {row.latest.value}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default BloodPressureModal;
