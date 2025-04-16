import { NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';
import { Database } from '@/types/database.types';

// GET a specific risk assessment
export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const supabase = createRouteHandlerClient<Database>({ cookies });
  
  const { data, error } = await supabase
    .from('patient_risk_reports')
    .select('*, patients(first_name, last_name)')
    .eq('id', params.id)
    .single();
  
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 404 });
  }
  
  return NextResponse.json({ data });
}

// PUT to update a risk assessment
export async function PUT(
  request: Request,
  { params }: { params: { id: string } }
) {
  const supabase = createRouteHandlerClient<Database>({ cookies });
  
  try {
    const requestData = await request.json();
    
    const { data, error } = await supabase
      .from('patient_risk_reports')
      .update({
        risk_level: requestData.riskLevel,
        risk_factors: requestData.riskFactors,
        assessment_details: requestData.assessmentDetails,
        action_items: requestData.actionItems,
        follow_up_date: requestData.followUpDate,
        status: requestData.status,
        updated_at: new Date().toISOString()
      })
      .eq('id', params.id)
      .select()
      .single();
    
    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    return NextResponse.json({ data });
  } catch (error) {
    return NextResponse.json({ error: 'Invalid request data' }, { status: 400 });
  }
}

// DELETE a risk assessment
export async function DELETE(
  request: Request,
  { params }: { params: { id: string } }
) {
  const supabase = createRouteHandlerClient<Database>({ cookies });
  
  const { error } = await supabase
    .from('patient_risk_reports')
    .delete()
    .eq('id', params.id);
  
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  
  return NextResponse.json({ success: true });
} 