'use client';

import RealTimeUserTable from '@/components/RealTimeUserTable';
import { TableAccessMethod, getTableName } from '@/lib/supabase/client';

export default function UsersPage() {
  // The users table is in the auth schema, not evelinaai
  const usersTable = 'auth.users';

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-2xl font-bold mb-5">Users</h1>
      <RealTimeUserTable tableName={usersTable} />
    </div>
  );
} 