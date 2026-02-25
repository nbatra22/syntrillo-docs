import React, { useState } from 'react';
import { c } from './theme';
import { useDashboardData } from './hooks/useDashboardData';

import BloodPressureCard    from './cards/BloodPressureCard';
import BPGraphCard          from './cards/BPGraphCard';
import RiskScoreCards       from './cards/RiskScoreCards';
import MedicalHistoryCard   from './cards/MedicalHistoryCard';
import LabValuesCard        from './cards/LabValuesCard';
import SubstanceUseCard     from './cards/SubstanceUseCard';
import PatientSummaryCard   from './cards/PatientSummaryCard';
import DevicesCard          from './cards/DevicesCard';
import HRGraphCard          from './cards/HRGraphCard';
import BloodPressureModal   from './modals/BloodPressureModal';
import RiskScoreModal       from './modals/RiskScoreModal';

type ModalType = 'blood-pressure' | 'risk-score' | null;

interface Props {
  temporaryLookupCode: string;
}

const DataDashboard: React.FC<Props> = ({ temporaryLookupCode }) => {
  const { data, loading, error } = useDashboardData(temporaryLookupCode);
  const [openModal, setOpenModal] = useState<ModalType>(null);

  if (loading) {
    return (
      <div style={{
        backgroundColor: c.bgMain,
        minHeight: '400px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: c.r,
      }}>
        <div style={{ textAlign: 'center' }}>
          <div className="spinner" style={{
            width: '28px', height: '28px',
            border: `3px solid ${c.border}`,
            borderTopColor: c.accent,
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
            margin: '0 auto 12px',
          }} />
          <p style={{ color: c.txt3, fontSize: '13px', margin: 0 }}>Loading dashboard…</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{
        backgroundColor: c.redBg,
        border: `1px solid ${c.redBd}`,
        borderRadius: c.r,
        padding: '16px 20px',
        color: c.red,
        fontSize: '13px',
      }}>
        {error ?? 'Failed to load dashboard data.'}
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: c.bgMain, padding: '24px', borderRadius: c.r }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
        paddingBottom: '20px',
        borderBottom: `1px solid ${c.divider}`,
      }}>
        <h1 style={{
          margin: 0,
          color: c.txt1,
          fontSize: '22px',
          fontWeight: 800,
          letterSpacing: '-0.02em',
        }}>
          Data Dashboard
        </h1>
        <button style={{
          backgroundColor: 'transparent',
          border: `1px solid ${c.border}`,
          borderRadius: c.rSm,
          color: c.txt2,
          fontSize: '13px',
          fontWeight: 500,
          padding: '7px 14px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          transition: 'border-color 0.2s, color 0.2s',
        }}>
          + Update Data
        </button>
      </div>

      {/* Two-column grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '58fr 42fr',
        gap: '16px',
        alignItems: 'start',
      }}>
        {/* ── Left column ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <BloodPressureCard
            summary={data.bloodPressureSummary}
            onClick={() => setOpenModal('blood-pressure')}
          />
          <BPGraphCard data={data.bpTimeSeries} />
          <HRGraphCard heartRate={data.heartRate} data={data.hrTimeSeries} />

          {/* Bottom row: Devices + Physical Activity */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <DevicesCard       devices={data.devices}          />
            <PatientSummaryCard summary={data.patientSummary} />
          </div>
        </div>

        {/* ── Right column ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <RiskScoreCards
            riskScore={data.riskScore}
            priorityScore={data.priorityScore}
            onClick={() => setOpenModal('risk-score')}
          />
          <MedicalHistoryCard items={data.medicalHistory} />
          <LabValuesCard      values={data.labValues}     />
          <SubstanceUseCard substanceUse={data.substanceUse} />
        </div>
      </div>

      {/* Modals */}
      {openModal === 'blood-pressure' && (
        <BloodPressureModal
          detail={data.bloodPressureDetail}
          onClose={() => setOpenModal(null)}
        />
      )}
      {openModal === 'risk-score' && (
        <RiskScoreModal
          riskScore={data.riskScore}
          priorityScore={data.priorityScore}
          onClose={() => setOpenModal(null)}
        />
      )}
    </div>
  );
};

export default DataDashboard;
