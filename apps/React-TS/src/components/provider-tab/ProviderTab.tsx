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
    <div className="w-full px-6 py-4">
      {/* Tab Navigation */}
      <ul className="flex border-b-2 border-gray-200 bg-white rounded-t-xl overflow-hidden">
        {tabs.map((tab) => (
          <li key={tab.id} className="mr-1">
            <button
              onClick={() => setActiveTab(tab.id)}
              className={`inline-block py-4 px-6 font-medium transition-all ${
                activeTab === tab.id
                  ? 'text-blue-600 border-b-3 border-blue-600 bg-blue-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              {tab.label}
            </button>
          </li>
        ))}

        {/* Spacer to push System tab to the right */}
        <li className="flex-grow"></li>

        {/* System Tab */}
        <li className="mr-4">
          <button
            onClick={() => setActiveTab('system')}
            className={`inline-block py-4 px-6 font-medium transition-all ${
              activeTab === 'system'
                ? 'text-blue-600 border-b-3 border-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            System
          </button>
        </li>
      </ul>

      {/* Tab Content */}
      <div className="bg-white rounded-b-xl shadow-sm p-8 min-h-[500px]">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default ProviderTab;
