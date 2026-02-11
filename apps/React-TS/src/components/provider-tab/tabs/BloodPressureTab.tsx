import React, { useState, useEffect } from 'react';
import { providerTabApi, patientSidebarApi } from '../../../utils/api';
import type { BloodPressureData, HeartRateData, BiometricsData } from '../../../utils/api';

interface BloodPressureTabProps {
  temporaryLookupCode: string;
}

const BloodPressureTab: React.FC<BloodPressureTabProps> = ({ temporaryLookupCode }) => {
  const [bpData, setBpData] = useState<BloodPressureData | null>(null);
  const [heartRateData, setHeartRateData] = useState<HeartRateData | null>(null);
  const [biometricsData, setBiometricsData] = useState<BiometricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (temporaryLookupCode) {
      fetchData();
    }
  }, [temporaryLookupCode]);

  const fetchData = async () => {
    setLoading(true);
    setError('');

    try {
      const [bloodPressureData, hrData, bioData] = await Promise.all([
        providerTabApi.getBloodPressure(temporaryLookupCode),
        patientSidebarApi.getHeartRate(temporaryLookupCode),
        patientSidebarApi.getBiometrics(temporaryLookupCode),
      ]);
      setBpData(bloodPressureData);
      setHeartRateData(hrData);
      setBiometricsData(bioData);
    } catch (err) {
      console.error('Error fetching blood pressure:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch blood pressure data');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | undefined): string => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'numeric',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-12">
        <div className="w-10 h-10 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin"></div>
        <p className="text-gray-600 text-base">Loading blood pressure data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-5 bg-red-50 border border-red-200 text-red-700 rounded-lg">
        Error: {error}
      </div>
    );
  }

  const getGradeIcon = (grade: number) => {
    if (grade === 0) return <i className="fa-solid fa-circle-check" style={{ color: '#16a34a' }}></i>;
    if (grade === 1) return <i className="fa-solid fa-circle-exclamation" style={{ color: '#eab308' }}></i>;
    if (grade === 2) return <i className="fa-solid fa-circle-exclamation" style={{ color: '#ea580c' }}></i>;
    return <i className="fa-solid fa-circle-xmark" style={{ color: '#dc2626' }}></i>;
  };

  const getStatusColor = (grade: number) => {
    if (grade === 0) return '#16a34a';
    if (grade === 1) return '#f59e0b';
    return '#dc2626';
  };

  if (!bpData?.data) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: '#6b7280', fontWeight: 500 }}>
        No blood pressure data available for this patient.
      </div>
    );
  }

  return (
    <section style={{ padding: '1rem 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontWeight: 'bold', fontSize: 'large', margin: 0 }}>
          Blood Pressure Analysis
        </h2>
      </div>

      <div style={{ margin: '0.5rem 0' }}>
        {/* BP Summary Container matching patient sidebar */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'stretch',
          backgroundColor: '#e5e7eb',
          borderRadius: '0.375rem',
          height: 'fit-content',
          padding: '1rem 0'
        }}>
          {/* Status Column */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.5rem',
            width: '33%',
            padding: '0 1rem'
          }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 500, color: '#6b7280', margin: 0, textDecoration: 'underline' }}>
              Status
            </h3>
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
              <span style={{
                fontSize: '1.5rem',
                fontWeight: 'bold',
                textAlign: 'center',
                color: getStatusColor(bpData.data.status.grade)
              }}>
                {bpData.data.status.value}
              </span>
            </div>
          </div>

          {/* Targets Column */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.5rem',
            width: '33%',
            padding: '0 1rem',
            borderRight: '1px solid #d1d5db',
            borderLeft: '1px solid #d1d5db'
          }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 500, color: '#6b7280', margin: 0, textDecoration: 'underline' }}>
              Targets
            </h3>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              flex: 1,
              width: '100%',
              gap: '0.5rem'
            }}>
              <p style={{ color: '#16284a', lineHeight: '30px', margin: 0 }}>Avg SBP &lt; 125 mmHg</p>
              <p style={{ color: '#16284a', lineHeight: '30px', margin: 0 }}>Avg DBP &lt; 80 mmHg</p>
              <p style={{ color: '#16284a', lineHeight: '30px', margin: 0 }}>Peak SBP &lt; 165 mmHg</p>
              <p style={{ color: '#16284a', lineHeight: '30px', margin: 0 }}>Low SBP &gt; 90 mmHg</p>
              <p style={{ color: '#16284a', lineHeight: '30px', margin: 0 }}>Symptomatic Hypotensive Episodes: 0</p>
              <p style={{ color: '#16284a', lineHeight: '30px', margin: 0 }}>Near-Hypotensive Episodes: 0</p>
            </div>
          </div>

          {/* Actual Column */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.5rem',
            width: '33%',
            padding: '0 1rem'
          }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 500, color: '#6b7280', margin: 0, textDecoration: 'underline' }}>
              Actual
            </h3>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              flex: 1,
              width: '100%',
              gap: '0.5rem'
            }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1rem 1fr', alignItems: 'center', gap: '1rem', fontSize: '20px', marginLeft: '0.5rem' }}>
                <span>{getGradeIcon(bpData.data.avg_sbp.grade)}</span>
                <p style={{ margin: 0, color: '#16284a' }}>Avg SBP: {bpData.data.avg_sbp.value} mmHg</p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1rem 1fr', alignItems: 'center', gap: '1rem', fontSize: '20px', marginLeft: '0.5rem' }}>
                <span>{getGradeIcon(bpData.data.avg_dbp.grade)}</span>
                <p style={{ margin: 0, color: '#16284a' }}>Avg DBP: {bpData.data.avg_dbp.value} mmHg</p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1rem 1fr', alignItems: 'center', gap: '1rem', fontSize: '20px', marginLeft: '0.5rem' }}>
                <span>{getGradeIcon(bpData.data.peak_sbp.grade)}</span>
                <p style={{ margin: 0, color: '#16284a' }}>Peak SBP: {bpData.data.peak_sbp.value} mmHg</p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1rem 1fr', alignItems: 'center', gap: '1rem', fontSize: '20px', marginLeft: '0.5rem' }}>
                <span>{getGradeIcon(bpData.data.low_sbp.grade)}</span>
                <p style={{ margin: 0, color: '#16284a' }}>Low SBP: {bpData.data.low_sbp.value} mmHg</p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1rem 1fr', alignItems: 'center', gap: '1rem', fontSize: '20px', marginLeft: '0.5rem' }}>
                <span>{bpData.data.symptomatic_hypotension.value > 0 ? getGradeIcon(3) : getGradeIcon(0)}</span>
                <p style={{ margin: 0, color: '#16284a' }}>Symptomatic Hypotensive Episodes: {bpData.data.symptomatic_hypotension.value}</p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1rem 1fr', alignItems: 'center', gap: '1rem', fontSize: '20px', marginLeft: '0.5rem' }}>
                <span>{bpData.data.near_hypotensive.value > 0 ? getGradeIcon(3) : getGradeIcon(0)}</span>
                <p style={{ margin: 0, color: '#16284a' }}>Near-Hypotensive Episodes: {bpData.data.near_hypotensive.value}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Footnote */}
        <p style={{ marginTop: '1rem', color: '#6b7280', fontSize: 'small' }}>
          The data above is calculated using the most recent two weeks of measurements.
        </p>
      </div>

      {/* Heart Rate Section */}
      <section style={{ padding: '1rem 0', marginTop: '2rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 'bold' }}>
            Resting Heart Rate
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            All heart rate measurements can be viewed on the patient's Healthie metrics tab.
          </p>
        </div>
      </section>

      <section style={{ padding: '1rem 0' }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          backgroundColor: 'white',
          border: '1px solid #d1d5db',
          borderRadius: '0.375rem',
          overflow: 'hidden'
        }}>
          <thead style={{ backgroundColor: '#f9fafb' }}>
            <tr>
              <td style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, color: '#374151', borderBottom: '1px solid #d1d5db', fontSize: '0.875rem' }}></td>
              <td style={{ padding: '1rem', textAlign: 'center', fontWeight: 600, color: '#374151', borderBottom: '1px solid #d1d5db', fontSize: '0.875rem' }}>Baseline</td>
              <td style={{ padding: '1rem', textAlign: 'center', fontWeight: 600, color: '#374151', borderBottom: '1px solid #d1d5db', fontSize: '0.875rem' }}>Prior</td>
              <td style={{ padding: '1rem', textAlign: 'center', fontWeight: 600, color: '#374151', borderBottom: '1px solid #d1d5db', fontSize: '0.875rem' }}>Latest</td>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', fontWeight: 'bold' }}>Date Range</td>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', textAlign: 'center' }}>
                {heartRateData?.baseline_start_date && heartRateData?.baseline_end_date
                  ? `${formatDate(heartRateData.baseline_start_date)} - ${formatDate(heartRateData.baseline_end_date)}`
                  : '-'}
              </td>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', textAlign: 'center' }}>
                {heartRateData?.prior_start_date && heartRateData?.prior_end_date
                  ? `${formatDate(heartRateData.prior_start_date)} - ${formatDate(heartRateData.prior_end_date)}`
                  : '-'}
              </td>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', textAlign: 'center' }}>
                {heartRateData?.current_start_date && heartRateData?.current_end_date
                  ? `${formatDate(heartRateData.current_start_date)} - ${formatDate(heartRateData.current_end_date)}`
                  : '-'}
              </td>
            </tr>
            <tr>
              <td style={{ padding: '1rem', color: '#16284a', fontWeight: 'bold' }}>Average RHR</td>
              <td style={{ padding: '1rem', color: '#16284a', textAlign: 'center' }}>
                {heartRateData?.average_rhr_baseline?.toFixed(1) ?? '-'}
              </td>
              <td style={{ padding: '1rem', color: '#16284a', textAlign: 'center' }}>
                {heartRateData?.average_rhr_prior?.toFixed(1) ?? '-'}
              </td>
              <td style={{ padding: '1rem', color: '#16284a', textAlign: 'center' }}>
                {heartRateData?.average_rhr_trailing?.toFixed(1) ?? '-'}
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      {/* Biometrics Section */}
      <section style={{ padding: '1rem 0', marginTop: '2rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 'bold' }}>
            Biometrics
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            Data is sourced from the patient's Healthie forms.
          </p>
        </div>
      </section>

      <section style={{ padding: '1rem 0' }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          backgroundColor: 'white',
          border: '1px solid #d1d5db',
          borderRadius: '0.375rem',
          overflow: 'hidden'
        }}>
          <thead style={{ backgroundColor: '#f9fafb' }}>
            <tr>
              <td style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, color: '#374151', borderBottom: '1px solid #d1d5db', fontSize: '0.875rem' }}></td>
              <td style={{ padding: '1rem', textAlign: 'center', fontWeight: 600, color: '#374151', borderBottom: '1px solid #d1d5db', fontSize: '0.875rem' }}>Baseline</td>
              <td style={{ padding: '1rem', textAlign: 'center', fontWeight: 600, color: '#374151', borderBottom: '1px solid #d1d5db', fontSize: '0.875rem' }}>Prior</td>
              <td style={{ padding: '1rem', textAlign: 'center', fontWeight: 600, color: '#374151', borderBottom: '1px solid #d1d5db', fontSize: '0.875rem' }}>Latest</td>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', fontWeight: 'bold' }}>Body mass index (kg/m²)</td>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', textAlign: 'center' }}>
                {biometricsData?.bmi_data?.bmi_baseline?.bmi ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      As of {formatDate(biometricsData.bmi_data.bmi_baseline.date)}
                    </div>
                    <div>{biometricsData.bmi_data.bmi_baseline.bmi.toFixed(1)}</div>
                  </div>
                ) : '-'}
              </td>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', textAlign: 'center' }}>
                {biometricsData?.bmi_data?.bmi_prior?.bmi ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      As of {formatDate(biometricsData.bmi_data.bmi_prior.date)}
                    </div>
                    <div>{biometricsData.bmi_data.bmi_prior.bmi.toFixed(1)}</div>
                  </div>
                ) : '-'}
              </td>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', textAlign: 'center' }}>
                {biometricsData?.bmi_data?.bmi_current?.bmi ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      As of {formatDate(biometricsData.bmi_data.bmi_current.date)}
                    </div>
                    <div>{biometricsData.bmi_data.bmi_current.bmi.toFixed(1)}</div>
                  </div>
                ) : '-'}
              </td>
            </tr>
            <tr>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', fontWeight: 'bold' }}>Physical Activity (min/week)</td>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', textAlign: 'center' }}>
                {biometricsData?.physical_activity_data?.active?.activity_baseline?.[0] ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      As of {formatDate(biometricsData.physical_activity_data.active.activity_baseline[1])}
                    </div>
                    <div>{biometricsData.physical_activity_data.active.activity_baseline[0]}</div>
                  </div>
                ) : '-'}
              </td>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', textAlign: 'center' }}>
                {biometricsData?.physical_activity_data?.active?.activity_prior?.[0] ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      As of {formatDate(biometricsData.physical_activity_data.active.activity_prior[1])}
                    </div>
                    <div>{biometricsData.physical_activity_data.active.activity_prior[0]}</div>
                  </div>
                ) : '-'}
              </td>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', textAlign: 'center' }}>
                {biometricsData?.physical_activity_data?.active?.activity_current?.[0] ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      As of {formatDate(biometricsData.physical_activity_data.active.activity_current[1])}
                    </div>
                    <div>{biometricsData.physical_activity_data.active.activity_current[0]}</div>
                  </div>
                ) : '-'}
              </td>
            </tr>
            <tr>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', fontWeight: 'bold' }}>Physical Inactivity (hours/day)</td>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', textAlign: 'center' }}>
                {biometricsData?.physical_activity_data?.inactive?.inactivity_baseline?.[0] ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      As of {formatDate(biometricsData.physical_activity_data.inactive.inactivity_baseline[1])}
                    </div>
                    <div>{biometricsData.physical_activity_data.inactive.inactivity_baseline[0]}</div>
                  </div>
                ) : '-'}
              </td>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', textAlign: 'center' }}>
                {biometricsData?.physical_activity_data?.inactive?.inactivity_prior?.[0] ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      As of {formatDate(biometricsData.physical_activity_data.inactive.inactivity_prior[1])}
                    </div>
                    <div>{biometricsData.physical_activity_data.inactive.inactivity_prior[0]}</div>
                  </div>
                ) : '-'}
              </td>
              <td style={{ padding: '1rem', borderBottom: '1px solid #d1d5db', color: '#16284a', textAlign: 'center' }}>
                {biometricsData?.physical_activity_data?.inactive?.inactivity_current?.[0] ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      As of {formatDate(biometricsData.physical_activity_data.inactive.inactivity_current[1])}
                    </div>
                    <div>{biometricsData.physical_activity_data.inactive.inactivity_current[0]}</div>
                  </div>
                ) : '-'}
              </td>
            </tr>
            <tr>
              <td style={{ padding: '1rem', color: '#16284a', fontWeight: 'bold' }}>Sodium consumer status</td>
              <td style={{ padding: '1rem', color: '#16284a', textAlign: 'center' }}>
                {biometricsData?.ssq_data?.ssq_baseline !== null && biometricsData?.ssq_data?.ssq_baseline !== undefined ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      As of {formatDate(biometricsData.ssq_data.ssq_baseline_date)}
                    </div>
                    <div>{biometricsData.ssq_data.ssq_baseline.toFixed(1)}</div>
                  </div>
                ) : '-'}
              </td>
              <td style={{ padding: '1rem', color: '#16284a', textAlign: 'center' }}>
                {biometricsData?.ssq_data?.ssq_prior !== null && biometricsData?.ssq_data?.ssq_prior !== undefined ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      As of {formatDate(biometricsData.ssq_data.ssq_prior_date)}
                    </div>
                    <div>{biometricsData.ssq_data.ssq_prior.toFixed(1)}</div>
                  </div>
                ) : '-'}
              </td>
              <td style={{ padding: '1rem', color: '#16284a', textAlign: 'center' }}>
                {biometricsData?.ssq_data?.ssq_current !== null && biometricsData?.ssq_data?.ssq_current !== undefined ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      As of {formatDate(biometricsData.ssq_data.ssq_current_date)}
                    </div>
                    <div>{biometricsData.ssq_data.ssq_current.toFixed(1)}</div>
                  </div>
                ) : '-'}
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </section>
  );
};

export default BloodPressureTab;
