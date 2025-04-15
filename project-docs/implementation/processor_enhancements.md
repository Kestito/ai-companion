# Scheduled Messaging System: Processor Enhancements

## Current Processor Architecture

The existing message processor (`src/ai_companion/modules/scheduled_messaging/processor.py`) implements a simple polling architecture:

1. Queries database for pending messages that are due
2. Processes each message sequentially
3. Routes messages to appropriate platform handlers
4. Updates status in database
5. Handles recurring messages

## Proposed Enhancements

Based on our requirements analysis, we propose the following enhancements to improve performance, reliability, and monitoring.

### 1. Enhanced Processing Model

#### 1.1 Worker Pool Architecture
```python
class MessageProcessor:
    def __init__(self, worker_count=5):
        self.worker_count = worker_count
        self.queue = asyncio.Queue()
        self.workers = []
        
    async def start(self):
        # Start worker tasks
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._worker_loop(i))
            self.workers.append(worker)
            
        # Start fetcher task
        self.fetcher = asyncio.create_task(self._fetcher_loop())
        
    async def _fetcher_loop(self):
        while True:
            # Fetch messages in batches with priority ordering
            messages = await self._fetch_due_messages()
            
            # Add to processing queue
            for message in messages:
                await self.queue.put(message)
                
            # Sleep for a short interval before next fetch
            await asyncio.sleep(10)
            
    async def _worker_loop(self, worker_id):
        while True:
            # Get next message from queue
            message = await self.queue.get()
            
            try:
                # Process message with appropriate handler
                await self._process_message(message)
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
            finally:
                # Mark task as done
                self.queue.task_done()
```

#### 1.2 Prioritized Message Fetching
```sql
-- Query to fetch messages in priority order
SELECT * FROM scheduled_messages
WHERE status = 'pending' 
  AND scheduled_time <= NOW()
  AND (attempts = 0 OR last_attempt_time < NOW() - (INTERVAL '5 minutes' * attempts))
ORDER BY priority ASC, scheduled_time ASC
LIMIT 100
```

#### 1.3 Improved Retry Logic
```python
async def _calculate_next_retry(message):
    attempts = message.get("attempts", 0)
    
    # Exponential backoff with jitter
    if attempts <= 0:
        return 0  # Immediate retry for first attempt
        
    # Base backoff: 5 minutes * attempt count squared
    backoff_minutes = 5 * (attempts ** 2)
    
    # Cap at 12 hours
    backoff_minutes = min(backoff_minutes, 720)
    
    # Add jitter (±15%)
    jitter = random.uniform(0.85, 1.15)
    backoff_minutes = backoff_minutes * jitter
    
    # Convert to seconds
    backoff_seconds = backoff_minutes * 60
    
    return backoff_seconds
```

### 2. Error Handling Improvements

#### 2.1 Error Categorization
```python
class ErrorCategory(Enum):
    TEMPORARY = "temporary"  # Transient errors, should retry
    PERMANENT = "permanent"  # Permanent errors, no retry
    THROTTLING = "throttling"  # Rate limiting, retry with specific backoff
    VALIDATION = "validation"  # Message content/format errors
    SYSTEM = "system"  # Internal system errors

async def _categorize_error(message, exception):
    # Platform-specific error mapping
    platform = message.get("platform")
    
    if platform == "telegram":
        return _categorize_telegram_error(exception)
    elif platform == "whatsapp":
        return _categorize_whatsapp_error(exception)
    else:
        return _categorize_generic_error(exception)
```

#### 2.2 Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = "closed"  # closed, open, half-open
        self.last_failure_time = 0
        
    async def execute(self, func, *args, **kwargs):
        if self.state == "open":
            # Check if timeout has elapsed
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "half-open"
                logger.info("Circuit breaker transitioning to half-open state")
            else:
                raise CircuitOpenError("Circuit breaker is open")
                
        try:
            result = await func(*args, **kwargs)
            
            # Reset on success if in half-open state
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker reset to closed state")
                
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == "closed" and self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning("Circuit breaker tripped to open state")
                
            raise
```

### 3. Advanced Status Tracking

#### 3.1 Message Lifecycle State Machine
```python
class MessageStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

async def _update_message_status(message_id, new_status, details=None):
    """Update message status with comprehensive tracking."""
    supabase = get_supabase_client()
    
    # Fetch current status
    result = await supabase.table("scheduled_messages") \
        .select("status, attempts") \
        .eq("id", message_id) \
        .execute()
    
    if not result.data:
        logger.error(f"Message {message_id} not found")
        return False
    
    current_status = result.data[0].get("status")
    attempts = result.data[0].get("attempts", 0)
    
    # Validate status transition
    valid_transitions = {
        "pending": ["processing", "cancelled", "expired"],
        "processing": ["sent", "failed", "pending"],
        "failed": ["pending", "cancelled", "expired"],
        "sent": [],  # Terminal state
        "cancelled": [],  # Terminal state
        "expired": []  # Terminal state
    }
    
    if new_status not in valid_transitions.get(current_status, []):
        logger.error(f"Invalid status transition from {current_status} to {new_status}")
        return False
    
    # Prepare update data
    update_data = {
        "status": new_status,
        "updated_at": datetime.now().isoformat()
    }
    
    # Add status-specific fields
    if new_status == "processing":
        update_data["attempts"] = attempts + 1
        update_data["last_attempt_time"] = datetime.now().isoformat()
    elif new_status == "sent":
        update_data["sent_at"] = datetime.now().isoformat()
    elif new_status == "failed":
        update_data["failed_at"] = datetime.now().isoformat()
        if details and "error" in details:
            update_data["error_message"] = details["error"]
    
    # Update the record
    await supabase.table("scheduled_messages") \
        .update(update_data) \
        .eq("id", message_id) \
        .execute()
    
    return True
```

#### 3.2 Status History Tracking
```sql
-- Create a status history table
CREATE TABLE IF NOT EXISTS public.message_status_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID REFERENCES public.scheduled_messages(id),
    status TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_message_status_history_message_id 
ON public.message_status_history(message_id);
```

### 4. Monitoring and Metrics

#### 4.1 Structured Logging
```python
def setup_logging():
    """Set up structured JSON logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add JSON handler
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(
        jsonlogger.JsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(json_handler)
    
    return root_logger
```

#### 4.2 Performance Metrics Collection
```python
class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "messages_processed": 0,
            "messages_succeeded": 0,
            "messages_failed": 0,
            "processing_time_ms": [],
            "errors_by_category": {
                "temporary": 0,
                "permanent": 0,
                "throttling": 0,
                "validation": 0,
                "system": 0
            }
        }
        
    async def record_processing(self, success, duration_ms, error_category=None):
        self.metrics["messages_processed"] += 1
        
        if success:
            self.metrics["messages_succeeded"] += 1
        else:
            self.metrics["messages_failed"] += 1
            
            if error_category:
                self.metrics["errors_by_category"][error_category] += 1
        
        self.metrics["processing_time_ms"].append(duration_ms)
        
    async def get_summary(self):
        """Get summary metrics for reporting."""
        total_processed = self.metrics["messages_processed"]
        if total_processed == 0:
            return {
                "success_rate": 0,
                "avg_processing_time_ms": 0,
                "total_processed": 0,
                "error_rate_by_category": {}
            }
            
        avg_time = sum(self.metrics["processing_time_ms"]) / len(self.metrics["processing_time_ms"])
        success_rate = self.metrics["messages_succeeded"] / total_processed
        
        error_rate_by_category = {
            category: count / total_processed 
            for category, count in self.metrics["errors_by_category"].items()
        }
        
        return {
            "success_rate": success_rate,
            "avg_processing_time_ms": avg_time,
            "total_processed": total_processed,
            "error_rate_by_category": error_rate_by_category
        }
```

#### 4.3 Health Check Endpoint
```python
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()
processor = None  # Will be set during startup

@app.get("/health")
async def health_check():
    if not processor:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "down", "reason": "Processor not initialized"}
        )
    
    # Get metrics
    metrics = await processor.metrics_collector.get_summary()
    
    # Check if processor is healthy
    is_healthy = True
    reasons = []
    
    # Check success rate
    if metrics["total_processed"] > 10 and metrics["success_rate"] < 0.9:
        is_healthy = False
        reasons.append(f"Low success rate: {metrics['success_rate']:.2f}")
    
    # Check error rates
    for category, rate in metrics["error_rate_by_category"].items():
        if rate > 0.1:  # More than 10% of messages failing with this category
            is_healthy = False
            reasons.append(f"High {category} error rate: {rate:.2f}")
    
    if is_healthy:
        return {"status": "up", "metrics": metrics}
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "reasons": reasons, "metrics": metrics}
        )
```

### 5. Implementation Plan

1. **Phase 1: Core Improvements**
   - Implement worker pool architecture
   - Add priority-based processing
   - Enhance retry logic

2. **Phase 2: Error Handling**
   - Add error categorization
   - Implement circuit breaker pattern
   - Enhance status tracking

3. **Phase 3: Monitoring**
   - Add structured logging
   - Implement metrics collection
   - Create health check endpoint

4. **Phase 4: Performance Optimization**
   - Add batch processing
   - Optimize database queries
   - Fine-tune worker count and polling intervals

## Expected Benefits

- **Improved Throughput**: Worker pool enables parallel processing
- **Better Reliability**: Enhanced error handling and retry mechanisms
- **Reduced Database Load**: Batched queries and optimized polling
- **Better Observability**: Comprehensive metrics and structured logging
- **Graceful Degradation**: Circuit breaker prevents cascading failures

## Compatibility Notes

These enhancements are designed to be backward compatible with:
- Existing database schema (with recommended additions)
- Existing platform handlers
- Current deployment infrastructure

## Testing Strategy

1. **Unit Tests**: Test individual components (error classification, retry logic)
2. **Integration Tests**: Test worker pool with mock database
3. **Load Tests**: Verify performance under high message volume
4. **Failure Tests**: Validate behavior during external service outages 