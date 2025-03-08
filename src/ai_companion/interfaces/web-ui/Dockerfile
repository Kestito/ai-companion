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