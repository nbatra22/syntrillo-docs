import React from 'react';

interface SystemDevicesTabProps {
  temporaryLookupCode: string;
  healthieUserId: string;
}

const SystemDevicesTab: React.FC<SystemDevicesTabProps> = ({ temporaryLookupCode, healthieUserId }) => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">System Devices</h2>

      <div className="p-8 text-center bg-gray-50 rounded border border-gray-200">
        <i className="fas fa-mobile-alt text-5xl text-gray-400 mb-4"></i>
        <p className="text-gray-600 text-lg">
          Device management and configuration will be available soon.
        </p>
      </div>
    </div>
  );
};

export default SystemDevicesTab;
