# Evelina AI Implementation Actions

This document outlines 10 incremental actions to implement the Evelina AI healthcare-focused system while preserving existing functionality. The actions prioritize user management, conversation interfaces in messaging platforms, and professional UI development first, followed by proactive features and voice capabilities.

RULE - For frotend use https://m3.material.io/develop/web . Use MUI components https://mui.com/material-ui/all-components/ 

Respect exiting stukture and do NO DELETE FUNCTIONALITY

## Action 1: Supabase Schema Enhancement

**Objective**: Extend the existing Supabase database schema to support healthcare-specific data with focus on users and conversations.

**Tasks**:
1. Create new database tables for  users, converstation , short memory , risk_assessments and support_interaction_logs in Supebase 
3. Enhance conversation and message tables with healthcare metadata
4. Set up appropriate indexes for optimized query performance
5. Configure row-level security policies for patient data protection
6. Integrate Intefaces like Chainlit, Telegram , whatcapp into User, converstation, short memory

**Expected Outcome**: Enhanced database schema that supports healthcare data while maintaining compatibility with existing conversation data.

**Timeline**: 1 week

## Action 2: Professional UI Development - Core Screens

**Objective**: Design and implement professional-looking UI for core system functions.

**Tasks**:
1. Design and implement login/authentication screen
   - Clean, medical-themed design with Evelina AI branding
   - Support for email/password and social authentication
   - Password recovery workflow
   - Remember me functionality
   - Multi-language support (Lithuanian/English)
   - authentication to use SUPARBASE

2. Develop main dashboard
   - Overview statistics (active users, conversation metrics, key health indicators)
   - Activity timeline showing recent interactions
   - Quick action buttons for common tasks
   - Notifications panel for alerts and system messages
   - Responsive design for desktop/tablet/mobile
   

3. Create user management interface
   - User listing with search, filter, and sorting capabilities
   - Detail view showing user profile, interaction history, and subsidy eligibility
   - Contact options (message, call, schedule) directly from user cards
   - Status indicators (active, requires follow-up, at risk)
   - User grouping by healthcare provider
   - Chat history have to have details what inteface was used

**Expected Outcome**: Professional-grade UI for core system functions that presents healthcare data in an organized, accessible manner.

**Timeline**: 2 weeks

## Action 3: Conversation Interface Enhancement

**Objective**: Optimize existing messaging interfaces (Telegram, WhatsApp) and create a unified conversation management system.

**Tasks**:
1. Enhance Telegram interface
   - Treatment information guidance
   - Legal/subsidy updates
   - Support service navigation
   - Inline buttons for common healthcare actions
   - Custom keyboards for structured data collection
   - Support for voice messages with transcription
   - use src\ai_companion\graph

2. Improve WhatsApp integration
   - Treatment information guidance
   - Legal/subsidy updates
   - Support service navigation
   - Automated appointment reminders
   - Structured healthcare questionnaires
   - Voice message support with transcription
   - Image sharing for symptom documentation
   - use src\ai_companion\graph

3. Develop conversation management dashboard
   - Real-time conversation monitoring
   - Agent takeover capabilities
   - Conversation tagging and categorization
   - Template response management
   - Conversation search and filtering

**Expected Outcome**: Enhanced messaging capabilities across platforms with a unified management interface.

**Timeline**: 2 weeks

## Action 4: Advanced UI Components - Analytics and Reporting

**Objective**: Develop sophisticated analytics and reporting interfaces for healthcare insights.

**Tasks**:
1. Design and implement analytics dashboard
   - Support utilization statistics
   - Subsidy program engagement
   - Legal document access patterns
   - Treatment info search trends
   - Usage patterns by time, location, and user type
   - System performance metrics

2. Create reporting interface
   - Scheduled and on-demand report generation
   - Custom report builder with drag-and-drop components
   - Export capabilities (PDF, Excel, CSV)
   - Report sharing and collaboration
   - Visualization library (charts, graphs, heatmaps)

3. Develop user detail screens
   - Comprehensive user profile view
   - Legal document access history
   - Conversation history with filtering
   - Risk assessment visualization
   - Treatment and medication tracking
   - Support service utilization

**Expected Outcome**: Comprehensive analytics and reporting capabilities that provide actionable healthcare insights.

**Timeline**: 2 weeks

## Action 5: Proactive Contact System

**Objective**: Implement the foundation for proactive patient contact and monitoring.

**Tasks**:
1. Develop scheduling engine for automated check-ins
2. Create contact preference management interface
3. Implement notification system for proactive outreach
4. Develop templates for different contact scenarios
5. Set up monitoring dashboard for contact effectiveness
6. Test it on telegram and whachapp .
7. In futere it will be calls and sms. NO NEEDED YET

**Expected Outcome**: Proactive contact capability that can be used alongside the existing reactive system.

**Timeline**: 2 weeks

## Action 6: Voice Analysis Enhancement

**Objective**: Extend the existing speech capabilities with emotion detection and Lithuanian language optimization.

**Tasks**:
1. Implement voice feature extraction pipeline for emotional analysis
2. Optimize Lithuanian ASR (Automatic Speech Recognition) accuracy
3. Create voice stress detection model
4. Develop adaptive voice response based on detected emotions
5. Set up voice analysis monitoring and improvement workflow

**Expected Outcome**: Enhanced voice processing capabilities that maintain current functionality while adding emotional intelligence.

**Timeline**: 2 weeks

## Action 7: Healthcare Dashboard

**Objective**: Create specialized healthcare visualization and management interfaces.

**Tasks**:
1. Develop treatment information visualization components
2. Create support service directory interface
3. Implement medication and treatment tracking views
4. Build appointment scheduling and reminder interface
5. Develop health status visualization dashboard

**Expected Outcome**: Healthcare-specific interface components that complement the existing conversation interfaces.

**Timeline**: 2 weeks

## Action 8: Risk Assessment Implementation

**Objective**: Develop the risk assessment framework for patient monitoring.

**Tasks**:
1. Implement standardized risk assessment models
2. Create risk factor tracking system
3. Develop alert generation for critical risk levels
4. Build risk trend visualization tools
5. Set up notification workflow for healthcare providers

**Expected Outcome**: Risk assessment capability that can identify and respond to patient risks.

**Timeline**: 2 weeks

## Action 9: Lithuanian Language Optimization

**Objective**: Enhance Lithuanian language support throughout the system.

**Tasks**:
1. Optimize Lithuanian text processing pipeline
2. Implement Lithuanian-specific medical terminology handling
3. Develop Lithuanian speech synthesis improvements
4. Create Lithuanian-specific UI components and localization
5. Set up Lithuanian language testing and validation framework

**Expected Outcome**: Improved Lithuanian language support across all interfaces.

**Timeline**: 1 week

## Action 10: External Service Integration

**Objective**: Implement integration points with external healthcare systems.

**Tasks**:
1. Develop secure EHR (Electronic Health Record) integration interfaces
2. Create appointment scheduling system connectors
3. Implement support service directory integrations
4. Build secure medical data exchange protocols
5. Develop emergency service notification system

**Expected Outcome**: External integration capabilities that connect Evelina AI to the broader healthcare ecosystem.

**Timeline**: 2 weeks

## UI Mockups for Key Screens

### Login Screen
```
┌────────────────────────────────────────────────┐
│                                                │
│                 [Evelina AI Logo]              │
│                                                │
│         Interaktyvios pacientų priežiūros      │
│            informacinė sistema                 │
│                                                │
│  ┌────────────────────────────────────────┐    │
│  │ Email                                  │    │
│  └────────────────────────────────────────┘    │
│                                                │
│  ┌────────────────────────────────────────┐    │
│  │ Password                     [👁]       │    │
│  └────────────────────────────────────────┘    │
│                                                │
│  [✓] Remember me         [Forgot Password?]    │
│                                                │
│  ┌────────────────────────────────────────┐    │
│  │              SIGN IN                   │    │
│  └────────────────────────────────────────┘    │
│                                                │
│  ────────────── or ──────────────              │
│                                                │
│  [Google Sign In]    [Microsoft Sign In]       │
│                                                │
│  Don't have an account? [Register]             │
│                                                │
│            [LT] | [EN]                         │
└────────────────────────────────────────────────┘
```

### Main Dashboard
```
┌────────────────────────────────────────────────────────────────────────────┐
│ Evelina AI [Logo]   🔍︎_______________   📋︎ Tasks   🔔︎ Notifications   👤︎ Admin ▼ │
├────────────┬───────────────────────────────────────────┬───────────────────┤
│            │                                           │                   │
│  NAVIGATION│              OVERVIEW                     │    NOTIFICATIONS  │
│            │                                           │                   │
│  📊 Dashboard│  ┌─────────┐  ┌─────────┐  ┌─────────┐    │  ⚠️ 3 patients    │
│            │  │         │  │         │  │         │    │  require follow-up│
│  👥 Users    │  │  148    │  │  27     │  │  92%    │    │                   │
│            │  │ Active  │  │ New     │  │ Response│    │  📅 5 upcoming     │
│  💬 Messages │  │ Users   │  │ Today   │  │ Rate    │    │  appointments     │
│            │  └─────────┘  └─────────┘  └─────────┘    │                   │
│  📈 Analytics│                                           │  ⚕️ New healthcare │
│            │  RECENT ACTIVITY                          │  update available  │
│  🗓️ Schedule │  ┌─────────────────────────────────────┐  │                   │
│            │  │ 09:45 • J. Smith: Medication reminder│  │  ┌─────────────┐  │
│  ⚕️ Healthcare│  │ 09:32 • A. Jonaitis: Message sent   │  │  │ VIEW ALL    │  │
│            │  │ 09:17 • L. Petrauskas: Risk assessed│  │  └─────────────┘  │
│  ⚙️ Settings │  │ 08:54 • New user registered        │  │                   │
│            │  │ 08:30 • System update completed     │  │   QUICK ACTIONS   │
│            │  └─────────────────────────────────────┘  │  ┌─────────────┐  │
│            │                                           │  │ New Message  │  │
│            │  USER DISTRIBUTION                        │  ├─────────────┤  │
│            │  ┌─────────────────────────────────────┐  │  │ Add Patient  │  │
│            │  │                                     │  │  ├─────────────┤  │
│            │  │  [Pie Chart: User Types]            │  │  │ Generate     │  │
│            │  │                                     │  │  │ Report       │  │
│            │  └─────────────────────────────────────┘  │  └─────────────┘  │
│            │                                           │                   │
└────────────┴───────────────────────────────────────────┴───────────────────┘
```

### User Management Screen
```
┌────────────────────────────────────────────────────────────────────────────┐
│ Evelina AI [Logo]   🔍︎_______________   📋︎ Tasks   🔔︎ Notifications   👤︎ Admin ▼ │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  USERS                                                [+ NEW USER]         │
│                                                                            │
│  🔍︎ Search users...   ⏬ Filter ▼   📂 Group by ▼   ⚙️ Columns ▼              │
│                                                                            │
│  ┌────────┬─────────────────┬────────┬──────────────┬─────────┬──────────┐ │
│  │ STATUS │ NAME            │ TYPE   │ LAST ACTIVE  │ RISK    │ ACTIONS  │ │
│  ├────────┼─────────────────┼────────┼──────────────┼─────────┼──────────┤ │
│  │ ●      │ Jonas Petraitis │ Patient│ Just now     │ ⚠️ Medium│ ···      │ │
│  ├────────┼─────────────────┼────────┼──────────────┼─────────┼──────────┤ │
│  │ ●      │ Marija Kazlausk │ Patient│ 5 min ago    │ 🟢 Low   │ ···      │ │
│  ├────────┼─────────────────┼────────┼──────────────┼─────────┼──────────┤ │
│  │ ○      │ Tomas Butkus    │ Patient│ Yesterday    │ 🔴 High  │ ···      │ │
│  ├────────┼─────────────────┼────────┼──────────────┼─────────┼──────────┤ │
│  │ ●      │ Ona Jankauskien │ Patient│ 10 min ago   │ 🟢 Low   │ ···      │ │
│  ├────────┼─────────────────┼────────┼──────────────┼─────────┼──────────┤ │
│  │ ●      │ Dr. A. Vaitiekū │ Doctor │ 1 hour ago   │ -       │ ···      │ │
│  ├────────┼─────────────────┼────────┼──────────────┼─────────┼──────────┤ │
│  │ ○      │ Eglė Rimkutė    │ Patient│ 3 days ago   │ 🟢 Low   │ ···      │ │
│  ├────────┼─────────────────┼────────┼──────────────┼─────────┼──────────┤ │
│  │ ●      │ Linas Paulauskas│ Patient│ 30 min ago   │ ⚠️ Medium│ ···      │ │
│  └────────┴─────────────────┴────────┴──────────────┴─────────┴──────────┘ │
│                                                                            │
│  Showing 7 of 148 users                                   < 1 2 3 ... 21 > │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### User Detail Screen
```
┌────────────────────────────────────────────────────────────────────────────┐
│ Evelina AI [Logo]   🔍︎_______________   📋︎ Tasks   🔔︎ Notifications   👤︎ Admin ▼ │
├────────────────────────────────────────────────────────────────────────────┤
│  < Back to Users                                                           │
│                                                                            │
│  Jonas Petraitis                                       ┌────────────────┐  │
│  ──────────────────                                    │                │  │
│                                     ⚠️ Medium Risk      │                │  │
│  📱 +370 612 34567                                      │    [Photo]     │  │
│  ✉️ jonas.petraitis@email.com                           │                │  │
│  🏠 Vilnius, Lithuania                                  │                │  │
│                                                        └────────────────┘  │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                 │
│  │ 💬 MESSAGE     │ │ 📞 CALL        │ │ 📅 SCHEDULE    │                 │
│  └────────────────┘ └────────────────┘ └────────────────┘                 │
│                                                                            │
│  ┌──────────┬─────────────┬──────────────┬───────────────┬───────────────┐│
│  │ OVERVIEW │ MEDICAL     │ CONVERSATIONS│ RISK FACTORS  │ APPOINTMENTS  ││
│  └──────────┴─────────────┴──────────────┴───────────────┴───────────────┘│
│                                                                            │
│  HEALTH SUMMARY                                                            │
│  ───────────────                                                           │
│  Diagnosis: Breast Cancer Stage II                                         │
│  Treatment: Chemotherapy (Cycle 3/6)                                       │
│  Last Assessment: 2023-08-15                                               │
│                                                                            │
│  RECENT CONVERSATIONS                                                      │
│  ─────────────────────                                                     │
│  Yesterday, 15:42 - Medication reminder (WhatsApp)                         │
│  2023-08-14, 10:15 - Symptom check (Telegram)                              │
│  2023-08-12, 09:30 - Appointment confirmation (WhatsApp)                   │
│                                                        [View All >]        │
│                                                                            │
│  UPCOMING APPOINTMENTS                                                     │
│  ─────────────────────                                                     │
│  2023-08-20, 14:00 - Oncology follow-up (Dr. Vaitiekūnas)                  │
│  2023-08-25, 11:30 - Chemotherapy session                                  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Conversation History Screen
```
┌────────────────────────────────────────────────────────────────────────────┐
│ Evelina AI [Logo]   🔍︎_______________   📋︎ Tasks   🔔︎ Notifications   👤︎ Admin ▼ │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  CONVERSATIONS                                                             │
│                                                                            │
│  Patient: Jonas Petraitis        Platform: Telegram       [EXPORT]         │
│                                                                            │
│  🔍︎ Search messages...   📅 Date: [2023-08-10 - 2023-08-17]   ⚙️ Filter ▼    │
│                                                                            │
│  2023-08-16 | Wednesday                                                    │
│  ──────────────────────                                                    │
│                                                                            │
│  [15:42] Evelina AI                                                        │
│  ┌──────────────────────────────────────────────────────┐                  │
│  │ Labas, Jonas! Primenu, kad šiandien reikia išgerti   │                  │
│  │ vaistus pagal gydytojo nurodytą grafiką. Ar jau      │                  │
│  │ išgėrei vaistus?                                     │                  │
│  └──────────────────────────────────────────────────────┘                  │
│                                                                            │
│  [15:45] Jonas Petraitis                                                   │
│  ┌──────────────────────────────────────────────────────┐                  │
│  │ Taip, ačiū už priminimą! Jau išgėriau.               │                  │
│  └──────────────────────────────────────────────────────┘                  │
│                                                                            │
│  [15:46] Evelina AI                                                        │
│  ┌──────────────────────────────────────────────────────┐                  │
│  │ Puiku! Kaip šiandien jaučiatės? Ar yra kokių         │                  │
│  │ simptomų, kurie jus neramina?                        │                  │
│  └──────────────────────────────────────────────────────┘                  │
│                                                                            │
│  [15:50] Jonas Petraitis                                                   │
│  ┌──────────────────────────────────────────────────────┐                  │
│  │ Jaučiuosi normaliai, bet truputį pykina po vaistų.   │                  │
│  │ Ar tai normalu?                                      │                  │
│  └──────────────────────────────────────────────────────┘                  │
│                                                                            │
│  [15:52] Evelina AI                                                        │
│  ┌──────────────────────────────────────────────────────┐                  │
│  │ Taip, pykinimas yra dažnas šalutinis poveikis po šių │                  │
│  │ vaistų. Jei pykinimas stiprus arba tęsiasi ilgiau    │                  │
│  │ nei 2 valandas, būtinai susisiekite su gydytoju.     │                  │
│  │                                                      │                  │
│  │ Štai keletas patarimų, kurie gali padėti:            │                  │
│  │ - Gerkite nedideliais gurkšneliais                   │                  │
│  │ - Venkite riebaus maisto                             │                  │
│  │ - Pailsėkite po valgio                               │                  │
│  └──────────────────────────────────────────────────────┘                  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Analytics Dashboard
```
┌────────────────────────────────────────────────────────────────────────────┐
│ Evelina AI [Logo]   🔍︎_______________   📋︎ Tasks   🔔︎ Notifications   👤︎ Admin ▼ │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ANALYTICS                                              [EXPORT] [SHARE]   │
│                                                                            │
│  Period: [Last 30 days ▼]   Compare to: [Previous period ▼]                │
│                                                                            │
│  USER ENGAGEMENT                    CONVERSATION METRICS                    │
│  ┌───────────────────────────┐      ┌───────────────────────────┐          │
│  │                           │      │                           │          │
│  │  [Line chart showing      │      │  [Bar chart showing       │          │
│  │   daily active users      │      │   message counts by       │          │
│  │   over time]              │      │   platform]               │          │
│  │                           │      │                           │          │
│  └───────────────────────────┘      └───────────────────────────┘          │
│                                                                            │
│  RISK DISTRIBUTION                  TOPIC ANALYSIS                         │
│  ┌───────────────────────────┐      ┌───────────────────────────┐          │
│  │                           │      │                           │          │
│  │  [Pie chart showing       │      │  [Word cloud showing      │          │
│  │   risk levels across      │      │   common conversation     │          │
│  │   patient population]     │      │   topics]                 │          │
│  │                           │      │                           │          │
│  └───────────────────────────┘      └───────────────────────────┘          │
│                                                                            │
│  SYSTEM PERFORMANCE                 HEALTH TRENDS                          │
│  ┌───────────────────────────┐      ┌───────────────────────────┐          │
│  │                           │      │                           │          │
│  │  [Area chart showing      │      │  [Heat map showing        │          │
│  │   response times and      │      │   symptom reporting       │          │
│  │   system load]            │      │   frequency]              │          │
│  │                           │      │                           │          │
│  └───────────────────────────┘      └───────────────────────────┘          │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## Implementation Order and Dependencies

The actions are designed to be implemented in sequence, with each building upon the previous:

1. **Supabase Schema Enhancement** - Foundation for all other actions
2. **Professional UI Development - Core Screens** - Creates the baseline user interface
3. **Conversation Interface Enhancement** - Optimizes Telegram and WhatsApp interfaces
4. **Advanced UI Components** - Adds analytics and reporting interfaces
5. **Proactive Contact System** - Builds on the enhanced conversation interfaces
6. **Voice Analysis Enhancement** - Adds emotional intelligence to voice interactions
7. **Healthcare Dashboard** - Creates specialized healthcare visualization tools
8. **Risk Assessment Implementation** - Adds patient risk monitoring capabilities
9. **Lithuanian Language Optimization** - Enhances language support across the system
10. **External Service Integration** - Connects with external healthcare systems

This sequence ensures that existing functionality is preserved while incrementally adding healthcare capabilities to the Evelina AI system, with a focus on user interface and conversation management first, followed by proactive features and voice capabilities. 