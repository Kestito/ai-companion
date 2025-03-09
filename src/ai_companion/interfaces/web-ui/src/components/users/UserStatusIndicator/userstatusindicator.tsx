import { Chip } from '@mui/material'
import CircleIcon from '@mui/icons-material/Circle'
import { UserStatus } from '@/lib/supabase/types'

interface StatusProps {
  status: UserStatus
}

type StatusConfig = {
  label: string;
  color: 'success' | 'error' | 'warning';
}

export const UserStatusIndicator = ({ status }: StatusProps) => {
  const statusMap: Record<UserStatus, StatusConfig> = {
    active: { label: 'Active', color: 'success' },
    inactive: { label: 'Inactive', color: 'error' },
    pending: { label: 'Pending', color: 'warning' }
  }

  const statusConfig = statusMap[status]

  return (
    <Chip
      label={statusConfig.label}
      color={statusConfig.color}
      size="small"
      icon={<CircleIcon sx={{ fontSize: '0.75rem' }} />}
      sx={{ 
        borderRadius: 1,
        '& .MuiChip-icon': { pl: 0.5 },
        '& .MuiChip-label': { pr: 1 }
      }}
    />
  )
}