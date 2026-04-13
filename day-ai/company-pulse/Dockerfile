# syntax=docker/dockerfile:1

# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app

# Install dependencies needed for native builds
RUN apk add --no-cache libc6-compat

# Copy package files and SDK tarball
COPY package*.json ./
COPY day-ai-sdk-0.1.0.tgz ./

# Update package.json to point to SDK tarball
RUN sed -i 's|"day-ai-sdk": "file:../day-sdk"|"day-ai-sdk": "file:./day-ai-sdk-0.1.0.tgz"|' package.json

# Install all dependencies including the SDK
RUN npm install --only=production

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app

# Copy dependencies from deps stage (includes SDK)
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/package*.json ./

# Copy all source files
COPY . .

# Restore the modified package.json from deps (with SDK tarball reference)
RUN cp package.json package.json.original
COPY --from=deps /app/package*.json ./

# Set build-time environment variables
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build the Next.js application
RUN npm run build

# Stage 3: Runner
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create a non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Change ownership to nextjs user
RUN chown -R nextjs:nodejs /app

USER nextjs

# Cloud Run sets PORT environment variable
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start the application
CMD ["node", "server.js"]
