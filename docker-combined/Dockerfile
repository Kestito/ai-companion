FROM ghcr.io/ai-companion/ai-companion:latest

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create volume for logs
VOLUME /app/logs

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]