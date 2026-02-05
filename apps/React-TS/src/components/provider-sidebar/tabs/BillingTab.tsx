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
    <div className="p-4 flex flex-col gap-4">
      {/* Header */}
      <div className="flex justify-between items-center pt-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-xl font-bold">Billing Dashboard</h1>
          <p className="text-gray-600 text-sm">
            Select a patient to view their measurement history and billing information.
          </p>
        </div>
        <input
          type="text"
          placeholder="Search by name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="px-3 py-2 bg-gray-200 border-none rounded outline-none text-sm"
        />
      </div>

      {/* Table */}
      <div className="mt-4">
        {/* Table Header */}
        <div className="grid grid-cols-[1fr_3fr_1fr_1fr] gap-4 py-4 text-center border-b-2 border-black">
          <h3 className="font-bold">ID</h3>
          <h3 className="font-bold text-left">Name</h3>
          <h3 className="font-bold">Eligibility</h3>
          <h3 className="font-bold">Device Training</h3>
        </div>

        {/* Table Content */}
        <div className="py-2 flex flex-col gap-2">
          {loading && (
            <div className="flex flex-col items-center justify-center gap-4 py-8">
              <div className="w-8 h-8 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin"></div>
              <p className="text-gray-600">Fetching data...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-100 text-red-700 rounded">
              Error: {error}
            </div>
          )}

          {!loading && !error && filteredData.length === 0 && (
            <p className="text-gray-600 text-center py-8">No patients found.</p>
          )}

          {!loading && !error && filteredData
            .sort((a, b) => a.patient_name.localeCompare(b.patient_name))
            .map((patient) => (
              <div
                key={patient.healthie_user_id}
                onClick={() => handlePatientClick(patient)}
                className="grid grid-cols-[1fr_3fr_1fr_1fr] gap-4 py-4 text-center items-center rounded hover:bg-gray-200 cursor-pointer"
              >
                <h3>{patient.healthie_user_id}</h3>
                <h3 className="text-left">{patient.patient_name}</h3>
                <h3>
                  {patient.eligible_to_bill ? (
                    <i className="fas fa-check text-green-600"></i>
                  ) : (
                    <i className="fas fa-xmark text-red-600"></i>
                  )}
                </h3>
                <h3>
                  {patient.bp_device_training_status ? (
                    <i className="fas fa-check text-green-600"></i>
                  ) : (
                    <i className="fas fa-xmark text-red-600"></i>
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
