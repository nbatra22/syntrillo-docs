import React, { useState } from 'react';
import BillingTab from './tabs/BillingTab';
import StatusTab from './tabs/StatusTab';
import QuestionnaireDatabaseTab from './tabs/QuestionnaireDatabaseTab';
import DumpsTab from './tabs/DumpsTab';
import SystemTab from './tabs/SystemTab';

type TabType = 'billing' | 'status' | 'questionnaire-database' | 'dumps' | 'system';

const ProviderSidebar: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('billing');

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    window.location.reload();
  };

  const tabs = [
    { id: 'billing' as TabType, label: 'Billing' },
    { id: 'status' as TabType, label: 'Status' },
    { id: 'questionnaire-database' as TabType, label: 'Questionnaires (database)' },
    { id: 'dumps' as TabType, label: 'Dumps' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'billing':
        return <BillingTab />;
      case 'status':
        return <StatusTab />;
      case 'questionnaire-database':
        return <QuestionnaireDatabaseTab />;
      case 'dumps':
        return <DumpsTab />;
      case 'system':
        return <SystemTab />;
      default:
        return <BillingTab />;
    }
  };

  return (
    <div className="w-full max-w-[1400px] mx-auto px-6 py-4">
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

        {/* Spacer to push System tab and Logout to the right */}
        <li className="flex-grow"></li>

        {/* System Tab */}
        <li className="mr-2">
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

        {/* Logout Button */}
        <li className="flex items-center ml-2 mr-4">
          <button
            onClick={handleLogout}
            className="px-5 py-2.5 text-sm font-medium text-red-600 border-2 border-red-600 rounded-lg hover:bg-red-50 hover:shadow-sm transition-all"
          >
            <i className="fas fa-sign-out-alt mr-2"></i> Logout
          </button>
        </li>
      </ul>

      {/* Tab Content */}
      <div className="bg-white rounded-b-xl shadow-sm min-h-[500px]">
        {renderTabContent()}
      </div>

      {/* Bottom Spacer */}
      <div className="mb-8"></div>
    </div>
  );
};

export default ProviderSidebar;
