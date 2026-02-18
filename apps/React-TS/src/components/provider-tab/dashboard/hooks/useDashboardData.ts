import { useState, useEffect } from 'react';
import { staticDashboardData } from '../data/staticData';
import type { DashboardData } from '../data/staticData';

// TODO: Uncomment when backend is ready:
// import { providerTabApi } from '../../../../utils/api';

export const useDashboardData = (_temporaryLookupCode: string) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        // ─────────────────────────────────────────────────────────────
        // TODO: Replace with real API calls when backend is ready:
        //
        // const [bp, risk] = await Promise.all([
        //   providerTabApi.getBloodPressure(_temporaryLookupCode),
        //   providerTabApi.getStrokeRiskFactors(_temporaryLookupCode),
        // ]);
        // if (!cancelled) setData(transformApiData(bp, risk));
        // ─────────────────────────────────────────────────────────────

        // Simulate network latency with static data
        await new Promise(r => setTimeout(r, 200));
        if (!cancelled) setData(staticDashboardData);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load dashboard data');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => { cancelled = true; };
  }, [_temporaryLookupCode]);

  return { data, loading, error };
};
