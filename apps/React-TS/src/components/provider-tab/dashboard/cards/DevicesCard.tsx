import React from 'react';
import { c } from '../theme';
import type { Device, DeviceStatus } from '../data/staticData';

interface Props {
  devices: Device[];
}

const statusStyle = (status: DeviceStatus): React.CSSProperties => {
  if (status === 'connected')    return { backgroundColor: c.greenBg, color: c.green,  border: `1px solid ${c.greenBd}` };
  if (status === 'unlinked')     return { backgroundColor: c.redBg,   color: c.red,    border: `1px solid ${c.redBd}`   };
  /* disconnected */              return { backgroundColor: 'rgba(100,116,139,0.15)', color: '#64748b', border: '1px solid rgba(100,116,139,0.3)' };
};

const statusLabel: Record<DeviceStatus, string> = {
  connected:    'Connected',
  unlinked:     'Unlinked',
  disconnected: 'Disconnected',
};

const DevicesCard: React.FC<Props> = ({ devices }) => {
  return (
    <div style={{
      backgroundColor: c.bgCard,
      border: `1px solid ${c.border}`,
      borderRadius: c.r,
      padding: '20px 24px',
      boxShadow: c.shadow,
    }}>
      <h3 style={{ margin: '0 0 16px', color: c.txt1, fontSize: '16px', fontWeight: 700, letterSpacing: '-0.01em' }}>
        Devices
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
        {devices.map((device, i) => {
          const isLast = i === devices.length - 1;
          return (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '9px 0',
                borderBottom: isLast ? undefined : `1px solid ${c.divider}`,
              }}
            >
              <span style={{ color: c.txt2, fontSize: '13px' }}>{device.name}</span>
              <span style={{
                ...statusStyle(device.status),
                padding: '2px 9px',
                borderRadius: c.rXs,
                fontSize: '11px',
                fontWeight: 700,
              }}>
                {statusLabel[device.status]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DevicesCard;
