import { NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';
import { Database } from '@/types/database.types';
import OpenAI from 'openai';

// Initialize OpenAI client with proper error handling for missing API key
const getOpenAIClient = () => {
  const apiKey = process.env.OPENAI_API_KEY || process.env.NEXT_PUBLIC_AZURE_OPENAI_API_KEY;
  
  if (!apiKey) {
    console.warn('OpenAI API key is missing. Using mock response for development.');
    // Return null to indicate we should use a mock response
    return null;
  }
  
  return new OpenAI({
    apiKey
  });
};

// Mock response for development without API key
const getMockAssessmentResponse = () => {
  return {
    riskLevel: "medium",
    riskFactors: ["Inconsistent medication adherence", "Reported dizziness", "Limited mobility"],
    assessmentDetails: { "key observations": "Patient has expressed difficulty in medication adherence and reports dizziness after taking medication." },
    actionItems: [{"title": "Medication review", "description": "Schedule appointment with physician to review current medications and side effects."}],
    recommendedFollowUp: "2025-05-01T00:00:00Z"
  };
};

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
      // First try to get messages from the messages table
      const { data: conversationMessages, error: messagesError } = await supabase
        .from('messages')
        .select('*')
        .eq('patient_id', patientId)
        .in('conversation_id', conversationIds)
        .order('sent_at', { ascending: true });
      
      if (!messagesError && conversationMessages && conversationMessages.length > 0) {
        messages = conversationMessages;
      } else {
        // If no messages found in messages table, try conversation_details
        const { data: conversationDetails, error: detailsError } = await supabase
          .from('conversation_details')
          .select('*, conversations!inner(*)')
          .in('conversation_id', conversationIds)
          .order('sent_at', { ascending: true });
        
        if (!detailsError && conversationDetails && conversationDetails.length > 0) {
          // Map conversation_details to message format
          messages = conversationDetails.map(detail => ({
            id: detail.id,
            patient_id: patientId,
            conversation_id: detail.conversation_id,
            content: detail.message_content,
            message_type: detail.sender === 'patient' ? 'incoming' : 'outgoing',
            sent_at: detail.sent_at
          }));
        }
      }
    } else {
      // Try to get recent messages if no conversation IDs provided
      const { data: recentMessages, error: messagesError } = await supabase
        .from('messages')
        .select('*')
        .eq('patient_id', patientId)
        .order('sent_at', { ascending: false })
        .limit(100);
      
      if (!messagesError && recentMessages && recentMessages.length > 0) {
        messages = recentMessages.reverse();
      } else {
        // If no messages found in messages table, try to get from conversation_details
        // First get all conversations for this patient
        const { data: patientConversations, error: convError } = await supabase
          .from('conversations')
          .select('id')
          .eq('patient_id', patientId)
          .limit(10);
        
        if (!convError && patientConversations && patientConversations.length > 0) {
          const conversationIds = patientConversations.map(conv => conv.id);
          
          const { data: conversationDetails, error: detailsError } = await supabase
            .from('conversation_details')
            .select('*')
            .in('conversation_id', conversationIds)
            .order('sent_at', { ascending: false })
            .limit(100);
          
          if (!detailsError && conversationDetails && conversationDetails.length > 0) {
            // Map conversation_details to message format
            messages = conversationDetails.map(detail => ({
              id: detail.id,
              patient_id: patientId,
              conversation_id: detail.conversation_id,
              content: detail.message_content,
              message_type: detail.sender === 'patient' ? 'incoming' : 'outgoing',
              sent_at: detail.sent_at
            })).reverse();
          }
        }
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
    
    // Check for OpenAI client
    const openai = getOpenAIClient();
    let assessmentResult;
    
    if (openai) {
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
        model: process.env.CHAT_MODEL || 'o4-mini',
        response_format: { type: 'json_object' }
      });
      
      // Add null check for the content
      const content = completion.choices[0].message.content;
      if (!content) {
        return NextResponse.json({ error: 'AI did not generate a valid response' }, { status: 500 });
      }
      
      assessmentResult = JSON.parse(content);
    } else {
      // Use mock response for development
      assessmentResult = getMockAssessmentResponse();
    }
    
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