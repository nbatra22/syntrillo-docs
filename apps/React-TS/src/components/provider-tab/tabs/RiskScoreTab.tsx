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
      setError(err instanceof Error ? err.message : 'Failed to fetch risk score');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-8">
        <div className="w-8 h-8 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin"></div>
        <p className="text-gray-600">Loading risk score data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-100 text-red-700 rounded">
        Error: {error}
      </div>
    );
  }

  if (!riskData?.data) {
    return (
      <div className="text-center py-8 text-gray-600">
        No risk score data available for this patient.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Stroke Risk Score Analysis</h2>

      <div className="grid grid-cols-2 gap-6">
        <div className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Risk Score</h3>
          <p className="text-5xl font-bold text-blue-600">
            {riskData.data.risk_score?.toFixed(1) ?? 'N/A'}
          </p>
        </div>

        <div className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Priority Score</h3>
          <p className="text-5xl font-bold text-purple-600">
            {riskData.data.priority_score?.toFixed(1) ?? 'N/A'}
          </p>
        </div>
      </div>

      {riskData.data.metrics && (
        <div className="mt-6">
          <h3 className="text-xl font-semibold text-gray-700 mb-4">Risk Factors</h3>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(riskData.data.metrics).map(([key, value]) => (
              <div key={key} className="flex justify-between p-3 bg-gray-50 rounded border border-gray-200">
                <span className="text-gray-700 font-medium capitalize">
                  {key.replace(/_/g, ' ')}:
                </span>
                <span className="font-semibold text-gray-900">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {riskData.data.independent_risk_variable_scores && (
        <div className="mt-6">
          <h3 className="text-xl font-semibold text-gray-700 mb-4">Independent Risk Variables</h3>
          <div className="grid grid-cols-3 gap-3">
            {Object.entries(riskData.data.independent_risk_variable_scores).map(([key, value]) => (
              <div key={key} className="p-3 bg-blue-50 rounded border border-blue-200">
                <p className="text-sm text-gray-600 mb-1">{key.replace(/_/g, ' ')}</p>
                <p className="text-xl font-bold text-blue-600">{String(value)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskScoreTab;
