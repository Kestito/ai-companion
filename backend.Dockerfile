FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Install additional packages for Telegram
RUN pip install --no-cache-dir python-telegram-bot supabase

# Expose port for API
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Command to run the app
CMD ["uvicorn", "src.ai_companion.interfaces.api:app", "--host", "0.0.0.0", "--port", "8000"] 