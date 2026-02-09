import React from 'react';

interface SystemTabProps {
  temporaryLookupCode: string;
  healthieUserId: string;
}

const SystemTab: React.FC<SystemTabProps> = ({ temporaryLookupCode, healthieUserId }) => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">System Information</h2>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-gray-50 rounded border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-600 mb-2">Temporary Lookup Code</h3>
          <p className="text-sm font-mono text-gray-800 break-all">
            {temporaryLookupCode || 'Not available'}
          </p>
        </div>

        <div className="p-4 bg-gray-50 rounded border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-600 mb-2">Healthie User ID</h3>
          <p className="text-sm font-mono text-gray-800">
            {healthieUserId || 'Not available'}
          </p>
        </div>
      </div>

      <div className="p-8 text-center bg-gray-50 rounded border border-gray-200">
        <i className="fas fa-cog text-5xl text-gray-400 mb-4"></i>
        <p className="text-gray-600 text-lg">
          System tools and settings will be available soon.
        </p>
      </div>
    </div>
  );
};

export default SystemTab;
