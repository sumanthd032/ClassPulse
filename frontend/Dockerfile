FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# Production: just the dist/ output — served by Nginx
FROM scratch AS export
COPY --from=builder /app/dist /dist
