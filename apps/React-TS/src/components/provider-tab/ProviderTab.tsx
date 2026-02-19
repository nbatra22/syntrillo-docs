import React from 'react';
import DataDashboard from './dashboard/DataDashboard';

interface ProviderTabProps {
  temporaryLookupCode: string;
  healthieUserId: string;
}

const ProviderTab: React.FC<ProviderTabProps> = ({ temporaryLookupCode }) => {
  return (
    <div style={{ maxWidth: '1200px' }}>
      <DataDashboard temporaryLookupCode={temporaryLookupCode} />
    </div>
  );
};

export default ProviderTab;
