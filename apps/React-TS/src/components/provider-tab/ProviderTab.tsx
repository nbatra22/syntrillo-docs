import React, { useState } from 'react';
import RiskScoreTab from './tabs/RiskScoreTab';
import BloodPressureTab from './tabs/BloodPressureTab';
import MedicationsTab from './tabs/MedicationsTab';
import DevicesTab from './tabs/DevicesTab';
import SystemTab from './tabs/SystemTab';

type TabType = 'risk-score' | 'blood-pressure' | 'medications' | 'devices' | 'system';

interface ProviderTabProps {
  temporaryLookupCode: string;
  healthieUserId: string;
}

const ProviderTab: React.FC<ProviderTabProps> = ({ temporaryLookupCode, healthieUserId }) => {
  const [activeTab, setActiveTab] = useState<TabType>('risk-score');

  const tabs = [
    { id: 'risk-score' as TabType, label: 'Risk Score' },
    { id: 'blood-pressure' as TabType, label: 'Blood Pressure' },
    { id: 'medications' as TabType, label: 'Medications' },
    { id: 'devices' as TabType, label: 'Devices' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'risk-score':
        return <RiskScoreTab temporaryLookupCode={temporaryLookupCode} />;
      case 'blood-pressure':
        return <BloodPressureTab temporaryLookupCode={temporaryLookupCode} />;
      case 'medications':
        return <MedicationsTab temporaryLookupCode={temporaryLookupCode} />;
      case 'devices':
        return <DevicesTab temporaryLookupCode={temporaryLookupCode} />;
      case 'system':
        return <SystemTab temporaryLookupCode={temporaryLookupCode} healthieUserId={healthieUserId} />;
      default:
        return <RiskScoreTab temporaryLookupCode={temporaryLookupCode} />;
    }
  };

  return (
    <div className="w-full">
      {/* Tab Navigation */}
      <ul className="flex border-b border-gray-300 bg-white">
        {tabs.map((tab) => (
          <li key={tab.id} className="mr-1">
            <button
              onClick={() => setActiveTab(tab.id)}
              className={`inline-block py-3 px-4 font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-white'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`}
            >
              {tab.label}
            </button>
          </li>
        ))}

        {/* Spacer to push System tab to the right */}
        <li className="flex-grow"></li>

        {/* System Tab */}
        <li className="mr-1">
          <button
            onClick={() => setActiveTab('system')}
            className={`inline-block py-3 px-4 font-medium transition-colors ${
              activeTab === 'system'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-white'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            System
          </button>
        </li>
      </ul>

      {/* Tab Content */}
      <div className="bg-white border border-t-0 border-gray-300 rounded-b p-4">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default ProviderTab;
