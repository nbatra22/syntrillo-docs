import React, { useState, useEffect } from 'react';
import PatientDashboard from '../../components/patient-sidebar/PatientDashboard';

const PatientSidebarPage: React.FC = () => {
  const [temporaryLookupCode, setTemporaryLookupCode] = useState<string>('');

  useEffect(() => {
    // Extract temporary lookup code from URL params
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('temporary_lookup_code');
    if (code) {
      setTemporaryLookupCode(code);
    }
  }, []);

  return (
    <div className="w-full max-w-[1200px] mx-auto bg-white p-6 rounded shadow">
      <PatientDashboard temporaryLookupCode={temporaryLookupCode} />
    </div>
  );
};

export default PatientSidebarPage;
