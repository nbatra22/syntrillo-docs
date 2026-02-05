import React from 'react';

const StatusTab: React.FC = () => {
  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold mb-2">Status</h3>
      <p className="text-gray-600">Loading content. Please wait...</p>
      {/* TODO: Implement status content loading from Flask backend */}
    </div>
  );
};

export default StatusTab;
