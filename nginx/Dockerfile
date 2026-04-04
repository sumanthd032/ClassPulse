FROM node:20-alpine AS frontend_builder
WORKDIR /app
COPY ../frontend/package.json ../frontend/package-lock.json* ./
RUN npm ci
COPY ../frontend .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=frontend_builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
