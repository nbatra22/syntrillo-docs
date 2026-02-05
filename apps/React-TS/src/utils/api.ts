// API configuration and utility functions

const API_BASE_URL = import.meta.env.DEV
  ? '' // Proxy handles this in dev mode
  : 'https://your-production-domain.com'; // Update with your production URL

// Types
export interface PatientOverview {
  healthie_user_id: string;
  patient_name: string;
  bp_device_training_status: boolean;
  eligible_to_bill: boolean;
}

export interface PatientBillingData {
  date_of_service: string;
  status: string;
}

export interface PatientDetailData {
  patient_bp_data: string[]; // Array of ISO date strings
  patient_billing_data: PatientBillingData[];
  status_map: {
    completed: string[];
    pending: string[];
    unbilled: string[];
  };
}

/**
 * Provider Sidebar API calls
 */
export const providerApi = {
  /**
   * Get all patients overview data for billing dashboard
   */
  getAllPatientsData: async (): Promise<PatientOverview[]> => {
    const authToken = localStorage.getItem('authToken');

    const response = await fetch(`${API_BASE_URL}/healthie/iframe_provider_sidebar/all_patients_data`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch all patients data');
    }

    const data = await response.json();
    return data.all_patient_overview_data;
  },

  /**
   * Get single patient detailed billing and BP data
   */
  getSinglePatientData: async (healthieUserId: string): Promise<PatientDetailData> => {
    const authToken = localStorage.getItem('authToken');

    const response = await fetch(
      `${API_BASE_URL}/healthie/iframe_provider_sidebar/single_patient_data?healthie_user_id=${encodeURIComponent(healthieUserId)}`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch patient data');
    }

    return response.json();
  },
};
