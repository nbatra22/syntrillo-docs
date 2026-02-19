import React from 'react';
import { c } from '../theme';

interface PatientSummary {
  height: string;
  weight: string;
  bmi: number;
  moderateVigorousActivity: string;
  physicalInactivity: string;
}

interface Props {
  summary: PatientSummary;
}


const PatientSummaryCard: React.FC<Props> = ({ summary }) => {
  return (
    <div style={{
      backgroundColor: c.bgCard,
      border: `1px solid ${c.border}`,
      borderRadius: c.r,
      padding: '20px 24px',
      boxShadow: c.shadow,
    }}>
      <h3 style={{ margin: '0 0 16px', color: c.txt1, fontSize: '16px', fontWeight: 700, letterSpacing: '-0.01em' }}>
        Physical Activity
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <span style={{ color: c.txt2, fontSize: '13px', fontWeight: 600 }}>Moderate/Vigorous Activity:</span>
          <div style={{ textAlign: 'right' }}>
            <span style={{ color: c.txt1, fontSize: '14px', fontWeight: 700 }}>{summary.moderateVigorousActivity}</span>
            <span style={{ color: c.txt3, fontSize: '11px', marginLeft: '4px' }}>min/week</span>
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <span style={{ color: c.txt2, fontSize: '13px', fontWeight: 600 }}>Physical Inactivity:</span>
          <div style={{ textAlign: 'right' }}>
            <span style={{ color: c.txt1, fontSize: '14px', fontWeight: 700 }}>{summary.physicalInactivity}</span>
            <span style={{ color: c.txt3, fontSize: '11px', marginLeft: '4px' }}>hrs/day</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientSummaryCard;
