import React, { useState, useEffect } from 'react';
import { providerApi } from '../../../utils/api';
import type { PatientOverview } from '../../../utils/api';

const BillingTab: React.FC = () => {
  const [allPatientData, setAllPatientData] = useState<PatientOverview[]>([]);
  const [filteredData, setFilteredData] = useState<PatientOverview[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchBillingData();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = allPatientData.filter(patient =>
        patient.patient_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredData(filtered);
    } else {
      setFilteredData(allPatientData);
    }
  }, [searchTerm, allPatientData]);

  const fetchBillingData = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await providerApi.getAllPatientsData();
      console.log('Fetched patient data:', data);
      setAllPatientData(data);
      setFilteredData(data);
    } catch (err) {
      console.error('Error fetching billing data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch billing data');
    } finally {
      setLoading(false);
    }
  };

  const handlePatientClick = (patient: PatientOverview) => {
    console.log('Patient clicked:', patient);
    // TODO: Implement modal to show patient details
    alert(`Patient: ${patient.patient_name}\nID: ${patient.healthie_user_id}`);
  };

  return (
    <div className="p-8 flex flex-col gap-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-bold text-gray-800">Billing Dashboard</h1>
          <p className="text-gray-600 text-base leading-relaxed">
            Select a patient to view their measurement history and billing information.
          </p>
        </div>
        <input
          type="text"
          placeholder="Search by name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="px-5 py-3 bg-gray-100 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base transition-all"
        />
      </div>

      {/* Table */}
      <div className="mt-4">
        {/* Table Header */}
        <div className="grid grid-cols-[1fr_3fr_1fr_1fr] gap-6 py-5 px-4 text-center bg-gray-50 rounded-t-xl border-b-2 border-gray-300">
          <h3 className="font-bold text-gray-700">ID</h3>
          <h3 className="font-bold text-left text-gray-700">Name</h3>
          <h3 className="font-bold text-gray-700">Eligibility</h3>
          <h3 className="font-bold text-gray-700">Device Training</h3>
        </div>

        {/* Table Content */}
        <div className="py-3 flex flex-col gap-2 bg-white rounded-b-xl">
          {loading && (
            <div className="flex flex-col items-center justify-center gap-4 py-12">
              <div className="w-10 h-10 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin"></div>
              <p className="text-gray-600 text-base">Fetching data...</p>
            </div>
          )}

          {error && (
            <div className="p-5 mx-4 my-2 bg-red-50 border border-red-200 text-red-700 rounded-lg">
              Error: {error}
            </div>
          )}

          {!loading && !error && filteredData.length === 0 && (
            <p className="text-gray-600 text-center py-12 text-base">No patients found.</p>
          )}

          {!loading && !error && filteredData
            .sort((a, b) => a.patient_name.localeCompare(b.patient_name))
            .map((patient) => (
              <div
                key={patient.healthie_user_id}
                onClick={() => handlePatientClick(patient)}
                className="grid grid-cols-[1fr_3fr_1fr_1fr] gap-6 py-5 px-4 mx-2 text-center items-center rounded-lg hover:bg-blue-50 hover:shadow-sm cursor-pointer transition-all"
              >
                <h3 className="text-gray-700">{patient.healthie_user_id}</h3>
                <h3 className="text-left text-gray-900 font-medium">{patient.patient_name}</h3>
                <h3>
                  {patient.eligible_to_bill ? (
                    <i className="fas fa-check text-green-600 text-lg"></i>
                  ) : (
                    <i className="fas fa-xmark text-red-600 text-lg"></i>
                  )}
                </h3>
                <h3>
                  {patient.bp_device_training_status ? (
                    <i className="fas fa-check text-green-600 text-lg"></i>
                  ) : (
                    <i className="fas fa-xmark text-red-600 text-lg"></i>
                  )}
                </h3>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default BillingTab;
