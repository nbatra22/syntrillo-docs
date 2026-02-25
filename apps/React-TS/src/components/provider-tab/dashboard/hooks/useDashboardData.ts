import { useState, useEffect } from 'react';
import { staticDashboardData } from '../data/staticData';
import type { DashboardData, Device, DeviceStatus, LabValue } from '../data/staticData';
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
        const [riskScoreResult, labResult, devicesResult] =
          await Promise.allSettled([
            riskScoreApi.getRiskScore(temporaryLookupCode),
            riskScoreApi.getLabValues(temporaryLookupCode),
            devicesApi.getDevices(temporaryLookupCode),
          ]);

        if (cancelled) return;

        const riskScoreData = riskScoreResult.status === 'fulfilled' ? riskScoreResult.value : null;
        const labData       = labResult.status       === 'fulfilled' ? labResult.value       : null;
        const devicesData   = devicesResult.status   === 'fulfilled' ? devicesResult.value   : null;

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

        setData({
          ...staticDashboardData,
          riskScore:     riskScoreData?.risk_score     ?? staticDashboardData.riskScore,
          priorityScore: riskScoreData?.priority_score ?? staticDashboardData.priorityScore,
          labValues,
          devices,
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
