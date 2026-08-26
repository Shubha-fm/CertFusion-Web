# syntax=docker/dockerfile:1
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CERTFUSION_MODE=auto \
    PORT=7860
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend ./backend
COPY formal ./formal
COPY --from=frontend /frontend/dist ./frontend_dist
COPY serve.py ./serve.py
EXPOSE 7860
CMD ["python","serve.py"]
