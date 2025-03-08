import { UserStatus } from '@/lib/supabase/types';

interface UserStatusIndicatorProps {
  status: UserStatus;
}

export function UserStatusIndicator({ status }: UserStatusIndicatorProps) {
  const getStatusColor = (status: UserStatus) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'inactive':
        return 'bg-red-500';
      case 'pending':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="flex items-center">
      <div className={`w-2 h-2 rounded-full ${getStatusColor(status)} mr-2`} />
      <span className="capitalize">{status}</span>
    </div>
  );
} 