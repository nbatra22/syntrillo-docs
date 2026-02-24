import { useState, useEffect } from 'react';
import { staticDashboardData } from '../data/staticData';
import type { DashboardData, Device, DeviceStatus, LabValue } from '../data/staticData';
import { bloodPressureApi } from '../../../../utils/actions/blood-pressure';
import { riskScoreApi } from '../../../../utils/actions/risk-score';
import { devicesApi } from '../../../../utils/actions/devices';

export const useDashboardData = (temporaryLookupCode: string) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [riskScoreResult, labResult, devicesResult, hrResult, metricsResult] =
          await Promise.allSettled([
            riskScoreApi.getRiskScore(temporaryLookupCode),
            riskScoreApi.getLabValues(temporaryLookupCode),
            devicesApi.getDevices(temporaryLookupCode),
            bloodPressureApi.getBPHR(temporaryLookupCode),
            bloodPressureApi.getBPMetrics(temporaryLookupCode),
          ]);

        if (cancelled) return;

        const riskScoreData = riskScoreResult.status === 'fulfilled' ? riskScoreResult.value : null;
        const labData       = labResult.status       === 'fulfilled' ? labResult.value       : null;
        const devicesData   = devicesResult.status   === 'fulfilled' ? devicesResult.value   : null;
        const hrData        = hrResult.status        === 'fulfilled' ? hrResult.value        : null;
        const metricsData   = metricsResult.status   === 'fulfilled' ? metricsResult.value   : null;

        // ── Transform lab values ───────────────────────────────────────
        const labValues: LabValue[] = labData ? [
          { label: 'Hemoglobin A1C (HA1C)',          value: labData.hemoglobin_a1c != null ? String(labData.hemoglobin_a1c) : '—', unit: '%'     },
          { label: 'Low-Density Lipoprotein (LDL)',  value: labData.ldl            != null ? String(labData.ldl)            : '—', unit: 'mg/dL' },
          { label: 'High-Density Lipoprotein (HDL)', value: labData.hdl            != null ? String(labData.hdl)            : '—', unit: 'mg/dL' },
          { label: 'Triglycerides',                  value: labData.triglycerides  != null ? String(labData.triglycerides)  : '—', unit: 'mg/dL' },
          { label: 'Creatinine',                     value: labData.creatinine     != null ? String(labData.creatinine)     : '—', unit: 'mg/dL' },
        ] : staticDashboardData.labValues;

        // ── Transform devices ──────────────────────────────────────────
        const devices: Device[] = devicesData
          ? devicesData.devices.map(d => ({ name: d.name, status: d.status as DeviceStatus }))
          : staticDashboardData.devices;

        // ── Heart rate ─────────────────────────────────────────────────
        const heartRate: DashboardData['heartRate'] = hrData ? {
          current:           hrData.average_rhr_trailing ?? staticDashboardData.heartRate.current,
          currentDate:       hrData.current_end_date     ?? staticDashboardData.heartRate.currentDate,
          avgResting:        hrData.average_rhr_baseline ?? staticDashboardData.heartRate.avgResting,
          baselineDateRange: hrData.baseline_start_date && hrData.baseline_end_date
            ? `${hrData.baseline_start_date} – ${hrData.baseline_end_date}`
            : staticDashboardData.heartRate.baselineDateRange,
        } : staticDashboardData.heartRate;

        // ── Patient summary (BMI) ──────────────────────────────────────
        const patientSummary: DashboardData['patientSummary'] = {
          ...staticDashboardData.patientSummary,
          bmi: metricsData?.bmi ?? staticDashboardData.patientSummary.bmi,
        };

        setData({
          ...staticDashboardData,
          riskScore:     riskScoreData?.risk_score     ?? staticDashboardData.riskScore,
          priorityScore: riskScoreData?.priority_score ?? staticDashboardData.priorityScore,
          labValues,
          devices,
          heartRate,
          patientSummary,
        });
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load dashboard data');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => { cancelled = true; };
  }, [temporaryLookupCode]);

  return { data, loading, error };
};
