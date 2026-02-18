// ============================================================
// Data Dashboard — Types & Static Data
//
// Static data is used while the backend connection is pending.
// When ready, replace `staticDashboardData` usage in
// useDashboardData.ts with real API calls from providerTabApi.
// ============================================================

export type BPCellStatus = 'good' | 'bad' | 'warn';
export type BadgeType = 'optimized' | 'non-optimized' | 'partially-optimized';
export type DeviceStatus = 'connected' | 'unlinked' | 'disconnected';
export type StatusSeverity = 'critical' | 'warning' | 'normal';

export interface BPTarget {
  label: string;
  target: string;
  actual: string;
  met: boolean;
}

export interface BPDetailCell {
  value: string | number;
  status?: BPCellStatus;
}

export interface BPDetailRow {
  title: string;
  baseline: BPDetailCell;
  prior: BPDetailCell;
  latest: BPDetailCell;
}

export interface BloodPressureSummary {
  status: string;
  statusSeverity: StatusSeverity;
  targets: BPTarget[];
}

export interface BloodPressureDetail {
  source: string;
  periods: {
    baseline: { dateRange: string };
    prior:    { dateRange: string };
    latest:   { dateRange: string };
  };
  rows: BPDetailRow[];
}

export interface MedicalHistoryItem {
  label: string;
  value: string;
  badge?: BadgeType;
}

export interface LabValue {
  label: string;
  value: string;
  unit: string;
  alert?: boolean;
}

export interface Device {
  name: string;
  status: DeviceStatus;
}

export interface DashboardData {
  bloodPressureSummary: BloodPressureSummary;
  bloodPressureDetail: BloodPressureDetail;
  riskScore: number;
  priorityScore: number;
  medicalHistory: MedicalHistoryItem[];
  labValues: LabValue[];
  devices: Device[];
  heartRate: {
    current: number;
    currentDate: string;
    avgResting: number;
    baselineDateRange: string;
  };
  patientSummary: {
    height: string;
    weight: string;
    bmi: number;
    moderateVigorousActivity: string;
    physicalInactivity: string;
  };
}

export const staticDashboardData: DashboardData = {
  bloodPressureSummary: {
    status: 'Out of Target — Needs Aggressive Intervention',
    statusSeverity: 'critical',
    targets: [
      { label: 'Avg SBP',                          target: '< 125 mmHg', actual: '161.2 mmHg', met: false },
      { label: 'Avg DBP',                          target: '< 80 mmHg',  actual: '101.1 mmHg', met: false },
      { label: 'Peak SBP',                         target: '< 165 mmHg', actual: '163 mmHg',   met: true  },
      { label: 'Low SBP',                          target: '> 90 mmHg',  actual: '160 mmHg',   met: true  },
      { label: 'Symptomatic Hypotensive Episodes', target: '0',          actual: '0',           met: true  },
    ],
  },

  bloodPressureDetail: {
    source: "Received from patient's Tenovi BPM Device",
    periods: {
      baseline: { dateRange: '2/8/25 – 2/22/25'  },
      prior:    { dateRange: '1/19/26 – 2/2/26'  },
      latest:   { dateRange: '2/3/26 – 2/17/26'  },
    },
    rows: [
      { title: 'Measurement Count',        baseline: { value: 22    },                  prior: { value: 28    },                  latest: { value: 30    }                  },
      { title: 'Avg. SBP (mmHg)',          baseline: { value: 129.7, status: 'good' }, prior: { value: 145.1, status: 'bad'  }, latest: { value: 146.8, status: 'bad'  } },
      { title: 'Avg. DBP (mmHg)',          baseline: { value: 74.3,  status: 'good' }, prior: { value: 78.9,  status: 'good' }, latest: { value: 79.7,  status: 'good' } },
      { title: 'Avg. PP (mmHg)',           baseline: { value: 74.3,  status: 'good' }, prior: { value: 78.9,  status: 'good' }, latest: { value: 79.7,  status: 'good' } },
      { title: 'Peak SBP² (mmHg)',         baseline: { value: 55.4  },                  prior: { value: 66.2  },                  latest: { value: 67.1  }                  },
      { title: 'Peak DBP² (mmHg)',         baseline: { value: 142.3, status: 'good' }, prior: { value: 165.7, status: 'good' }, latest: { value: 164.0, status: 'good' } },
      { title: 'Low SBP³ (mmHg)',          baseline: { value: 92.3,  status: 'good' }, prior: { value: 87.3,  status: 'good' }, latest: { value: 88.7,  status: 'good' } },
      { title: 'Low DBP³ (mmHg)',          baseline: { value: 113.3 },                  prior: { value: 123.0 },                  latest: { value: 128.7 }                  },
      { title: 'SBP SD (mmHg)',            baseline: { value: 60.0  },                  prior: { value: 68.0  },                  latest: { value: 72.3  }                  },
      { title: 'DBP SD (mmHg)',            baseline: { value: 9.9,   status: 'warn' }, prior: { value: 6.0,   status: 'warn' }, latest: { value: 5.2,   status: 'warn' } },
      { title: 'SBP Count (>=170)',        baseline: { value: 0     },                  prior: { value: 0     },                  latest: { value: 1     }                  },
      { title: 'Near Hypotensive Events',  baseline: { value: 0     },                  prior: { value: 0     },                  latest: { value: 0     }                  },
      { title: 'Engagement',               baseline: { value: 100.0 },                  prior: { value: 115.4 },                  latest: { value: 107.7 }                  },
      { title: 'Progress',                 baseline: { value: '—'   },                  prior: { value: '—'   },                  latest: { value: '—'   }                  },
      { title: 'Average RHR (BPM)',        baseline: { value: 67.5  },                  prior: { value: 74.5  },                  latest: { value: 76.6  }                  },
      { title: 'Body Mass Index (kg/m²)',  baseline: { value: 31.3  },                  prior: { value: '—'   },                  latest: { value: 31.9  }                  },
      { title: 'Sodium Consumer Status',   baseline: { value: 98.5  },                  prior: { value: '—'   },                  latest: { value: 86.0  }                  },
    ],
  },

  riskScore:     10.65,
  priorityScore: 93.4,

  medicalHistory: [
    { label: 'History of Stroke',        value: 'Yes (1)',      badge: 'optimized'           },
    { label: 'Stroke Etiology',          value: 'Cardioembolic'                               },
    { label: 'Atrial Fibrillation',      value: 'Yes',          badge: 'optimized'           },
    { label: 'Congestive Heart Failure', value: 'Yes',          badge: 'non-optimized'       },
    { label: 'Hyperlipidemia',           value: 'Yes'                                         },
    { label: 'LDL Level',                value: 'High',         badge: 'non-optimized'       },
    { label: 'HDL Level',                value: 'Low',          badge: 'partially-optimized' },
  ],

  labValues: [
    { label: 'Hemoglobin A1C (HA1C)',          value: '—', unit: '%'     },
    { label: 'Low-Density Lipoprotein (LDL)',  value: '—', unit: 'mg/dL' },
    { label: 'High-Density Lipoprotein (HDL)', value: '—', unit: 'mg/dL' },
    { label: 'Triglycerides',                  value: '—', unit: 'mg/dL', alert: true },
    { label: 'Creatinine',                     value: '—', unit: 'mg/dL' },
  ],

  devices: [
    { name: 'Tenovi Watch',   status: 'unlinked'  },
    { name: 'Tenovi Pillbox', status: 'connected' },
    { name: 'Tenovi BPM - L', status: 'connected' },
  ],

  heartRate: {
    current:           57.56,
    currentDate:       '02/17/2026',
    avgResting:        78.50,
    baselineDateRange: '6/13/2025 – 6/27/2025',
  },

  patientSummary: {
    height:                   '6ft 0in',
    weight:                   '255 lbs',
    bmi:                      34.6,
    moderateVigorousActivity: '—',
    physicalInactivity:       '—',
  },
};
