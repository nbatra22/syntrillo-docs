import React, { useState } from 'react';
import RiskScoreTab from './tabs/RiskScoreTab';
import BloodPressureTab from './tabs/BloodPressureTab';
import MedicationsTab from './tabs/MedicationsTab';
import DevicesTab from './tabs/DevicesTab';
import SystemTab from './tabs/SystemTab';
import SystemDevicesTab from './tabs/SystemDevicesTab';

type TabType = 'risk-score' | 'blood-pressure' | 'medications' | 'devices' | 'system' | 'system-devices';

interface ProviderTabProps {
  temporaryLookupCode: string;
  healthieUserId: string;
}

const ProviderTab: React.FC<ProviderTabProps> = ({ temporaryLookupCode, healthieUserId }) => {
  const [activeTab, setActiveTab] = useState<TabType>('risk-score');

  const leftTabs = [
    { id: 'risk-score' as TabType, label: 'Risk Score' },
    { id: 'blood-pressure' as TabType, label: 'Blood Pressure' },
    { id: 'medications' as TabType, label: 'Medications' },
    { id: 'devices' as TabType, label: 'Devices' },
  ];

  const rightTabs = [
    { id: 'system' as TabType, label: 'System' },
    { id: 'system-devices' as TabType, label: 'System Devices' },
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
      case 'system-devices':
        return <SystemDevicesTab temporaryLookupCode={temporaryLookupCode} healthieUserId={healthieUserId} />;
      default:
        return <RiskScoreTab temporaryLookupCode={temporaryLookupCode} />;
    }
  };

  return (
    <div style={{ maxWidth: '1200px' }}>
      {/* Tab Navigation - Bootstrap nav-tabs style */}
      <ul style={{
        display: 'flex',
        listStyle: 'none',
        padding: 0,
        margin: 0,
        borderBottom: '1px solid #dee2e6'
      }} role="tablist">
        {leftTabs.map((tab) => (
          <li key={tab.id} style={{ marginRight: '0.25rem' }}>
            <a
              onClick={(e) => {
                e.preventDefault();
                setActiveTab(tab.id);
              }}
              href={`#tab-${tab.id}`}
              role="tab"
              style={{
                display: 'block',
                padding: '0.5rem 1rem',
                border: '1px solid transparent',
                borderTopLeftRadius: '0.25rem',
                borderTopRightRadius: '0.25rem',
                color: activeTab === tab.id ? '#495057' : '#007bff',
                backgroundColor: activeTab === tab.id ? '#fff' : 'transparent',
                borderColor: activeTab === tab.id ? '#dee2e6 #dee2e6 #fff' : 'transparent',
                cursor: 'pointer',
                textDecoration: 'none'
              }}
            >
              {tab.label}
            </a>
          </li>
        ))}

        {/* Spacer to push right tabs to the right */}
        <li style={{ flex: 1, marginLeft: 'auto' }}></li>

        {/* Right Tabs (System and System Devices) */}
        {rightTabs.map((tab) => (
          <li key={tab.id} style={{ marginRight: '0.25rem' }}>
            <a
              onClick={(e) => {
                e.preventDefault();
                setActiveTab(tab.id);
              }}
              href={`#tab-${tab.id}`}
              role="tab"
              style={{
                display: 'block',
                padding: '0.5rem 1rem',
                border: '1px solid transparent',
                borderTopLeftRadius: '0.25rem',
                borderTopRightRadius: '0.25rem',
                color: activeTab === tab.id ? '#495057' : '#007bff',
                backgroundColor: activeTab === tab.id ? '#fff' : 'transparent',
                borderColor: activeTab === tab.id ? '#dee2e6 #dee2e6 #fff' : 'transparent',
                cursor: 'pointer',
                textDecoration: 'none'
              }}
            >
              {tab.label}
            </a>
          </li>
        ))}
      </ul>

      {/* Tab Content */}
      <div style={{ padding: '1.5rem', backgroundColor: '#fff' }}>
        {renderTabContent()}
      </div>
    </div>
  );
};

export default ProviderTab;
