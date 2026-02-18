import React from 'react';
import ProviderTab from '../../components/provider-tab/ProviderTab';

const ProviderTabPage: React.FC = () => {
  const params = new URLSearchParams(window.location.search);
  const temporaryLookupCode = params.get('temporaryLookupCode') ?? 'dev-test';
  const healthieUserId      = params.get('healthieUserId')      ?? 'dev-user';

  return (
    <ProviderTab
      temporaryLookupCode={temporaryLookupCode}
      healthieUserId={healthieUserId}
    />
  );
};

export default ProviderTabPage;
