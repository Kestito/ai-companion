"use client";

import { PatientStatus } from '@/lib/supabase/types';
import { Tooltip } from '@mui/material';

interface PatientStatusIndicatorProps {
  status: PatientStatus;
  showLabel?: boolean;
}

/**
 * A component that visually indicates a patient's status
 * Displays a colored dot with an optional label
 * 
 * @param status - The patient's current status
 * @param showLabel - Whether to show a text label next to the indicator
 */
export function PatientStatusIndicator({ status, showLabel = true }: PatientStatusIndicatorProps) {
  const getStatusInfo = (status: PatientStatus) => {
    switch (status) {
      case 'stable':
        return { color: 'bg-blue-500', label: 'Stable', description: 'Patient is in stable condition' };
      case 'critical':
        return { color: 'bg-red-600', label: 'Critical', description: 'Patient requires immediate attention' };
      case 'discharged':
        return { color: 'bg-gray-400', label: 'Discharged', description: 'Patient has been discharged' };
      default:
        return { color: 'bg-gray-500', label: status, description: 'Unknown status' };
    }
  };

  const statusInfo = getStatusInfo(status);

  return (
    <Tooltip title={statusInfo.description} arrow placement="top">
      <div className="flex items-center">
        <div className={`w-3 h-3 rounded-full ${statusInfo.color} mr-2 flex-shrink-0`} />
        {showLabel && <span className="text-sm font-medium">{statusInfo.label}</span>}
      </div>
    </Tooltip>
  );
} 