import React from 'react';
import { c } from '../theme';
import type { LabValue } from '../data/staticData';

interface Props {
  values: LabValue[];
}

const LabValuesCard: React.FC<Props> = ({ values }) => {
  return (
    <div style={{
      backgroundColor: c.bgCard,
      border: `1px solid ${c.border}`,
      borderRadius: c.r,
      padding: '20px 24px',
      boxShadow: c.shadow,
    }}>
      <h3 style={{ margin: '0 0 16px', color: c.txt1, fontSize: '16px', fontWeight: 700, letterSpacing: '-0.01em' }}>
        Lab Values
      </h3>

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
  );
};

export default LabValuesCard;
