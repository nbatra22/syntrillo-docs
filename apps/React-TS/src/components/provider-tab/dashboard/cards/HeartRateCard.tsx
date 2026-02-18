import React from 'react';
import { c } from '../theme';

interface HeartRate {
  current: number;
  currentDate: string;
  avgResting: number;
  baselineDateRange: string;
}

interface Props {
  heartRate: HeartRate;
}

const HeartRateCard: React.FC<Props> = ({ heartRate }) => {
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

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
        {/* Current heart rate */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          padding: '8px 0',
          borderBottom: `1px solid ${c.divider}`,
        }}>
          <div>
            <p style={{ margin: 0, color: c.txt2, fontSize: '13px' }}>Heart Rate</p>
            <p style={{ margin: '2px 0 0', color: c.txt3, fontSize: '11px' }}>
              As of {heartRate.currentDate}
            </p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ color: c.txt1, fontSize: '22px', fontWeight: 800, lineHeight: 1, letterSpacing: '-0.01em' }}>
              {heartRate.current.toFixed(2)}
            </span>
            <span style={{ color: c.txt3, fontSize: '11px', marginLeft: '4px' }}>BPM</span>
          </div>
        </div>

        {/* Average resting heart rate */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          padding: '10px 0 0',
        }}>
          <div>
            <p style={{ margin: 0, color: c.txt2, fontSize: '13px' }}>Avg. Resting Heart Rate</p>
            <p style={{ margin: '2px 0 0', color: c.txt3, fontSize: '11px' }}>
              Baseline: {heartRate.baselineDateRange}
            </p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ color: c.txt1, fontSize: '22px', fontWeight: 800, lineHeight: 1, letterSpacing: '-0.01em' }}>
              {heartRate.avgResting.toFixed(2)}
            </span>
            <span style={{ color: c.txt3, fontSize: '11px', marginLeft: '4px' }}>BPM</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HeartRateCard;
