# Build stage
FROM node:18-alpine AS deps
WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json ./
RUN npm install

# Builder stage
FROM node:18-alpine AS builder
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

# Production stage
FROM node:18-alpine AS runner
WORKDIR /app

# Set environment variables
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1
# Make sure to set the INTERFACE environment variable to specify this is the web-ui
ENV INTERFACE web-ui

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy only necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose the port
EXPOSE 3000

# Set the environment variable for the port
ENV PORT 3000

# Start only the Next.js server
CMD ["node", "server.js"] 