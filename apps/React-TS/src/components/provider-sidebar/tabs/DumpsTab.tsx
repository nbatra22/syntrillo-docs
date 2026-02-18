import React from 'react';

const DumpsTab: React.FC = () => {
  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold mb-2">Dumps</h3>
      <p className="text-gray-600">Loading content. Please wait...</p>
      {/* TODO: Implement dumps content loading from Flask backend */}
    </div>
  );
};

export default DumpsTab;
