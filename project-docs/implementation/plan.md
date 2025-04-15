# Evelina AI Implementation Plan

## 1. Project Structure Overview

### Existing File Structure
```
src/
├── ai_companion/
│   ├── core/               # Core functionality and base classes
│   │   ├── prompts.py      # System prompts and templates
│   │   └── ...
│   ├── graph/              # Conversation graph implementation
│   │   ├── nodes.py        # Node implementations for conversation flow
│   │   ├── edges.py        # Edge definitions connecting nodes
│   │   ├── graph.py        # Graph orchestration
│   │   ├── state.py        # Conversation state management
│   │   └── utils/          # Graph utilities
│   │       ├── chains.py   # LLM chain definitions
│   │       ├── helpers.py  # Helper functions
│   │       └── ...
│   ├── interfaces/         # External interface implementations
│   │   ├── whatsapp/       # WhatsApp integration
│   │   └── ...
│   ├── modules/            # Feature-specific modules
│   │   ├── image/          # Image generation and processing
│   │   ├── memory/         # Memory management
│   │   │   ├── long_term/  # Long-term memory storage
│   │   │   └── ...
│   │   ├── rag/            # Retrieval-Augmented Generation
│   │   │   ├── core/       # Core RAG functionality
│   │   │   │   ├── enhanced_retrieval.py  # Advanced retrieval methods
│   │   │   │   ├── monitoring.py          # RAG monitoring and metrics
│   │   │   │   ├── query_preprocessor.py  # Query enhancement
│   │   │   │   ├── rag_chain.py           # Main RAG chain implementation
│   │   │   │   ├── response_generation.py # Response creation
│   │   │   │   └── vector_store.py        # Vector database interface
│   │   │   └── ...
│   │   ├── schedules/      # Scheduling and context generation
│   │   ├── speech/         # Text-to-speech functionality
│   │   └── ...
│   ├── api/                # API endpoints and routing
│   ├── utils/              # Shared utilities and helpers
│   └── settings.py         # Application settings
├── tests/                  # Test suite
└── ...
```

### Required New Files/Directories

#### Healthcare-Specific Components
```
src/
├── ai_companion/
│   ├── modules/
│   │   ├── healthcare/             # New healthcare module
│   │   │   ├── oncology/           # Oncology-specific functionality
│   │   │   │   ├── knowledge.py    # Oncology knowledge management
│   │   │   │   ├── treatments.py   # Treatment information processing
│   │   │   │   ├── support.py      # Support services information
│   │   │   │   └── risk.py         # Risk assessment models
│   │   │   ├── medical_nlp/        # Medical NLP components
│   │   │   │   ├── entity.py       # Medical entity recognition
│   │   │   │   ├── terminology.py  # Medical terminology processing
│   │   │   │   └── validation.py   # Medical content validation
│   │   │   ├── integration/        # Healthcare system integration
│   │   │   │   ├── ehr.py          # Electronic Health Record integration
│   │   │   │   ├── appointments.py # Appointment scheduling
│   │   │   │   └── notifications.py # Healthcare provider notifications
│   │   │   └── compliance/         # Healthcare compliance
│   │   │       ├── privacy.py      # Privacy protection mechanisms
│   │   │       ├── audit.py        # Audit logging functionality
│   │   │       └── consent.py      # Consent management
│   │   └── ...
```

#### Voice Analysis Extensions
```
src/
├── ai_companion/
│   ├── modules/
│   │   ├── speech/
│   │   │   ├── analysis/           # Enhanced voice analysis
│   │   │   │   ├── emotion.py      # Emotion detection from voice
│   │   │   │   ├── stress.py       # Stress detection 
│   │   │   │   └── features.py     # Voice feature extraction
│   │   │   ├── lithuanian/         # Lithuanian-specific voice processing
│   │   │   │   ├── asr.py          # Lithuanian ASR optimizations
│   │   │   │   ├── tts.py          # Lithuanian TTS improvements
│   │   │   │   └── dialects.py     # Lithuanian dialect handling
│   │   │   └── ...
```

#### Proactive Systems
```
src/
├── ai_companion/
│   ├── modules/
│   │   ├── proactive/              # Proactive outreach systems
│   │   │   ├── scheduler.py        # Contact scheduling engine
│   │   │   ├── monitoring.py       # Patient monitoring system
│   │   │   ├── alerts.py           # Alert generation and management
│   │   │   └── optimization.py     # Contact optimization algorithms
│   │   └── ...
```

## 2. Interface Architecture

### Existing Interfaces
- **API Interface**: Current FastAPI implementation for backend services
- **WhatsApp Interface**: Integration with WhatsApp messaging 
- **Telegram Interface**: Integration with Telegram messaging
- **Chainlit Interface**: Interactive chat UI for development and testing
- **CLI Interface**: Command-line interface for testing and administration

### New Evelina AI Next.js Interface

#### Frontend Structure
```
frontend/
├── app/
│   ├── api/                      # API routes for server-side operations
│   ├── (auth)/                   # Authentication-related pages
│   │   ├── login/
│   │   ├── register/
│   │   └── profile/
│   ├── chat/                     # Chat interface pages
│   │   ├── page.tsx              # Main chat interface
│   │   ├── history/              # Chat history view
│   │   └── [sessionId]/          # Specific conversation view
│   ├── healthcare/               # Healthcare-specific pages
│   │   ├── resources/            # Medical information resources
│   │   ├── support/              # Support services directory
│   │   └── schedule/             # Scheduling interface
│   ├── onboarding/               # User onboarding flow
│   └── layout.tsx                # Main application layout
├── components/                   # Reusable React components
│   ├── ui/                       # General UI components
│   ├── chat/                     # Chat-specific components
│   │   ├── ChatBubble.tsx        # Message display component
│   │   ├── ChatInput.tsx         # User input component
│   │   ├── ChatContainer.tsx     # Chat container component
│   │   ├── VoiceInput.tsx        # Voice input component
│   │   └── ResponseIndicator.tsx # Response status indicator
│   ├── healthcare/               # Healthcare-specific components
│   │   ├── RiskAssessment.tsx    # Risk assessment display
│   │   ├── TreatmentInfo.tsx     # Treatment information component
│   │   └── SupportDirectory.tsx  # Support service listing
│   └── layout/                   # Layout components
├── lib/                          # Client-side utilities
│   ├── api.ts                    # API client
│   ├── hooks/                    # Custom React hooks
│   └── utils/                    # Utility functions
├── public/                       # Static assets
└── styles/                       # Global styles
```

#### Key Interface Features
1. **Conversational UI**
   - Real-time chat interface with message history
   - Voice input and output capabilities
   - Emotion and context-aware response formatting
   - Source attribution for healthcare information

2. **Healthcare Dashboard**
   - Treatment information visualization
   - Support service directory with contact information
   - Appointment scheduling and reminders
   - Medication and treatment adherence tracking

3. **Personalization**
   - User profile management
   - Preference settings for communication style
   - Notification management
   - Language settings (Lithuanian/English)

4. **Accessibility Features**
   - Screen reader compatibility
   - Voice-only interaction mode
   - High contrast and large text options
   - Simplified interface option for elderly users

## 3. Database Architecture (Supabase)

### User Management
```
Table: users
- id: uuid (primary key)
- created_at: timestamp
- email: string (unique)
- phone: string
- name: string
- preferred_language: string (default: 'lt')
- notification_preferences: jsonb
- healthcare_provider_id: uuid (foreign key)
- medical_record_id: string (external identifier)
- consent_status: jsonb
- last_login: timestamp
```

### Authentication Extensions
```
Table: user_verification
- id: uuid (primary key)
- user_id: uuid (foreign key)
- verification_type: string (enum: 'medical', 'caregiver', 'provider')
- verification_status: string (enum: 'pending', 'verified', 'rejected')
- verification_date: timestamp
- verification_data: jsonb
- verified_by: uuid (optional)
```

### Conversation Memory
```
Table: conversations
- id: uuid (primary key)
- user_id: uuid (foreign key)
- started_at: timestamp
- ended_at: timestamp (optional)
- summary: text
- context: jsonb
- metadata: jsonb

Table: messages
- id: uuid (primary key)
- conversation_id: uuid (foreign key)
- user_id: uuid (foreign key)
- content: text
- type: string (enum: 'user', 'assistant', 'system')
- created_at: timestamp
- metadata: jsonb (includes emotional state, sources, etc.)
- voice_url: string (optional)
- is_proactive: boolean (default: false)

Table: memories
- id: uuid (primary key)
- user_id: uuid (foreign key)
- content: text
- importance: float
- created_at: timestamp
- last_accessed: timestamp
- source_message_id: uuid (optional foreign key)
- category: string
- metadata: jsonb
```

### Healthcare Extensions
```
Table: health_records
- id: uuid (primary key)
- user_id: uuid (foreign key)
- record_type: string (enum: 'condition', 'treatment', 'medication', etc.)
- content: jsonb
- start_date: timestamp
- end_date: timestamp (optional)
- source: string
- verified: boolean
- last_updated: timestamp

Table: risk_assessments
- id: uuid (primary key)
- user_id: uuid (foreign key)
- assessment_date: timestamp
- risk_level: string (enum: 'low', 'medium', 'high', 'critical')
- risk_factors: jsonb
- source_conversation_id: uuid (optional foreign key)
- notification_sent: boolean
- notes: text
```

### Proactive Contact Management
```
Table: contact_schedule
- id: uuid (primary key)
- user_id: uuid (foreign key)
- scheduled_at: timestamp
- contact_type: string (enum: 'check_in', 'follow_up', 'reminder', 'alert')
- priority: integer
- status: string (enum: 'pending', 'completed', 'failed', 'rescheduled')
- completed_at: timestamp (optional)
- outcome: string
- notes: text

Table: contact_preferences
- id: uuid (primary key)
- user_id: uuid (foreign key)
- contact_method: string (enum: 'voice', 'message', 'email')
- day_preferences: jsonb (days of week)
- time_preferences: jsonb (time ranges)
- frequency_limit: integer (contacts per week)
- opt_out: boolean (default: false)
```

## 4. Deployment Architecture

The Evelina AI system is deployed using Azure Container Apps with virtual network integration. This architecture provides scalability, security, and reliability for the healthcare-focused AI companion.

### Azure Container Apps Configuration

```
Container Registry: evelinaai247acr.azurecr.io
Image: evelinaai247acr.azurecr.io/ai-companion:latest
Resource Group: evelina-ai-rg
Environment: evelina-env-vnet
```

### Network Configuration
- **Ingress**: External exposure with multiple port mappings
  - Main API port: 8000
  - Additional ports: 8080, 8090
- **Virtual Network Integration**: For secure communication with other Azure services

### Scaling Parameters
- **Minimum Replicas**: 1
- **Maximum Replicas**: 10
- **Auto-scaling**: Based on CPU and memory usage

### External Service Integration
1. **Qdrant Vector Database**
   - Cloud-hosted Qdrant instance for vector embeddings
   - Region: europe-west3-0 (GCP)
   - Authentication: API key

2. **Azure OpenAI Service**
   - Endpoint: ai-kestutis9429ai265477517797.openai.azure.com
   - Models:
     - GPT-4o for conversational AI
     - text-embedding-3-small for embeddings
   - API Version: 2024-08-01-preview

3. **Supabase**
   - PostgreSQL database for structured data and conversation memory
   - Authentication through service role API key
   - URL: aubulhjfeszmsheonmpy.supabase.co

### Environment Configuration
- Interface mode: "all" (supporting multiple interface types)
- Collection name: "Information" (for vector storage)
- Various API keys and authentication tokens for service access

### Security Measures
- Virtual network integration for secure communication
- Managed identities for Azure resources
- API keys stored as environment variables
- Service-to-service authentication

### Monitoring and Operations
- Container health checks
- Log integration with Azure Monitor
- Application insights for performance tracking
- Automatic scaling based on load metrics

## 5. Internal System Integration
1. **RAG to Healthcare Module**
   - Query routing to specialized medical knowledge retrieval
   - Healthcare information validation before response generation
   - Medical terminology enhancement in queries

2. **Voice Analysis to Emotional State**
   - Voice feature extraction feeding into emotional state detection
   - Emotional state informing conversation flow decisions
   - Sentiment trend analysis for risk assessment

3. **Memory to Proactive System**
   - Relevant memories triggering proactive contact scheduling
   - Conversation history informing contact optimization
   - Long-term relationship building through memory reinforcement

### External System Integration
1. **Healthcare System Integration**
   - Electronic Health Record (EHR) API connectivity
   - Appointment scheduling system integration
   - Secure patient data exchange protocols

2. **Support Service Directory**
   - Support organization database integration
   - Service availability and eligibility checking
   - Referral tracking system

3. **Emergency Services**
   - Crisis detection and escalation protocols
   - Emergency contact triggering system
   - Location-based emergency service routing

## 6. Implementation Phases

### Phase 1: Foundation (Weeks 1-4)
- Set up enhanced database schema in Supabase
- Create Next.js frontend application structure
- Implement basic chat interface with existing RAG system
- Establish user authentication and profile management

### Phase 2: Healthcare Knowledge (Weeks 5-8)
- Develop healthcare knowledge modules
- Implement medical NLP components
- Create healthcare content validation workflows
- Build healthcare information visualization components

### Phase 3: Voice & Emotion (Weeks 9-12)
- Enhance voice processing for Lithuanian
- Implement emotion detection from voice and text
- Create adaptive response generation based on emotional state
- Build voice-driven interface components

### Phase 4: Proactive Systems (Weeks 13-16)
- Develop contact scheduling engine
- Implement risk assessment framework
- Create notification and alert system
- Build proactive contact management interface

### Phase 5: Integration & Compliance (Weeks 17-20)
- Implement healthcare system integrations
- Establish compliance and privacy frameworks
- Create comprehensive security measures
- Develop audit and reporting systems

## 7. Success Criteria

### Technical Metrics
- System response time < 3 seconds
- Voice recognition accuracy > 95% for Lithuanian
- System availability > 99.9%
- Database query performance < 100ms average

### User Experience Metrics
- Conversation completion rate > 90%
- User satisfaction rating > 4.5/5
- Task success rate > 85%
- Return usage rate > 70%

### Healthcare Impact Metrics
- Information accuracy > 98%
- Successful navigation to support services > 85%
- Healthcare provider satisfaction > 4.2/5
- Self-reported patient well-being improvement > 20%
