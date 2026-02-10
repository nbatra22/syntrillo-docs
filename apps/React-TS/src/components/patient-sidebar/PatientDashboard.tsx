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
    <div className="space-y-8 p-6">
      <h1 className="text-3xl font-bold text-gray-800 mb-2">Syntrillo Dashboard</h1>

      {/* Stroke Risk Factor Analysis Section */}
      <section className="bg-white rounded-2xl shadow-sm overflow-hidden">
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-5">
          <h2 className="text-2xl font-semibold text-gray-800">Stroke Risk Factor Analysis</h2>
        </div>
        <div className="p-6">
          {strokeRiskData?.data ? (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl shadow-sm">
                  <p className="text-sm font-medium text-gray-600 mb-2">Risk Score</p>
                  <p className="text-4xl font-bold text-blue-600">
                    {strokeRiskData.data.risk_score?.toFixed(1) ?? 'N/A'}
                  </p>
                </div>
                <div className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl shadow-sm">
                  <p className="text-sm font-medium text-gray-600 mb-2">Priority Score</p>
                  <p className="text-4xl font-bold text-purple-600">
                    {strokeRiskData.data.priority_score?.toFixed(1) ?? 'N/A'}
                  </p>
                </div>
              </div>

              {strokeRiskData.data.metrics && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-gray-700 mb-4">Key Metrics</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {Object.entries(strokeRiskData.data.metrics).map(([key, value]) => (
                      <div key={key} className="flex justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                        <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}:</span>
                        <span className="font-semibold text-gray-900">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-600 py-4">No stroke risk data available.</p>
          )}
        </div>
      </section>

      {/* Blood Pressure Analysis Section */}
      <section className="bg-white rounded-2xl shadow-sm overflow-hidden">
        <div className="bg-gradient-to-r from-red-50 to-pink-50 px-6 py-5">
          <h2 className="text-2xl font-semibold text-gray-800">Blood Pressure Analysis</h2>
          <p className="text-sm text-gray-600 mt-2 leading-relaxed">
            The data below is calculated using your most recent two weeks of measurements.
          </p>
        </div>
        <div className="p-6">
          {bpData?.data ? (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-6">
                <div className="p-6 bg-gradient-to-br from-red-50 to-red-100 rounded-xl shadow-sm">
                  <p className="text-sm font-medium text-gray-600 mb-2">Average SBP</p>
                  <p className="text-4xl font-bold text-red-600">
                    {bpData.data.avg_systolic?.toFixed(0) ?? 'N/A'} <span className="text-base font-normal">mmHg</span>
                  </p>
                </div>
                <div className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl shadow-sm">
                  <p className="text-sm font-medium text-gray-600 mb-2">Average DBP</p>
                  <p className="text-4xl font-bold text-blue-600">
                    {bpData.data.avg_diastolic?.toFixed(0) ?? 'N/A'} <span className="text-base font-normal">mmHg</span>
                  </p>
                </div>
                <div className="p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-xl shadow-sm">
                  <p className="text-sm font-medium text-gray-600 mb-2">Measurements</p>
                  <p className="text-4xl font-bold text-green-600">
                    {bpData.data.num_measurements ?? 'N/A'}
                  </p>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-100 rounded-xl p-6">
                <ul className="text-sm text-gray-700 space-y-3 leading-relaxed">
                  <li className="flex items-start">
                    <span className="text-blue-500 mr-2">•</span>
                    <span>Blood pressure measurements are captured as two numbers, both measured in millimeters of mercury (mmHg).</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-500 mr-2">•</span>
                    <span><span className="font-semibold text-gray-800">Systolic Blood Pressure (SBP)</span>, the top number, measures the pressure in your arteries when your heart beats and pumps blood.</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-500 mr-2">•</span>
                    <span><span className="font-semibold text-gray-800">Diastolic Blood Pressure (DBP)</span>, the bottom number, measures the pressure in your arteries when your heart rests between beats.</span>
                  </li>
                </ul>
              </div>
            </div>
          ) : (
            <p className="text-gray-600 py-4">No blood pressure data available.</p>
          )}
        </div>
      </section>
    </div>
  );
};

export default PatientDashboard;
