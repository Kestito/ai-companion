import { Chip } from '@mui/material';
import { 
  WhatsApp as WhatsAppIcon,
  Telegram as TelegramIcon,
  Phone as PhoneIcon,
  QuestionMark as QuestionMarkIcon
} from '@mui/icons-material';
import { ReactElement } from 'react';

type PlatformType = 'whatsapp' | 'telegram' | 'phone' | 'unknown';

interface PatientPlatformIndicatorProps {
  platform?: string;
}

interface PlatformConfig {
  label: string;
  color: 'success' | 'info' | 'warning' | 'default' | 'primary' | 'secondary' | 'error';
  icon: ReactElement;
}

/**
 * Component to display patient communication platform with appropriate colors and icons
 * 
 * @param platform - The platform identifier (whatsapp, telegram, etc.)
 */
export function PatientPlatformIndicator({ platform }: PatientPlatformIndicatorProps) {
  // Normalize platform string
  const normalizedPlatform = platform?.toLowerCase() || 'unknown';
  
  // Determine platform type
  let platformType: PlatformType = 'unknown';
  if (normalizedPlatform.includes('whatsapp')) {
    platformType = 'whatsapp';
  } else if (normalizedPlatform.includes('telegram')) {
    platformType = 'telegram';
  } else if (normalizedPlatform.includes('phone') || normalizedPlatform.includes('call')) {
    platformType = 'phone';
  }
  
  // Configure display properties based on platform type
  const platformConfig: Record<PlatformType, PlatformConfig> = {
    whatsapp: {
      label: 'WhatsApp',
      color: 'success',
      icon: <WhatsAppIcon fontSize="small" />,
    },
    telegram: {
      label: 'Telegram',
      color: 'info',
      icon: <TelegramIcon fontSize="small" />,
    },
    phone: {
      label: 'Phone',
      color: 'warning',
      icon: <PhoneIcon fontSize="small" />,
    },
    unknown: {
      label: 'Unknown',
      color: 'default',
      icon: <QuestionMarkIcon fontSize="small" />,
    }
  };
  
  const config = platformConfig[platformType];
  
  return (
    <Chip
      icon={config.icon}
      label={config.label}
      color={config.color}
      size="small"
      variant="outlined"
    />
  );
} 