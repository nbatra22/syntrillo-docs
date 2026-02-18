import React from 'react';

interface DevicesTabProps {
  temporaryLookupCode: string;
}

const DevicesTab: React.FC<DevicesTabProps> = ({ temporaryLookupCode }) => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Patient Devices</h2>
      <div className="p-8 text-center bg-purple-50 rounded border border-purple-200">
        <i className="fas fa-heartbeat text-5xl text-purple-400 mb-4"></i>
        <p className="text-gray-600 text-lg">
          Device management will be available soon.
        </p>
        <p className="text-gray-500 text-sm mt-2">
          This feature is currently in development.
        </p>
      </div>
    </div>
  );
};

export default DevicesTab;
