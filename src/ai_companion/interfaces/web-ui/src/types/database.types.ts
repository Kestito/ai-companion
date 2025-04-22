export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      patient_risk_reports: {
        Row: {
          id: string
          patient_id: string
          risk_level: string
          risk_factors: string[] | null
          assessment_details: string | null
          action_items: string | null
          follow_up_date: string | null
          status: string
          created_at: string
          updated_at: string | null
        }
        Insert: {
          id?: string
          patient_id: string
          risk_level: string
          risk_factors?: string[] | null
          assessment_details?: string | null
          action_items?: string | null
          follow_up_date?: string | null
          status?: string
          created_at?: string
          updated_at?: string | null
        }
        Update: {
          id?: string
          patient_id?: string
          risk_level?: string
          risk_factors?: string[] | null
          assessment_details?: string | null
          action_items?: string | null
          follow_up_date?: string | null
          status?: string
          created_at?: string
          updated_at?: string | null
        }
      }
      patients: {
        Row: {
          id: string
          first_name: string
          last_name: string
          email: string | null
          phone: string | null
          date_of_birth: string | null
          medical_history: string | null
          created_at: string
          updated_at: string | null
        }
        Insert: {
          id?: string
          first_name: string
          last_name: string
          email?: string | null
          phone?: string | null
          date_of_birth?: string | null
          medical_history?: string | null
          created_at?: string
          updated_at?: string | null
        }
        Update: {
          id?: string
          first_name?: string
          last_name?: string
          email?: string | null
          phone?: string | null
          date_of_birth?: string | null
          medical_history?: string | null
          created_at?: string
          updated_at?: string | null
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
} 