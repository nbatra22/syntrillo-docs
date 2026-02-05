import React from 'react';

const SystemTab: React.FC = () => {
  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold mb-2">System</h3>
      <p className="text-gray-600">Loading content. Please wait...</p>
      {/* TODO: Implement system content loading from Flask backend */}
    </div>
  );
};

export default SystemTab;
