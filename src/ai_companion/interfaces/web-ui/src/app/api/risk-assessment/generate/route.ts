import { NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';
import { Database } from '@/types/database.types';
import OpenAI from 'openai';

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// POST handler to generate a risk assessment from conversations
export async function POST(request: Request) {
  const supabase = createRouteHandlerClient<Database>({ cookies });
  
  try {
    const requestData = await request.json();
    const { patientId, conversationIds } = requestData;
    
    if (!patientId) {
      return NextResponse.json({ error: 'Patient ID is required' }, { status: 400 });
    }
    
    // Get patient data
    const { data: patientData, error: patientError } = await supabase
      .from('patients')
      .select('*')
      .eq('id', patientId)
      .single();
    
    if (patientError) {
      return NextResponse.json({ error: 'Patient not found' }, { status: 404 });
    }
    
    // Get conversation messages
    let messages = [];
    
    if (conversationIds && conversationIds.length > 0) {
      // Get messages from specific conversations
      const { data: conversationMessages, error: messagesError } = await supabase
        .from('messages')
        .select('*')
        .eq('patient_id', patientId)
        .in('conversation_id', conversationIds)
        .order('sent_at', { ascending: true });
      
      if (!messagesError) {
        messages = conversationMessages;
      }
    } else {
      // Get recent messages if no conversation IDs provided
      const { data: recentMessages, error: messagesError } = await supabase
        .from('messages')
        .select('*')
        .eq('patient_id', patientId)
        .order('sent_at', { ascending: false })
        .limit(100);
      
      if (!messagesError) {
        messages = recentMessages.reverse();
      }
    }
    
    if (messages.length === 0) {
      return NextResponse.json({ error: 'No messages found for analysis' }, { status: 404 });
    }
    
    // Prepare conversation text for analysis
    const conversationText = messages.map(msg => {
      const sender = msg.message_type === 'incoming' ? 'Patient' : 'System';
      return `${sender}: ${msg.content}`;
    }).join('\n');
    
    // Generate risk assessment using AI
    const prompt = `
      Analyze the following conversation with a patient and assess their risk level.
      
      Patient Information:
      - Name: ${patientData.first_name} ${patientData.last_name}
      - Current risk status: ${patientData.risk || 'Unknown'}
      
      Conversation:
      ${conversationText}
      
      Please provide a risk assessment with the following information:
      1. Overall risk level (low, medium, high)
      2. Key risk factors identified in the conversation
      3. Recommended actions
      4. Follow-up timeline
      
      Format your response as JSON with the following structure:
      {
        "riskLevel": "low|medium|high",
        "riskFactors": ["factor1", "factor2", ...],
        "assessmentDetails": { "key observations": "..." },
        "actionItems": [{"title": "action1", "description": "..."}],
        "recommendedFollowUp": "2023-12-01T00:00:00Z"
      }
    `;
    
    const completion = await openai.chat.completions.create({
      messages: [{ role: 'system', content: prompt }],
      model: process.env.CHAT_MODEL || 'gpt-4o',
      response_format: { type: 'json_object' }
    });
    
    const assessmentResult = JSON.parse(completion.choices[0].message.content);
    
    // Store the risk assessment in the database
    const { data: riskReport, error: insertError } = await supabase
      .from('patient_risk_reports')
      .insert({
        patient_id: patientId,
        risk_level: assessmentResult.riskLevel,
        risk_factors: assessmentResult.riskFactors,
        conversation_ids: conversationIds || [],
        assessment_details: assessmentResult.assessmentDetails,
        action_items: assessmentResult.actionItems,
        follow_up_date: assessmentResult.recommendedFollowUp,
        status: 'active'
      })
      .select()
      .single();
    
    if (insertError) {
      return NextResponse.json({ error: insertError.message }, { status: 500 });
    }
    
    // Update patient risk level if needed
    if (patientData.risk !== assessmentResult.riskLevel) {
      await supabase
        .from('patients')
        .update({ risk: assessmentResult.riskLevel })
        .eq('id', patientId);
    }
    
    return NextResponse.json({ data: riskReport });
  } catch (error) {
    console.error('Error generating risk assessment:', error);
    return NextResponse.json({ error: 'Failed to generate risk assessment' }, { status: 500 });
  }
} 