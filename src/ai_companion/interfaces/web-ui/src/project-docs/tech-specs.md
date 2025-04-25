# AI Companion Technical Specifications

## Scheduler API

### Endpoints

#### GET /api/scheduler
Retrieves a list of scheduled messages, optionally filtered by patient ID.

**Query Parameters:**
- `patientId` (optional): Filter messages by patient ID
- `status` (optional): Filter messages by status (pending, sent, failed, cancelled)

**Response:**
```json
{
  "messages": [
    {
      "id": "message-uuid",
      "patient_id": "patient-uuid",
      "message_content": "Message text",
      "scheduled_time": "2023-10-15T14:30:00Z",
      "status": "pending",
      "created_at": "2023-10-10T09:15:30Z",
      "recurrence": {
        "type": "weekly",
        "days": [1, 3, 5],
        "time": "14:30"
      }
    }
  ]
}
```

#### POST /api/scheduler
Creates a new scheduled message.

**Request Body:**
```json
{
  "patientId": "patient-uuid",
  "chatId": "1234567890",
  "messageContent": "Message text",
  "scheduledTime": "2023-10-15T14:30:00Z",
  "recurrence": {
    "type": "weekly",
    "days": [1, 3, 5]
  }
}
```

**Response:**
```json
{
  "messageData": {
    "id": "message-uuid",
    "patient_id": "patient-uuid",
    "message_content": "Message text",
    "scheduled_time": "2023-10-15T14:30:00Z",
    "status": "pending",
    "created_at": "2023-10-10T09:15:30Z",
    "recurrence": {
      "type": "weekly",
      "days": [1, 3, 5],
      "time": "14:30"
    }
  },
  "success": true
}
```

#### PATCH /api/scheduler
Updates an existing scheduled message.

**Request Body:**
```json
{
  "id": "message-uuid",
  "messageContent": "Updated message text",
  "scheduledTime": "2023-10-16T15:00:00Z",
  "status": "pending"
}
```

**Response:**
```json
{
  "messageData": {
    "id": "message-uuid",
    "patient_id": "patient-uuid",
    "message_content": "Updated message text",
    "scheduled_time": "2023-10-16T15:00:00Z",
    "status": "pending",
    "created_at": "2023-10-10T09:15:30Z",
    "recurrence": {
      "type": "weekly",
      "days": [1, 3, 5],
      "time": "15:00"
    }
  },
  "success": true
}
```

#### DELETE /api/scheduler
Cancels a scheduled message.

**Query Parameters:**
- `id`: The UUID of the message to cancel

**Response:**
```json
{
  "success": true
}
```

#### POST /api/scheduler/send-now
Sends a scheduled message immediately.

**Request Body:**
```json
{
  "id": "message-uuid"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Message scheduled for immediate sending"
}
```

### Integration with Telegram

The scheduler API integrates with the Telegram Bot API to send messages. Each patient must have a valid Telegram ID (chat_id) associated with their profile for messaging to work.

### Error Handling

All API endpoints return appropriate HTTP status codes and error messages:

- 400: Bad Request - Missing or invalid parameters
- 404: Not Found - Message ID not found
- 500: Internal Server Error - Backend processing error

Detailed error messages are included in the response body to aid in troubleshooting. 