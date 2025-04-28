import { NextRequest, NextResponse } from 'next/server';

// Define message goal type
type MessageGoal = 'proactive-monitoring' | 'risky-patient' | 'medication-reminder' | 'appointment-reminder';

// Example templates for different message goals
const messageTemplates: Record<MessageGoal, string[]> = {
  'proactive-monitoring': [
    "How are you feeling today? Don't forget to log your symptoms in the app.",
    "Hope you're doing well! Quick reminder to take your medication and update your status.",
    "Checking in - have you experienced any new symptoms today? Please let us know so we can monitor your progress."
  ],
  'risky-patient': [
    "Important reminder: Please contact your doctor if you're experiencing any of the symptoms we discussed.",
    "Your well-being is important to us. Please confirm you've taken your medication today and are feeling okay.",
    "Our records show it's time for your check-in. Please respond with how you're feeling on a scale of 1-10."
  ],
  'medication-reminder': [
    "Reminder: It's time to take your prescribed medication. Please confirm when you've taken it.",
    "Don't forget to take your medication as scheduled. Your adherence to the treatment plan is crucial for your recovery.",
    "Medication reminder: Please take your pills as prescribed and let us know if you have any side effects."
  ],
  'appointment-reminder': [
    "Reminder: You have an appointment scheduled for tomorrow. Please confirm your attendance.",
    "Your medical appointment is coming up soon. Don't forget to prepare any questions you might have.",
    "Just a friendly reminder about your upcoming appointment. Let us know if you need to reschedule."
  ]
};

/**
 * POST handler for generating message content
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { messageGoal, patientContext } = body;
    
    if (!messageGoal) {
      return NextResponse.json({ error: 'Message goal is required' }, { status: 400 });
    }
    
    // Select a template based on message goal
    const templates = messageTemplates[messageGoal as MessageGoal] || messageTemplates['proactive-monitoring'];
    
    // Randomly select a template
    const randomIndex = Math.floor(Math.random() * templates.length);
    const messageContent = templates[randomIndex];
    
    // In a real implementation, this would use AI to generate personalized content
    // based on patient context, message goal, and medical history
    
    return NextResponse.json({
      messageContent,
      goal: messageGoal
    });
  } catch (error) {
    console.error('Error generating message content:', error);
    return NextResponse.json(
      { error: 'Failed to generate message content: ' + (error instanceof Error ? error.message : String(error)) },
      { status: 500 }
    );
  }
} 