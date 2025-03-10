import { createClient } from '@/lib/supabase/server'
import { cookies } from 'next/headers'
import { PatientTable } from '@/components/patients/patienttable'
import { Patient } from '@/lib/supabase/types'

export default async function PatientsPage() {
  const cookieStore = cookies()
  const supabase = createClient(cookieStore)

  const { data: patients, error } = await supabase
    .from('patients')
    .select('*')

  if (error) {
    console.error('Error fetching patients:', error)
    return (
      <div className="p-4">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> Failed to load patients.</span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Patients</h1>
      <PatientTable patients={patients as Patient[]} />
    </div>
  )
} 