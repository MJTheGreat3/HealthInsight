# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Install all dependencies (including dev dependencies for build)
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application
COPY --from=build /app/dist /usr/share/nginx/html

# Use existing nginx user, but ensure proper permissions
RUN chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /usr/share/nginx/html

# Health check removed per user request

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

