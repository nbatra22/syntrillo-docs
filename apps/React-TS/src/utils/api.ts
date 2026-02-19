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

export interface BloodPressureData {
  success: boolean;
  error: string | null;
  data: {
    status: { value: string; grade: number };
    avg_sbp: { value: number; grade: number };
    avg_dbp: { value: number; grade: number };
    peak_sbp: { value: number; grade: number };
    low_sbp: { value: number; grade: number };
    symptomatic_hypotension: { value: number };
    near_hypotensive: { value: number };
    avg_systolic?: number;
    avg_diastolic?: number;
    peak_systolic?: number;
    low_systolic?: number;
    num_measurements?: number;
  };
}

export interface StrokeRiskData {
  success: boolean;
  message?: string;
  data: {
    risk_score?: number;
    priority_score?: number;
    metrics?: Record<string, any>;
    independent_risk_variable_scores?: Record<string, any>;
    dependent_risk_variable_contributions?: Record<string, any>;
  };
}

export interface HeartRateData {
  average_rhr_baseline?: number;
  average_rhr_trailing?: number;
  average_rhr_prior?: number;
  baseline_start_date?: string;
  baseline_end_date?: string;
  prior_start_date?: string;
  prior_end_date?: string;
  current_start_date?: string;
  current_end_date?: string;
}

export interface BiometricsData {
  physical_activity_data: {
    inactive: {
      inactivity_baseline?: any;
      inactivity_prior?: any;
      inactivity_current?: any;
    };
    active: {
      activity_baseline?: any;
      activity_prior?: any;
      activity_current?: any;
    };
  };
  bmi_data: {
    bmi_current?: { bmi: number; date: string };
    bmi_prior?: { bmi: number; date: string };
    bmi_baseline?: { bmi: number; date: string };
  };
  ssq_data: {
    ssq_current?: number;
    ssq_prior?: number;
    ssq_baseline?: number;
    ssq_baseline_date?: string;
    ssq_prior_date?: string;
    ssq_current_date?: string;
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

/**
 * Patient Sidebar API calls
 */
export const patientSidebarApi = {
  /**
   * Get blood pressure summary data for patient sidebar
   */
  getBloodPressure: async (temporaryLookupCode: string): Promise<BloodPressureData> => {
    const response = await fetch(`${API_BASE_URL}/healthie/iframe/patient_sidebar/blood_pressure`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        temporary_lookup_code: temporaryLookupCode,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch blood pressure data');
    }

    return response.json();
  },

  getBPSummary: async (temporaryLookupCode: string): Promise<BloodPressureData> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/blood-pressure/summary`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        temporary_lookup_code: temporaryLookupCode,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch blood pressure data');
    }

    return response.json();
  },

  /**
   * Get heart rate data for patient sidebar
   */
  getHeartRate: async (temporaryLookupCode: string): Promise<HeartRateData> => {
    const response = await fetch(`${API_BASE_URL}/healthie/iframe/patient_sidebar/heart_rate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        temporary_lookup_code: temporaryLookupCode,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch heart rate data');
    }

    return response.json();
  },

  /**
   * Get biometrics data (BMI, physical activity, sodium) for patient sidebar
   */
  getBiometrics: async (temporaryLookupCode: string): Promise<BiometricsData> => {
    const response = await fetch(`${API_BASE_URL}/healthie/iframe/patient_sidebar/biometrics`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        temporary_lookup_code: temporaryLookupCode,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch biometrics data');
    }

    return response.json();
  },

  /**
   * Get stroke risk factors data for patient sidebar
   */
  getStrokeRiskFactors: async (temporaryLookupCode: string): Promise<StrokeRiskData> => {
    const response = await fetch(`${API_BASE_URL}/healthie/iframe/patient_sidebar/stroke_risk_factors`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        temporary_lookup_code: temporaryLookupCode,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch stroke risk factors');
    }

    return response.json();
  },
};

/**
 * Provider Tab API calls (Patient Extra Tab in Healthie)
 */
export const providerTabApi = {
  /**
   * Get blood pressure data for provider tab
   */
  getBloodPressure: async (temporaryLookupCode: string): Promise<BloodPressureData> => {
    const response = await fetch(`${API_BASE_URL}/healthie/iframe/patient_sidebar/blood_pressure`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        temporary_lookup_code: temporaryLookupCode,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch blood pressure data');
    }

    return response.json();
  },

  /**
   * Get stroke risk factors for provider tab
   */
  getStrokeRiskFactors: async (temporaryLookupCode: string): Promise<StrokeRiskData> => {
    const response = await fetch(`${API_BASE_URL}/healthie/iframe/patient_sidebar/stroke_risk_factors`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        temporary_lookup_code: temporaryLookupCode,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch stroke risk factors');
    }

    return response.json();
  },
};
