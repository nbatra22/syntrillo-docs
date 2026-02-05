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
    <div className="w-full max-w-[1200px] mx-auto">
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

        {/* Spacer to push System tab and Logout to the right */}
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

        {/* Logout Button */}
        <li className="flex items-center ml-2 mr-2">
          <button
            onClick={handleLogout}
            className="px-3 py-2 text-sm font-medium text-red-600 border border-red-600 rounded hover:bg-red-50 transition-colors"
          >
            <i className="fas fa-sign-out-alt mr-1"></i> Logout
          </button>
        </li>
      </ul>

      {/* Tab Content */}
      <div className="bg-white border border-t-0 border-gray-300 rounded-b">
        {renderTabContent()}
      </div>

      {/* Bottom Spacer */}
      <div className="bg-white mb-5">
        <p>&nbsp;</p>
      </div>
    </div>
  );
};

export default ProviderSidebar;
