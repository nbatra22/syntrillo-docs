import React, { useState, useEffect } from 'react';
import ProviderTab from '../../components/provider-tab/ProviderTab';

const ProviderTabPage: React.FC = () => {
  const [temporaryLookupCode, setTemporaryLookupCode] = useState<string>('');
  const [healthieUserId, setHealthieUserId] = useState<string>('');

  useEffect(() => {
    // Extract parameters from URL
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('temporary_lookup_code');
    const userId = urlParams.get('healthie_user_id') || urlParams.get('hl_current_user_id');

    // Set values from URL or use dev defaults
    setTemporaryLookupCode(code || 'dev-test-code-123');
    setHealthieUserId(userId || '1033222');
  }, []);

  return (
    <div className="w-full max-w-[1200px] mx-auto bg-white rounded shadow">
      <ProviderTab
        temporaryLookupCode={temporaryLookupCode}
        healthieUserId={healthieUserId}
      />
    </div>
  );
};

export default ProviderTabPage;
