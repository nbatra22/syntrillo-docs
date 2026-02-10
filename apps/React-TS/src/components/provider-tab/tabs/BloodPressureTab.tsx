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
      <div className="flex flex-col items-center justify-center gap-4 py-12">
        <div className="w-10 h-10 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin"></div>
        <p className="text-gray-600 text-base">Loading blood pressure data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-5 bg-red-50 border border-red-200 text-red-700 rounded-lg">
        Error: {error}
      </div>
    );
  }

  if (!bpData?.data) {
    return (
      <div className="text-center py-12 text-gray-600 text-base">
        No blood pressure data available for this patient.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h2 className="text-3xl font-bold text-gray-800 mb-2">Blood Pressure Analysis</h2>

      <div className="grid grid-cols-3 gap-8">
        <div className="p-8 bg-gradient-to-br from-red-50 to-red-100 rounded-2xl shadow-sm">
          <h3 className="text-sm font-semibold text-gray-600 mb-3">Average Systolic</h3>
          <p className="text-5xl font-bold text-red-600">
            {bpData.data.avg_systolic?.toFixed(0) ?? 'N/A'}
            <span className="text-xl ml-2 font-normal">mmHg</span>
          </p>
        </div>

        <div className="p-8 bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl shadow-sm">
          <h3 className="text-sm font-semibold text-gray-600 mb-3">Average Diastolic</h3>
          <p className="text-5xl font-bold text-blue-600">
            {bpData.data.avg_diastolic?.toFixed(0) ?? 'N/A'}
            <span className="text-xl ml-2 font-normal">mmHg</span>
          </p>
        </div>

        <div className="p-8 bg-gradient-to-br from-green-50 to-green-100 rounded-2xl shadow-sm">
          <h3 className="text-sm font-semibold text-gray-600 mb-3">Total Measurements</h3>
          <p className="text-5xl font-bold text-green-600">
            {bpData.data.num_measurements ?? 'N/A'}
          </p>
        </div>
      </div>

      {bpData.data.peak_systolic && (
        <div className="grid grid-cols-2 gap-8">
          <div className="p-6 bg-orange-50 rounded-xl border border-orange-200">
            <h3 className="text-sm font-semibold text-gray-600 mb-3">Peak Systolic</h3>
            <p className="text-4xl font-bold text-orange-600">
              {bpData.data.peak_systolic.toFixed(0)} <span className="text-lg font-normal">mmHg</span>
            </p>
          </div>

          <div className="p-6 bg-teal-50 rounded-xl border border-teal-200">
            <h3 className="text-sm font-semibold text-gray-600 mb-3">Low Systolic</h3>
            <p className="text-4xl font-bold text-teal-600">
              {bpData.data.low_systolic?.toFixed(0) ?? 'N/A'} <span className="text-lg font-normal">mmHg</span>
            </p>
          </div>
        </div>
      )}

      <div className="mt-8 p-6 bg-blue-50 border border-blue-100 rounded-xl">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Understanding Blood Pressure</h3>
        <ul className="text-base text-gray-700 space-y-3 leading-relaxed">
          <li className="flex items-start">
            <span className="text-blue-500 mr-2">•</span>
            <span><span className="font-semibold text-gray-800">Systolic (top number):</span> Pressure when heart beats</span>
          </li>
          <li className="flex items-start">
            <span className="text-blue-500 mr-2">•</span>
            <span><span className="font-semibold text-gray-800">Diastolic (bottom number):</span> Pressure when heart rests</span>
          </li>
          <li className="flex items-start">
            <span className="text-blue-500 mr-2">•</span>
            <span><span className="font-semibold text-gray-800">Normal range:</span> Less than 120/80 mmHg</span>
          </li>
          <li className="flex items-start">
            <span className="text-blue-500 mr-2">•</span>
            <span><span className="font-semibold text-gray-800">Elevated:</span> 120-129 systolic and less than 80 diastolic</span>
          </li>
          <li className="flex items-start">
            <span className="text-blue-500 mr-2">•</span>
            <span><span className="font-semibold text-gray-800">High (Hypertension Stage 1):</span> 130-139 systolic or 80-89 diastolic</span>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default BloodPressureTab;
