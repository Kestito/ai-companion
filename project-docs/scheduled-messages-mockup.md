# Scheduled Messages UI Mockup

## Overview
This document provides a visual description of the enhanced Scheduled Messages UI. It includes mockups for the main view and the new message creation workflow.

## Main View

```
+----------------------------------------------------------------------+
|                                                                      |
| Home / Scheduled Messages                                            |
|                                                                      |
| Scheduled Messages                                 [+ New Message]   |
| Manage scheduled messages and patient communication                  |
|                                                                      |
| [Success] Scheduler is running. Last check: May 15, 2023 10:30 AM    |
| Pending messages: 5                                      [Refresh]   |
|                                                                      |
| +------------------------------------------------------------------+ |
| | [Search messages or patients...]           [Filters] [Refresh]   | |
| |                                                                  | |
| | +------------------------------------------------------+         | |
| | | Status:    [All Statuses ▼]                          |         | |
| | | Platform:  [All Platforms ▼]                         |         | |
| | | From Date: [05/01/2023]       To Date: [05/31/2023]  |         | |
| | |                                                      |         | |
| | |                                [Clear All] [Apply]   |         | |
| | +------------------------------------------------------+         | |
| +------------------------------------------------------------------+ |
|                                                                      |
| [All Messages] [Pending] [Sent] [Failed] [Cancelled]                 |
|                                                                      |
| +------------------------------------------------------------------+ |
| | Patient | Scheduled Time | Message      | Platform | Status      | |
| |--------------------------------------------------------------    | |
| | John D. | May 16, 2023   | Appointment  | Telegram | [PENDING]   | |
| |         | 10:30 AM       | reminder...  |          | [▶][✕][⋮]   | |
| |--------------------------------------------------------------    | |
| | Mary S. | May 15, 2023   | Thank you    | Email    | [SENT]      | |
| |         | 2:15 PM        | for your...  |          | [⋮]         | |
| |--------------------------------------------------------------    | |
| | Robert  | May 14, 2023   | Medication   | SMS      | [FAILED]    | |
| | Johnson | 9:00 AM        | reminder...  |          | [↻][⋮]      | |
| |--------------------------------------------------------------    | |
| | Emma W. | Daily          | Daily check- | Telegram | [PENDING]   | |
| |         | 8:00 AM        | in message   |          | [▶][✕][⋮]   | |
| +------------------------------------------------------------------+ |
|                                                                      |
| Showing 4 of 24 messages                         [< 1 2 3 ... >]    |
|                                                                      |
+----------------------------------------------------------------------+
```

## New Message Dialog - Step-by-Step Wizard

### Step 1: Select Patient

```
+------------------------------------------------------+
|                                                      |
| New Scheduled Message                          [×]   |
|                                                      |
| [Patient] → [Message] → [Schedule] → [Review]        |
|                                                      |
| Select Patient                                       |
|                                                      |
| [Search or select patient...]                        |
|                                                      |
| Communication Channel                                |
|                                                      |
| +---------------+ +---------------+ +---------------+ |
| |   Telegram    | |     Email     | |      SMS      | |
| |               | |               | |               | |
| |  Available    | |  Available    | |  Not available| |
| +---------------+ +---------------+ +---------------+ |
|                                                      |
|                                                      |
|                                [Cancel] [Next >]     |
+------------------------------------------------------+
```

### Step 2: Message Content

```
+------------------------------------------------------+
|                                                      |
| New Scheduled Message                          [×]   |
|                                                      |
| [Patient] → [Message] → [Schedule] → [Review]        |
|                                                      |
| Message Content                                      |
|                                                      |
| +--------------------------------------------+       |
| | Hi John,                                   |       |
| |                                            |       |
| | This is a reminder about your appointment  |       |
| | tomorrow at 10:30 AM with Dr. Smith.       |       |
| |                                            |       |
| | Please reply to confirm.                   |       |
| |                                            |       |
| | Thank you!                                 |       |
| +--------------------------------------------+       |
|                                                      |
| Character count: 123                                 |
|                                                      |
| [Use Template ▼]                                     |
|                                                      |
|                            [< Back] [Next >]         |
+------------------------------------------------------+
```

### Step 3: Schedule Options

```
+------------------------------------------------------+
|                                                      |
| New Scheduled Message                          [×]   |
|                                                      |
| [Patient] → [Message] → [Schedule] → [Review]        |
|                                                      |
| Schedule Options                                     |
|                                                      |
| Date: [05/16/2023]      Time: [10:30 AM]             |
|                                                      |
| [Send in 2 minutes]                                  |
|                                                      |
| [✓] Recurring message                                |
|                                                      |
| Recurrence pattern: [Weekly ▼]                       |
|                                                      |
| Days:                                                |
| [✓] Mon [✓] Tue [✓] Wed [✓] Thu [✓] Fri [ ] Sat [ ] Sun |
|                                                      |
| End date: [06/16/2023]                               |
|                                                      |
| Priority: [Normal ▼]                                 |
|                                                      |
| Delivery window: [0] minutes                         |
|                                                      |
|                            [< Back] [Next >]         |
+------------------------------------------------------+
```

### Step 4: Review

```
+------------------------------------------------------+
|                                                      |
| New Scheduled Message                          [×]   |
|                                                      |
| [Patient] → [Message] → [Schedule] → [Review]        |
|                                                      |
| Review Message                                       |
|                                                      |
| Patient: John Doe (Telegram: @johndoe)               |
| Platform: Telegram                                   |
|                                                      |
| Schedule: Weekly on Mon, Tue, Wed, Thu, Fri          |
| Starting: May 16, 2023 at 10:30 AM                   |
| Ending: June 16, 2023                                |
| Priority: Normal                                     |
|                                                      |
| Message:                                             |
| Hi John,                                             |
|                                                      |
| This is a reminder about your appointment            |
| tomorrow at 10:30 AM with Dr. Smith.                 |
|                                                      |
| Please reply to confirm.                             |
|                                                      |
| Thank you!                                           |
|                                                      |
|                      [< Back] [Schedule Message]     |
+------------------------------------------------------+
```

## Message Details Dialog

```
+------------------------------------------------------+
|                                                      |
| Message Details                               [×]    |
|                                                      |
| Status: [PENDING]                                    |
|                                                      |
| Patient: John Doe                                    |
| Telegram ID: @johndoe                                |
|                                                      |
| Scheduled: May 16, 2023 at 10:30 AM                  |
| Created: May 15, 2023 at 2:45 PM                     |
| Last attempt: N/A                                    |
| Delivery attempts: 0                                 |
|                                                      |
| Message content:                                     |
| +--------------------------------------------+       |
| | Hi John,                                   |       |
| |                                            |       |
| | This is a reminder about your appointment  |       |
| | tomorrow at 10:30 AM with Dr. Smith.       |       |
| |                                            |       |
| | Please reply to confirm.                   |       |
| |                                            |       |
| | Thank you!                                 |       |
| +--------------------------------------------+       |
|                                                      |
| Recurrence: Weekly (Mon, Tue, Wed, Thu, Fri)         |
| Platform: Telegram                                   |
| Priority: Normal                                     |
|                                                      |
|                [Cancel] [Send Now] [Close]           |
+------------------------------------------------------+
```

## Confirmation Dialog

```
+------------------------------------------------------+
|                                                      |
| Cancel Scheduled Message                             |
|                                                      |
| Are you sure you want to cancel this scheduled       |
| message?                                             |
|                                                      |
| Patient: John Doe                                    |
| Scheduled: May 16, 2023 at 10:30 AM                  |
|                                                      |
| This action cannot be undone.                        |
|                                                      |
|                             [No] [Yes, Cancel]       |
+------------------------------------------------------+
```

## Implementation Notes

1. **Colors and Status Indicators**
   - Pending: Blue
   - Sent: Green
   - Failed: Red/Orange
   - Cancelled: Gray

2. **Responsive Design**
   - On mobile, table columns will collapse and show fewer columns
   - Filters will stack vertically
   - Action buttons will turn into a menu

3. **Accessibility**
   - All interactive elements will have proper ARIA labels
   - Color is not the only indicator of status
   - Keyboard navigation will be fully supported 