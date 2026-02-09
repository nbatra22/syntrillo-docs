import React, { useState, useEffect } from 'react';
import { patientSidebarApi } from '../../utils/api';
import type { StrokeRiskData, BloodPressureData } from '../../utils/api';

interface PatientDashboardProps {
  temporaryLookupCode: string;
}

const PatientDashboard: React.FC<PatientDashboardProps> = ({ temporaryLookupCode }) => {
  const [strokeRiskData, setStrokeRiskData] = useState<StrokeRiskData | null>(null);
  const [bpData, setBpData] = useState<BloodPressureData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (temporaryLookupCode) {
      fetchData();
    }
  }, [temporaryLookupCode]);

  const fetchData = async () => {
    setLoading(true);
    setError('');

    try {
      const [strokeData, bloodPressureData] = await Promise.all([
        patientSidebarApi.getStrokeRiskFactors(temporaryLookupCode),
        patientSidebarApi.getBloodPressure(temporaryLookupCode),
      ]);

      setStrokeRiskData(strokeData);
      setBpData(bloodPressureData);
    } catch (err) {
      console.error('Error fetching patient data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch patient data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-12">
        <div className="w-12 h-12 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin"></div>
        <p className="text-gray-600">Loading patient data...</p>
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

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Syntrillo Dashboard</h1>

      {/* Stroke Risk Factor Analysis Section */}
      <section className="border border-gray-300 rounded">
        <div className="bg-gray-100 p-4 border-b border-gray-300">
          <h2 className="text-xl font-semibold text-gray-800">Stroke Risk Factor Analysis</h2>
        </div>
        <div className="p-4">
          {strokeRiskData?.data ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-blue-50 rounded">
                  <p className="text-sm text-gray-600">Risk Score</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {strokeRiskData.data.risk_score?.toFixed(1) ?? 'N/A'}
                  </p>
                </div>
                <div className="p-3 bg-purple-50 rounded">
                  <p className="text-sm text-gray-600">Priority Score</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {strokeRiskData.data.priority_score?.toFixed(1) ?? 'N/A'}
                  </p>
                </div>
              </div>

              {strokeRiskData.data.metrics && (
                <div className="mt-4">
                  <h3 className="font-semibold text-gray-700 mb-2">Key Metrics</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {Object.entries(strokeRiskData.data.metrics).map(([key, value]) => (
                      <div key={key} className="flex justify-between p-2 bg-gray-50 rounded">
                        <span className="text-gray-600">{key.replace(/_/g, ' ')}:</span>
                        <span className="font-medium">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-600">No stroke risk data available.</p>
          )}
        </div>
      </section>

      {/* Blood Pressure Analysis Section */}
      <section className="border border-gray-300 rounded">
        <div className="bg-gray-100 p-4 border-b border-gray-300">
          <h2 className="text-xl font-semibold text-gray-800">Blood Pressure Analysis</h2>
          <p className="text-sm text-gray-600 mt-1">
            The data below is calculated using your most recent two weeks of measurements.
          </p>
        </div>
        <div className="p-4">
          {bpData?.data ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="p-3 bg-red-50 rounded">
                  <p className="text-sm text-gray-600">Average SBP</p>
                  <p className="text-2xl font-bold text-red-600">
                    {bpData.data.avg_systolic?.toFixed(0) ?? 'N/A'} <span className="text-sm">mmHg</span>
                  </p>
                </div>
                <div className="p-3 bg-blue-50 rounded">
                  <p className="text-sm text-gray-600">Average DBP</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {bpData.data.avg_diastolic?.toFixed(0) ?? 'N/A'} <span className="text-sm">mmHg</span>
                  </p>
                </div>
                <div className="p-3 bg-green-50 rounded">
                  <p className="text-sm text-gray-600">Measurements</p>
                  <p className="text-2xl font-bold text-green-600">
                    {bpData.data.num_measurements ?? 'N/A'}
                  </p>
                </div>
              </div>

              <ul className="text-sm text-gray-600 space-y-2 bg-gray-50 p-4 rounded">
                <li>
                  Blood pressure measurements are captured as two numbers, both measured in millimeters of mercury (mmHg).
                </li>
                <li>
                  <span className="font-semibold">Systolic Blood Pressure (SBP)</span>, the top number, measures the pressure in your arteries when your heart beats and pumps blood.
                </li>
                <li>
                  <span className="font-semibold">Diastolic Blood Pressure (DBP)</span>, the bottom number, measures the pressure in your arteries when your heart rests between beats.
                </li>
              </ul>
            </div>
          ) : (
            <p className="text-gray-600">No blood pressure data available.</p>
          )}
        </div>
      </section>
    </div>
  );
};

export default PatientDashboard;
