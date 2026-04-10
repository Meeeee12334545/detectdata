# Stage 1: Build the React frontend
FROM node:22-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .

RUN npm run build

# Stage 2: Python backend — also serves the built frontend
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt && playwright install --with-deps chromium

COPY backend/app /app/app
COPY backend/scripts /app/scripts

# Embed the built frontend so FastAPI can serve it
COPY --from=frontend-build /frontend/dist /app/static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
