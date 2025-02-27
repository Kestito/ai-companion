# AI Companion Monitoring

This document describes the monitoring capabilities of the AI Companion system, including the RAG monitoring module and the monitoring API.

## Monitoring Interface

The AI Companion includes a dedicated monitoring interface that provides access to system metrics and performance data. This interface is implemented as a FastAPI application that exposes endpoints for retrieving metrics and performance reports.

### Endpoints

The monitoring API provides the following endpoints:

- **GET /monitor/health**: Health check endpoint for the monitoring API
- **GET /monitor/metrics**: Get current RAG metrics
- **GET /monitor/report**: Get RAG performance report
- **POST /monitor/reset**: Reset all RAG metrics

### Running the Monitoring Interface

The monitoring interface can be run in several ways:

#### Standalone Mode

```bash
uvicorn ai_companion.interfaces.monitor.app:app --host 0.0.0.0 --port 8090
```

#### Docker Mode

```bash
docker run -p 8090:8090 -e INTERFACE=monitor ai-companion:all
```

#### All Interfaces Mode

```bash
docker run -p 8000:8000 -p 8080:8080 -p 8090:8090 -e INTERFACE=all ai-companion:all
```

### Accessing the Monitoring Interface

Once running, the monitoring interface can be accessed at:

- API Documentation: http://localhost:8090/docs
- Metrics: http://localhost:8090/monitor/metrics
- Performance Report: http://localhost:8090/monitor/report

## RAG Monitoring

The RAG monitoring module tracks the performance and usage of the Retrieval-Augmented Generation system. It collects metrics on query success rates, response times, and error types.

### Metrics Collected

The RAG monitoring system collects the following metrics:

- **Query Metrics**:
  - Total queries
  - Successful queries
  - Failed queries
  - Verified responses
  - Insufficient information cases
  - Validation failures

- **Error Types**:
  - Insufficient information
  - Query processing errors
  - Retrieval errors
  - Response generation errors
  - System errors

- **Performance Metrics**:
  - Average query time
  - Average retrieval time
  - Average response time
  - Average generation time
  - Average total time

- **Search Source Metrics**:
  - Vector-only searches
  - Keyword-only searches
  - Hybrid searches
  - Total vector documents retrieved
  - Total keyword documents retrieved

- **Time-Based Statistics**:
  - Hourly query counts
  - Daily query counts

### Performance Report

The performance report provides a summary of the RAG system's performance, including:

- **Accuracy**:
  - Success rate
  - Verification rate
  - Insufficient information rate
  - Failure rate

- **Performance**:
  - Average response time
  - Average query time
  - Average retrieval time

- **Volume**:
  - Total queries
  - Daily average

- **Errors**:
  - Top error types

## Integration with Other Interfaces

The monitoring interface is designed to work alongside the other interfaces (WhatsApp, Chainlit, Telegram) and provides insights into the system's performance across all interfaces.

### Metrics Storage

Metrics are stored in a JSON file at the path specified by the `METRICS_DIR` environment variable (defaults to `metrics/rag_metrics.json`). This file is periodically saved and can be backed up or analyzed externally.

### Cleanup Policy

To prevent the metrics file from growing too large, the system automatically removes statistics older than 30 days.

## Extending the Monitoring System

The monitoring system can be extended in several ways:

1. **Additional Metrics**: New metrics can be added to the `RAGMonitor` class in `ai_companion/modules/rag/core/monitoring.py`.
2. **Custom Reports**: New report types can be added as endpoints in the monitoring API.
3. **Alerting**: The monitoring system can be extended to send alerts when certain thresholds are exceeded.
4. **Visualization**: The metrics can be visualized using external tools like Grafana or custom dashboards.

## Troubleshooting

If you encounter issues with the monitoring system:

1. **Check Logs**: The monitoring system logs errors and warnings to the application logs.
2. **Check Metrics File**: Ensure the metrics file is being created and updated correctly.
3. **Check API Access**: Verify that the monitoring API is accessible and returning valid responses.
4. **Check Permissions**: Ensure the application has permission to write to the metrics directory. 