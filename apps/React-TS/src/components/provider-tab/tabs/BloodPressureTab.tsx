import React, { useState, useEffect } from 'react';
import { providerTabApi } from '../../../utils/api';
import type { BloodPressureData } from '../../../utils/api';

interface BloodPressureTabProps {
  temporaryLookupCode: string;
}

const BloodPressureTab: React.FC<BloodPressureTabProps> = ({ temporaryLookupCode }) => {
  const [bpData, setBpData] = useState<BloodPressureData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (temporaryLookupCode) {
      fetchBloodPressure();
    }
  }, [temporaryLookupCode]);

  const fetchBloodPressure = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await providerTabApi.getBloodPressure(temporaryLookupCode);
      setBpData(data);
    } catch (err) {
      console.error('Error fetching blood pressure:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch blood pressure data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-8">
        <div className="w-8 h-8 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin"></div>
        <p className="text-gray-600">Loading blood pressure data...</p>
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

  if (!bpData?.data) {
    return (
      <div className="text-center py-8 text-gray-600">
        No blood pressure data available for this patient.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Blood Pressure Analysis</h2>

      <div className="grid grid-cols-3 gap-6">
        <div className="p-6 bg-gradient-to-br from-red-50 to-red-100 rounded-lg shadow">
          <h3 className="text-sm font-semibold text-gray-600 mb-2">Average Systolic</h3>
          <p className="text-4xl font-bold text-red-600">
            {bpData.data.avg_systolic?.toFixed(0) ?? 'N/A'}
            <span className="text-lg ml-2">mmHg</span>
          </p>
        </div>

        <div className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg shadow">
          <h3 className="text-sm font-semibold text-gray-600 mb-2">Average Diastolic</h3>
          <p className="text-4xl font-bold text-blue-600">
            {bpData.data.avg_diastolic?.toFixed(0) ?? 'N/A'}
            <span className="text-lg ml-2">mmHg</span>
          </p>
        </div>

        <div className="p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-lg shadow">
          <h3 className="text-sm font-semibold text-gray-600 mb-2">Total Measurements</h3>
          <p className="text-4xl font-bold text-green-600">
            {bpData.data.num_measurements ?? 'N/A'}
          </p>
        </div>
      </div>

      {bpData.data.peak_systolic && (
        <div className="grid grid-cols-2 gap-6">
          <div className="p-4 bg-orange-50 rounded border border-orange-200">
            <h3 className="text-sm font-semibold text-gray-600 mb-2">Peak Systolic</h3>
            <p className="text-3xl font-bold text-orange-600">
              {bpData.data.peak_systolic.toFixed(0)} <span className="text-base">mmHg</span>
            </p>
          </div>

          <div className="p-4 bg-teal-50 rounded border border-teal-200">
            <h3 className="text-sm font-semibold text-gray-600 mb-2">Low Systolic</h3>
            <p className="text-3xl font-bold text-teal-600">
              {bpData.data.low_systolic?.toFixed(0) ?? 'N/A'} <span className="text-base">mmHg</span>
            </p>
          </div>
        </div>
      )}

      <div className="mt-6 p-4 bg-gray-50 rounded border border-gray-200">
        <h3 className="font-semibold text-gray-700 mb-3">Understanding Blood Pressure</h3>
        <ul className="text-sm text-gray-600 space-y-2">
          <li>
            <span className="font-semibold">Systolic (top number):</span> Pressure when heart beats
          </li>
          <li>
            <span className="font-semibold">Diastolic (bottom number):</span> Pressure when heart rests
          </li>
          <li>
            <span className="font-semibold">Normal range:</span> Less than 120/80 mmHg
          </li>
          <li>
            <span className="font-semibold">Elevated:</span> 120-129 systolic and less than 80 diastolic
          </li>
          <li>
            <span className="font-semibold">High (Hypertension Stage 1):</span> 130-139 systolic or 80-89 diastolic
          </li>
        </ul>
      </div>
    </div>
  );
};

export default BloodPressureTab;
