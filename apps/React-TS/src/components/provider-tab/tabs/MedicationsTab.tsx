import React from 'react';

interface MedicationsTabProps {
  temporaryLookupCode: string;
}

const MedicationsTab: React.FC<MedicationsTabProps> = ({ temporaryLookupCode }) => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Medications</h2>
      <div className="p-8 text-center bg-blue-50 rounded border border-blue-200">
        <i className="fas fa-pills text-5xl text-blue-400 mb-4"></i>
        <p className="text-gray-600 text-lg">
          Medications management will be available soon.
        </p>
        <p className="text-gray-500 text-sm mt-2">
          This feature is currently in development.
        </p>
      </div>
    </div>
  );
};

export default MedicationsTab;
