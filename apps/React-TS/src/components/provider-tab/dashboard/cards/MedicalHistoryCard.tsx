import React from 'react';
import { c } from '../theme';
import type { MedicalHistoryItem, BadgeType } from '../data/staticData';

interface Props {
  items: MedicalHistoryItem[];
}

const badge = (type: BadgeType): React.CSSProperties => {
  if (type === 'optimized') return {
    backgroundColor: c.greenBg, color: c.green, border: `1px solid ${c.greenBd}`,
    padding: '2px 8px', borderRadius: c.rXs, fontSize: '11px', fontWeight: 700,
    whiteSpace: 'nowrap', flexShrink: 0,
  };
  if (type === 'non-optimized') return {
    backgroundColor: c.redBg, color: c.red, border: `1px solid ${c.redBd}`,
    padding: '2px 8px', borderRadius: c.rXs, fontSize: '11px', fontWeight: 700,
    whiteSpace: 'nowrap', flexShrink: 0,
  };
  // partially-optimized
  return {
    backgroundColor: c.amberBg, color: c.amber, border: `1px solid ${c.amberBd}`,
    padding: '2px 8px', borderRadius: c.rXs, fontSize: '11px', fontWeight: 700,
    whiteSpace: 'nowrap', flexShrink: 0,
  };
};

const badgeLabel: Record<BadgeType, string> = {
  'optimized':           'Optimized',
  'non-optimized':       'Non Optimized',
  'partially-optimized': 'Partially Optimized',
};

const MedicalHistoryCard: React.FC<Props> = ({ items }) => {
  return (
    <div style={{
      backgroundColor: c.bgCard,
      border: `1px solid ${c.border}`,
      borderRadius: c.r,
      padding: '20px 24px',
      boxShadow: c.shadow,
    }}>
      <h3 style={{ margin: '0 0 16px', color: c.txt1, fontSize: '16px', fontWeight: 700, letterSpacing: '-0.01em' }}>
        Medical History
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
        {items.map((item, i) => {
          const isLast = i === items.length - 1;
          return (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '10px',
                padding: '9px 0',
                borderBottom: isLast ? undefined : `1px solid ${c.divider}`,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                <span style={{ color: c.txt2, fontSize: '13px', flexShrink: 0 }}>{item.label}</span>
                {item.badge && (
                  <span style={badge(item.badge)}>{badgeLabel[item.badge]}</span>
                )}
              </div>
              <span style={{
                color: c.txt1,
                fontSize: '13px',
                fontWeight: 600,
                whiteSpace: 'nowrap',
                flexShrink: 0,
              }}>
                {item.value}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MedicalHistoryCard;
