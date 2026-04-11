FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt && playwright install --with-deps chromium

COPY app /app/app
COPY scripts /app/scripts

EXPOSE 8000

CMD ["/bin/sh", "-c", "python scripts/bootstrap_admin.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
