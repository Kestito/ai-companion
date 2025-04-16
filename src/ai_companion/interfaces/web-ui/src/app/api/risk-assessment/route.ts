import { NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';
import { Database } from '@/types/database.types';

// GET handler to retrieve risk assessments
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const patientId = searchParams.get('patientId');
  const limit = searchParams.get('limit') || '10';
  const offset = searchParams.get('offset') || '0';
  
  const supabase = createRouteHandlerClient<Database>({ cookies });
  
  let query = supabase
    .from('patient_risk_reports')
    .select('*, patients(first_name, last_name)')
    .order('assessment_date', { ascending: false })
    .limit(parseInt(limit as string))
    .range(parseInt(offset as string), parseInt(offset as string) + parseInt(limit as string) - 1);
  
  if (patientId) {
    query = query.eq('patient_id', patientId);
  }
  
  const { data, error } = await query;
  
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  
  return NextResponse.json({ data });
}

// POST handler to create a new risk assessment
export async function POST(request: Request) {
  const supabase = createRouteHandlerClient<Database>({ cookies });
  
  try {
    const requestData = await request.json();
    
    const { data, error } = await supabase
      .from('patient_risk_reports')
      .insert({
        patient_id: requestData.patientId,
        risk_level: requestData.riskLevel,
        risk_factors: requestData.riskFactors,
        conversation_ids: requestData.conversationIds,
        assessment_details: requestData.assessmentDetails,
        action_items: requestData.actionItems,
        follow_up_date: requestData.followUpDate,
        assessed_by: requestData.assessedBy,
        status: requestData.status || 'active'
      })
      .select()
      .single();
    
    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    return NextResponse.json({ data }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: 'Invalid request data' }, { status: 400 });
  }
} 