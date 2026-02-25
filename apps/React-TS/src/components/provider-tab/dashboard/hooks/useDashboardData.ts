import { useState, useEffect } from 'react';
import { staticDashboardData } from '../data/staticData';
import type { DashboardData, Device, DeviceStatus, LabValue, MedicalHistoryItem, BadgeType, SubstanceUse } from '../data/staticData';
import { riskScoreApi } from '../../../../utils/actions/risk-score';
import { devicesApi } from '../../../../utils/actions/devices';

function mapCompliance(c: string | null | undefined): BadgeType | undefined {
  if (c === 'optimized') return 'optimized';
  if (c === 'not optimized') return 'non-optimized';
  if (c === 'partially optimized') return 'partially-optimized';
  return undefined;
}

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
        const [riskScoreResult, devicesResult] =
          await Promise.allSettled([
            riskScoreApi.getRiskScore(temporaryLookupCode),
            devicesApi.getDevices(temporaryLookupCode),
          ]);

        if (cancelled) return;

        const riskScoreData = riskScoreResult.status === 'fulfilled' ? riskScoreResult.value : null;
        const devicesData   = devicesResult.status   === 'fulfilled' ? devicesResult.value   : null;

        const metricsData      = riskScoreData?.metrics;
        const labApiData       = metricsData?.lab_data;
        const substanceApiData = metricsData?.substance_use_data;
        const srsData          = metricsData?.srs_response_data;
        const compliance       = srsData?.compliance;

        // ── Lab values ─────────────────────────────────────────────────────
        const labValues: LabValue[] = labApiData ? [
          { label: 'Hemoglobin A1C (HA1C)',          value: labApiData.hgA1c_value        != null ? String(labApiData.hgA1c_value)        : '—', unit: '%'     },
          { label: 'Low-Density Lipoprotein (LDL)',  value: labApiData.ldl_value          != null ? String(labApiData.ldl_value)          : '—', unit: 'mg/dL' },
          { label: 'High-Density Lipoprotein (HDL)', value: labApiData.hdl_value          != null ? String(labApiData.hdl_value)          : '—', unit: 'mg/dL' },
          { label: 'Triglycerides',                  value: srsData?.Triglycerides        != null ? String(srsData.Triglycerides)        : '—', unit: 'mg/dL' },
          { label: 'Creatinine',                     value: labApiData.creatintine_value  != null ? String(labApiData.creatintine_value)  : '—', unit: 'mg/dL' },
        ] : staticDashboardData.labValues;

        // ── Substance use ──────────────────────────────────────────────────
        const substanceUse: SubstanceUse | null = substanceApiData ? {
          tobaccoUse:         substanceApiData.tobacco_use             ?? null,
          tobaccoType:        substanceApiData.tobacco_type            ?? null,
          alcoholConsumption: substanceApiData.alcohol_consumption     ?? null,
          marijuanaUse:       substanceApiData.marijuana_use           ?? null,
          otherSubstanceUse:  substanceApiData.other_substance_use     ?? null,
          otherSubstanceType: substanceApiData.other_substance_checkbox ?? null,
        } : null;

        // ── Medical history ────────────────────────────────────────────────
        const medicalHistory: MedicalHistoryItem[] = (() => {
          if (!srsData) return staticDashboardData.medicalHistory;

          const items: MedicalHistoryItem[] = [];

          if (srsData.HasPreviousStroke) {
            items.push({ label: 'History of Stroke', value: srsData.NumberOfStrokes ?? 'Yes', badge: mapCompliance(compliance?.strokeCompliance) });
            if (srsData.LatestStrokeMechanism) {
              items.push({ label: 'Stroke Etiology', value: srsData.LatestStrokeMechanism });
            }
          }

          if (srsData.ScreenedForTIA) {
            items.push({ label: 'TIA', value: srsData.LikelihoodOfTIA ?? 'Yes', badge: mapCompliance(compliance?.tiaCompliance) });
          }

          if (srsData.HistoryOfAtrialFibrillation != null) {
            items.push({ label: 'Atrial Fibrillation', value: srsData.HistoryOfAtrialFibrillation ? 'Yes' : 'No', badge: mapCompliance(compliance?.atrialFibrillationCompliance) });
          }

          if (srsData.HistoryOfCHF != null) {
            items.push({ label: 'Congestive Heart Failure', value: srsData.HistoryOfCHF ? 'Yes' : 'No', badge: mapCompliance(compliance?.chfCompliance) });
          }

          if (srsData.HistoryOfCAD != null) {
            items.push({ label: 'Coronary Artery Disease', value: srsData.CADType ?? (srsData.HistoryOfCAD ? 'Yes' : 'No'), badge: mapCompliance(compliance?.cadCompliance) });
          }

          if (srsData.HistoryOfHyperlipidemia != null) {
            items.push({ label: 'Hyperlipidemia', value: srsData.HistoryOfHyperlipidemia ? 'Yes' : 'No' });
          }

          if (srsData.LDLLevel) {
            items.push({ label: 'LDL Level', value: srsData.LDLLevel, badge: mapCompliance(compliance?.ldlCompliance) });
          }

          if (srsData.HDLLevel) {
            items.push({ label: 'HDL Level', value: srsData.HDLLevel, badge: mapCompliance(compliance?.hdlCompliance) });
          }

          return items;
        })();

        // ── Physical activity ──────────────────────────────────────────────
        const patientSummary = {
          ...staticDashboardData.patientSummary,
          moderateVigorousActivity: srsData?.PhysicalActivityMinutes != null ? String(srsData.PhysicalActivityMinutes) : staticDashboardData.patientSummary.moderateVigorousActivity,
          physicalInactivity:       srsData?.PhysicalInactivityHours  != null ? String(srsData.PhysicalInactivityHours)  : staticDashboardData.patientSummary.physicalInactivity,
        };

        // ── Devices ────────────────────────────────────────────────────────
        const devices: Device[] = devicesData
          ? devicesData.devices.map(d => ({ name: d.name, status: d.status as DeviceStatus }))
          : staticDashboardData.devices;

        setData({
          ...staticDashboardData,
          riskScore:     riskScoreData?.risk_score     ?? staticDashboardData.riskScore,
          priorityScore: riskScoreData?.priority_score ?? staticDashboardData.priorityScore,
          labValues,
          substanceUse,
          medicalHistory,
          patientSummary,
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
