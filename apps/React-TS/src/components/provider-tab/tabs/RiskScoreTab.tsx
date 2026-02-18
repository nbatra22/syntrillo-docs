import React, { useState, useEffect } from 'react';
import { providerTabApi } from '../../../utils/api';
import type { StrokeRiskData } from '../../../utils/api';

interface RiskScoreTabProps {
  temporaryLookupCode: string;
}

const RiskScoreTab: React.FC<RiskScoreTabProps> = ({ temporaryLookupCode }) => {
  const [riskData, setRiskData] = useState<StrokeRiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (temporaryLookupCode) {
      fetchRiskScore();
    }
  }, [temporaryLookupCode]);

  const fetchRiskScore = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await providerTabApi.getStrokeRiskFactors(temporaryLookupCode);
      setRiskData(data);
    } catch (err) {
      console.error('Error fetching risk score:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch risk score data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1rem', padding: '3rem' }}>
        <div className="spinner" style={{
          width: '2rem',
          height: '2rem',
          border: '4px solid white',
          borderTopColor: '#3b82f6',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
        <p style={{ color: '#6b7280', fontSize: '1rem' }}>Loading risk score data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '1.25rem', backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', borderRadius: '0.5rem' }}>
        Error: {error}
      </div>
    );
  }

  const riskScore = riskData?.data?.risk_score ?? 'N/A';
  const priorityScore = riskData?.data?.priority_score ?? 'N/A';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header with Scores */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <h1 style={{ fontWeight: 'bold', fontSize: 'large', margin: 0 }}>
            Stroke Risk Score
          </h1>
          <button
            onClick={fetchRiskScore}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '2rem',
              height: '2rem',
              padding: 0,
              borderRadius: '50%',
              border: 'none',
              color: '#16284a',
              backgroundColor: '#e5e7eb',
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
            title="Refresh Risk Score Data"
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#d1d5db'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#e5e7eb'}
          >
            <i className="fa-solid fa-arrows-rotate"></i>
          </button>
        </div>

        {/* Scores Display */}
        <div style={{ display: 'flex', gap: '2rem' }}>
          <div style={{
            backgroundColor: '#e5e7eb',
            borderRadius: '0.375rem',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.5rem',
            minWidth: '150px'
          }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 500, color: '#6b7280', margin: 0 }}>
              Risk Score
            </h3>
            <h2 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#16284a', margin: 0 }}>
              {riskScore}
            </h2>
          </div>
          <div style={{
            backgroundColor: '#e5e7eb',
            borderRadius: '0.375rem',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.5rem',
            minWidth: '150px'
          }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 500, color: '#6b7280', margin: 0 }}>
              Priority Score
            </h3>
            <h2 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#16284a', margin: 0 }}>
              {priorityScore}
            </h2>
          </div>
        </div>
      </div>

      {/* Clinical Assessment */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', backgroundColor: '#eff6ff', padding: '1.5rem', borderRadius: '0.75rem', border: '1px solid #bfdbfe' }}>
        <p style={{ fontSize: '1rem', color: '#1e40af', margin: 0 }}>
          Our clinicians have reviewed your health information and feel that you are at an overall low risk of stroke.
          Given available data, they estimate your one-year risk of stroke and heart attack is most likely around 1%
          although it may be as high as 2% per year depending on the interaction of your unique risk factors.
        </p>
        <p style={{ fontSize: '1rem', color: '#1e40af', margin: 0 }}>
          The following risk factors or conditions are contributing the most to your current risk of stroke.
          Addressing these risk factors can help lower your overall risk of stroke.
        </p>
      </div>

      {/* Risk Factors Table */}
      <div style={{ overflow: 'hidden', borderRadius: '0.75rem', border: '1px solid #d1d5db', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#f3f4f6' }}>
              <th style={{ padding: '1rem 1.5rem', textAlign: 'left', fontWeight: 600, color: '#374151', width: '33%' }}>Risk Factor</th>
              <th style={{ padding: '1rem 1.5rem', textAlign: 'left', fontWeight: 600, color: '#374151' }}>Comments from your doctor</th>
            </tr>
          </thead>
          <tbody style={{ backgroundColor: 'white' }}>
            <tr style={{ borderTop: '1px solid #e5e7eb' }}>
              <td style={{ padding: '1rem 1.5rem', fontWeight: 500, color: '#111827' }}>Hypertension</td>
              <td style={{ padding: '1rem 1.5rem', color: '#374151', lineHeight: '1.625' }}>
                Our clinicians estimate that the risk factor most contributing to your risk of stroke and heart disease
                is your average systolic blood pressure which was 133. According to this estimate, your risk of stroke
                is increased by 35% compared to an optimal value (average systolic blood pressure &lt; 125). Your average
                systolic blood pressure also increases your risk of dementia and kidney disease.
              </td>
            </tr>
            <tr style={{ borderTop: '1px solid #e5e7eb' }}>
              <td style={{ padding: '1rem 1.5rem', fontWeight: 500, color: '#111827' }}>Hyperlipidemia (LDL and Triglycerides)</td>
              <td style={{ padding: '1rem 1.5rem', color: '#374151', lineHeight: '1.625' }}>
                Our clinicians estimate the second most important risk factor contributing to your risk of stroke and
                heart disease is your hyperlipidemia. According to this estimate, your risk of stroke is increased by 25%
                compared to the optimal levels. A LDL level &gt; 100 is considered elevated although the goal LDL level
                in patients with known atherosclerosis is less than 70. A triglyceride level greater than 150 is considered elevated.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RiskScoreTab;
