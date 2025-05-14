# Build stage
FROM mcr.microsoft.com/oryx/node:18 AS deps

# Install necessary system dependencies
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy package files for dependency installation
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Builder stage
FROM mcr.microsoft.com/oryx/node:18 AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment variables for Next.js
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV production

# Add ARGs for build-time environment variables
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_AZURE_OPENAI_ENDPOINT
ARG NEXT_PUBLIC_AZURE_OPENAI_API_KEY
ARG NEXT_PUBLIC_AZURE_OPENAI_DEPLOYMENT
ARG NEXT_PUBLIC_EMBEDDING_MODEL
ARG NEXT_PUBLIC_LLM_MODEL
ARG NEXT_PUBLIC_COLLECTION_NAME
ARG NEXT_PUBLIC_API_URL

# Pass ARGs to ENVs for Next.js to use during build
ENV NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL}
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY}
ENV NEXT_PUBLIC_AZURE_OPENAI_ENDPOINT=${NEXT_PUBLIC_AZURE_OPENAI_ENDPOINT}
ENV NEXT_PUBLIC_AZURE_OPENAI_API_KEY=${NEXT_PUBLIC_AZURE_OPENAI_API_KEY}
ENV NEXT_PUBLIC_AZURE_OPENAI_DEPLOYMENT=${NEXT_PUBLIC_AZURE_OPENAI_DEPLOYMENT}
ENV NEXT_PUBLIC_EMBEDDING_MODEL=${NEXT_PUBLIC_EMBEDDING_MODEL}
ENV NEXT_PUBLIC_LLM_MODEL=${NEXT_PUBLIC_LLM_MODEL}
ENV NEXT_PUBLIC_COLLECTION_NAME=${NEXT_PUBLIC_COLLECTION_NAME}
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Build the application
RUN npm run build

# Production stage - Use Node.js official image
FROM node:18-alpine AS runner
WORKDIR /app

# Set environment variables
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1
ENV INTERFACE web-ui
ENV PORT 3000
ENV WEBSITES_PORT 3000
# Azure environment variables
ENV WEBSITE_HOSTNAME app.azurewebsites.net
ENV WEBSITE_INSTANCE_ID web_1
ENV WEBSITE_SITE_NAME ai-companion-frontend

# Copy only necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Add health check endpoint for Azure
RUN echo 'const http = require("http"); \
const server = http.createServer((req, res) => { \
  if (req.url === "/health") { \
    res.writeHead(200, {"Content-Type": "application/json"}); \
    res.end(JSON.stringify({status: "ok"})); \
  } else { \
    res.writeHead(404); \
    res.end(); \
  } \
}); \
server.listen(4000, () => { \
  console.log("Health check server running on port 4000"); \
});' > /app/health.js

# Add startup script for Azure
RUN echo '#!/bin/bash\n\
node health.js &\n\
exec node server.js\n\
' > /app/startup.sh && chmod +x /app/startup.sh

# Expose the ports for main app and health check
EXPOSE 3000 4000

# Health check for Azure App Service
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:4000/health || exit 1

# Command to run using Azure's PM2 for better process management
CMD ["/app/startup.sh"] 