import React, { useState, useEffect } from 'react';
import { patientSidebarApi } from '../../utils/api';
import type { BloodPressureData, HeartRateData, BiometricsData } from '../../utils/api';

interface PatientDashboardProps {
  temporaryLookupCode: string;
}

const PatientDashboard: React.FC<PatientDashboardProps> = ({ temporaryLookupCode }) => {
  const [bpData, setBpData] = useState<BloodPressureData | null>(null);
  const [heartRateData, setHeartRateData] = useState<HeartRateData | null>(null);
  const [biometricsData, setBiometricsData] = useState<BiometricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [bpLoading, setBpLoading] = useState(true);
  const [biometricsLoading, setBiometricsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (temporaryLookupCode) {
      fetchData();
    }
  }, [temporaryLookupCode]);

  const fetchData = async () => {
    setLoading(true);
    setBpLoading(true);
    setBiometricsLoading(true);
    setError('');

    try {
      // Fetch blood pressure data
      const bloodPressureData = await patientSidebarApi.getBloodPressure(temporaryLookupCode);
      setBpData(bloodPressureData);
      setBpLoading(false);

      // Fetch heart rate and biometrics data
      const [hrData, bioData] = await Promise.all([
        patientSidebarApi.getHeartRate(temporaryLookupCode),
        patientSidebarApi.getBiometrics(temporaryLookupCode),
      ]);
      setHeartRateData(hrData);
      setBiometricsData(bioData);
      setBiometricsLoading(false);
    } catch (err) {
      console.error('Error fetching patient data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch patient data');
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

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <div className="spinner" style={{
          width: '2rem',
          height: '2rem',
          border: '4px solid white',
          borderTopColor: '#3b82f6',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '1rem', backgroundColor: '#fee2e2', color: '#dc2626', borderRadius: '0.375rem' }}>
        Error: {error}
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem 10%', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <h1 style={{ fontWeight: 'bold', fontSize: 'x-large', margin: 0, color: '#16284a' }}>
        Syntrillo Dashboard
      </h1>

      {/* Stroke Risk Factor Analysis Section */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        <div>
          <h2 style={{ fontWeight: 'bold', fontSize: 'large', margin: 0, color: '#16284a' }}>
            Stroke Risk Factor Analysis
          </h2>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ color: '#16284a', fontSize: '16px' }}>
              Our clinicians have reviewed your health information feel that you are at an overall low risk of stroke. Given available data, they estimate your one-year risk of stroke and heart attack is most likely around 1% although it may be as high as 2% per year depending on the interaction of your unique risk factors.
            </p>
            <p style={{ color: '#16284a', fontSize: '16px' }}>
              The following risk factors or conditions are contributing the most to your current risk of stroke. Addressing these risk factors can help lower your overall risk of stroke.
            </p>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#e5e7eb', fontWeight: 'bold', borderRadius: '0.375rem' }}>
                <th style={{ padding: '0.5rem', textAlign: 'left', width: '30%' }}>Risk Factor</th>
                <th style={{ padding: '0.5rem', textAlign: 'left' }}>Comments from your doctor</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ padding: '0.5rem' }}>Hypertension</td>
                <td style={{ padding: '0.5rem' }}>Our clinicians estimate that the risk factor most contributing to your risk of stroke and heart disease is your average systolic blood pressure which was 133. According to this estimate, your risk of stroke is increased by 35% compared to an optimal value (average systolic blood pressure &lt; 125). Your average systolic blood pressure also increases your risk of dementia and kidney disease.</td>
              </tr>
              <tr>
                <td style={{ padding: '0.5rem' }}>Hyperlipidemia (LDL and Triglycerides)</td>
                <td style={{ padding: '0.5rem' }}>Our clinicians estimate the second most important risk factor contributing to your risk of stroke and heart disease is your hyperlipidemia. According to this estimate, your risk of stroke is increased by 25% compared to the optimal levels. A LDL level &gt; 100 is considered elevated although the goal LDL level in patients with known atherosclerosis is less than 70. A triglyceride level greater than 150 is considered elevated.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Blood Pressure Analysis Section */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        <div>
          <h2 style={{ fontWeight: 'bold', fontSize: 'large', margin: 0, color: '#16284a' }}>
            Blood Pressure Analysis
          </h2>
          <p style={{ color: '#6b7280', fontSize: 'small', marginBottom: 0, marginTop: '0.5rem' }}>
            The data below is calculated using your most recent two weeks of measurements.
          </p>
        </div>
        <div>
          {bpData?.data && !bpLoading ? (
            <>
              {/* BP Summary Container */}
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
                  <h3 style={{ fontSize: '0.875rem', fontWeight: 500, color: '#6b7280', margin: 0 }}>
                    Status
                  </h3>
                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
                    <span style={{
                      fontSize: '1.25rem',
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
                  <h3 style={{ fontSize: '0.875rem', fontWeight: 500, color: '#6b7280', margin: 0 }}>
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
                  <h3 style={{ fontSize: '0.875rem', fontWeight: 500, color: '#6b7280', margin: 0 }}>
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

              {/* BP Footnotes */}
              <ul style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#6b7280', padding: '1rem', listStyleType: 'disc' }}>
                <li style={{ marginLeft: '0.5rem' }}>
                  Blood pressure measurements are captured as two numbers, both measured in millimeters of mercury (mmHg).
                </li>
                <li style={{ marginLeft: '0.5rem' }}>
                  <span style={{ fontWeight: 'bold' }}>Systolic Blood Pressure (SBP)</span>, the top number, measures the pressure in your arteries when your heart beats and pumps blood.
                </li>
                <li style={{ marginLeft: '0.5rem' }}>
                  <span style={{ fontWeight: 'bold' }}>Diastolic Blood Pressure (DBP)</span>, the bottom number, measures the pressure in your arteries when your heart rests between beats.
                </li>
                <li style={{ marginLeft: '0.5rem' }}>
                  <span style={{ fontWeight: 'bold' }}>Peak SBP</span> and <span style={{ fontWeight: 'bold' }}>Low SBP</span> represent the average of your three highest and lowest systolic blood pressure readings.
                </li>
                <li style={{ marginLeft: '0.5rem' }}>
                  <span style={{ fontWeight: 'bold' }}>Symptomatic Hypotensive Episodes</span> are blood pressure readings where your SBP is below 90 mmHg accompanied by symptoms like dizziness or fainting.
                </li>
              </ul>
            </>
          ) : (
            <p>No blood pressure data available.</p>
          )}
        </div>
      </section>

      {/* Biometrics Section */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        <div>
          <h2 style={{ fontWeight: 'bold', fontSize: 'large', margin: 0, color: '#16284a' }}>
            Biometrics
          </h2>
          <p style={{ color: '#6b7280', fontSize: 'small', marginBottom: 0, marginTop: '0.5rem' }}>
            Additional health metrics listed below are sourced from your connected devices and/or manually logged.
          </p>
        </div>
        <div>
          {biometricsLoading ? (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              Retrieving metrics...
            </div>
          ) : (
            <table style={{
              display: 'block',
              width: '100%',
              borderCollapse: 'collapse',
              marginBottom: '1rem',
              backgroundColor: 'white'
            }}>
              <thead>
                <tr style={{ borderBottom: '1px solid black', width: '100%' }}>
                  <td style={{
                    padding: '1rem',
                    textAlign: 'left',
                    verticalAlign: 'top',
                    border: '1px solid black',
                    fontWeight: 'bold',
                    color: '#374151',
                    backgroundColor: '#f9fafb',
                    borderRight: '1px solid black'
                  }}></td>
                  <td style={{
                    padding: '1rem',
                    border: '1px solid black',
                    width: '20%',
                    fontWeight: 'bold',
                    color: '#374151',
                    textAlign: 'center',
                    backgroundColor: '#f9fafb',
                    borderRight: '1px solid black'
                  }}>Baseline</td>
                  <td style={{
                    padding: '1rem',
                    border: '1px solid black',
                    width: '20%',
                    fontWeight: 'bold',
                    color: '#374151',
                    textAlign: 'center',
                    backgroundColor: '#f9fafb',
                    borderRight: '1px solid black'
                  }}>Prior</td>
                  <td style={{
                    padding: '1rem',
                    border: '1px solid black',
                    width: '20%',
                    fontWeight: 'bold',
                    color: '#374151',
                    textAlign: 'center',
                    backgroundColor: '#f9fafb'
                  }}>Latest</td>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: '1px solid black' }}>
                  <td style={{
                    padding: '1rem',
                    textAlign: 'left',
                    verticalAlign: 'top',
                    border: '1px solid black',
                    fontWeight: 'bold',
                    color: '#374151',
                    width: '40%',
                    backgroundColor: '#f9fafb',
                    borderRight: '1px solid black'
                  }}><strong>Avg. Resting Heart Rate (bpm)</strong></td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {heartRateData?.average_rhr_baseline ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          From {formatDate(heartRateData.baseline_start_date)} - {formatDate(heartRateData.baseline_end_date)}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{heartRateData.average_rhr_baseline.toFixed(1)}</div>
                      </>
                    ) : '-'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {heartRateData?.average_rhr_prior ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          From {formatDate(heartRateData.prior_start_date)} - {formatDate(heartRateData.prior_end_date)}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{heartRateData.average_rhr_prior.toFixed(1)}</div>
                      </>
                    ) : '-'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {heartRateData?.average_rhr_trailing ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          From {formatDate(heartRateData.current_start_date)} - {formatDate(heartRateData.current_end_date)}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{heartRateData.average_rhr_trailing.toFixed(1)}</div>
                      </>
                    ) : '-'}
                  </td>
                </tr>
                <tr style={{ borderBottom: '1px solid black' }}>
                  <td style={{
                    padding: '1rem',
                    textAlign: 'left',
                    verticalAlign: 'top',
                    border: '1px solid black',
                    fontWeight: 'bold',
                    color: '#374151',
                    width: '40%',
                    backgroundColor: '#f9fafb',
                    borderRight: '1px solid black'
                  }}><strong>Body mass index (kg/m²)</strong></td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {biometricsData?.bmi_data?.bmi_baseline?.bmi ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          As of {formatDate(biometricsData.bmi_data.bmi_baseline.date)}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{biometricsData.bmi_data.bmi_baseline.bmi.toFixed(1)}</div>
                      </>
                    ) : '-'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {biometricsData?.bmi_data?.bmi_prior?.bmi ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          As of {formatDate(biometricsData.bmi_data.bmi_prior.date)}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{biometricsData.bmi_data.bmi_prior.bmi.toFixed(1)}</div>
                      </>
                    ) : '-'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {biometricsData?.bmi_data?.bmi_current?.bmi ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          As of {formatDate(biometricsData.bmi_data.bmi_current.date)}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{biometricsData.bmi_data.bmi_current.bmi.toFixed(1)}</div>
                      </>
                    ) : '-'}
                  </td>
                </tr>
                <tr style={{ borderBottom: '1px solid black' }}>
                  <td style={{
                    padding: '1rem',
                    textAlign: 'left',
                    verticalAlign: 'top',
                    border: '1px solid black',
                    fontWeight: 'bold',
                    color: '#374151',
                    width: '40%',
                    backgroundColor: '#f9fafb',
                    borderRight: '1px solid black'
                  }}><strong>Physical Activity (min/week)</strong></td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {biometricsData?.physical_activity_data?.active?.activity_baseline?.[0] ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          As of {formatDate(biometricsData.physical_activity_data.active.activity_baseline[1])}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{biometricsData.physical_activity_data.active.activity_baseline[0]}</div>
                      </>
                    ) : '-'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {biometricsData?.physical_activity_data?.active?.activity_prior?.[0] ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          As of {formatDate(biometricsData.physical_activity_data.active.activity_prior[1])}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{biometricsData.physical_activity_data.active.activity_prior[0]}</div>
                      </>
                    ) : '-'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {biometricsData?.physical_activity_data?.active?.activity_current?.[0] ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          As of {formatDate(biometricsData.physical_activity_data.active.activity_current[1])}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{biometricsData.physical_activity_data.active.activity_current[0]}</div>
                      </>
                    ) : '-'}
                  </td>
                </tr>
                <tr style={{ borderBottom: '1px solid black' }}>
                  <td style={{
                    padding: '1rem',
                    textAlign: 'left',
                    verticalAlign: 'top',
                    border: '1px solid black',
                    fontWeight: 'bold',
                    color: '#374151',
                    width: '40%',
                    backgroundColor: '#f9fafb',
                    borderRight: '1px solid black'
                  }}><strong>Physical Inactivity (hours/day)</strong></td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {biometricsData?.physical_activity_data?.inactive?.inactivity_baseline?.[0] ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          As of {formatDate(biometricsData.physical_activity_data.inactive.inactivity_baseline[1])}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{biometricsData.physical_activity_data.inactive.inactivity_baseline[0]}</div>
                      </>
                    ) : '-'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {biometricsData?.physical_activity_data?.inactive?.inactivity_prior?.[0] ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          As of {formatDate(biometricsData.physical_activity_data.inactive.inactivity_prior[1])}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{biometricsData.physical_activity_data.inactive.inactivity_prior[0]}</div>
                      </>
                    ) : '-'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {biometricsData?.physical_activity_data?.inactive?.inactivity_current?.[0] ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          As of {formatDate(biometricsData.physical_activity_data.inactive.inactivity_current[1])}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{biometricsData.physical_activity_data.inactive.inactivity_current[0]}</div>
                      </>
                    ) : '-'}
                  </td>
                </tr>
                <tr style={{ borderBottom: '1px solid black' }}>
                  <td style={{
                    padding: '1rem',
                    textAlign: 'left',
                    verticalAlign: 'top',
                    border: '1px solid black',
                    fontWeight: 'bold',
                    color: '#374151',
                    width: '40%',
                    backgroundColor: '#f9fafb',
                    borderRight: '1px solid black'
                  }}><strong>Sodium consumer status</strong></td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {biometricsData?.ssq_data?.ssq_baseline !== null && biometricsData?.ssq_data?.ssq_baseline !== undefined ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          As of {formatDate(biometricsData.ssq_data.ssq_baseline_date)}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{biometricsData.ssq_data.ssq_baseline.toFixed(1)}</div>
                      </>
                    ) : '-'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {biometricsData?.ssq_data?.ssq_prior !== null && biometricsData?.ssq_data?.ssq_prior !== undefined ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          As of {formatDate(biometricsData.ssq_data.ssq_prior_date)}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{biometricsData.ssq_data.ssq_prior.toFixed(1)}</div>
                      </>
                    ) : '-'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center', border: '1px solid black', color: '#374151' }}>
                    {biometricsData?.ssq_data?.ssq_current !== null && biometricsData?.ssq_data?.ssq_current !== undefined ? (
                      <>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>
                          As of {formatDate(biometricsData.ssq_data.ssq_current_date)}:
                        </h4>
                        <div style={{ fontSize: '16px' }}>{biometricsData.ssq_data.ssq_current.toFixed(1)}</div>
                      </>
                    ) : '-'}
                  </td>
                </tr>
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
};

export default PatientDashboard;
