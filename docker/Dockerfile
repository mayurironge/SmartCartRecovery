# Image for the FastAPI backend.
FROM python:3.14.8-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installed before copying the code so this layer is reused
# when only the code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY genai ./genai
COPY dashboard ./dashboard

EXPOSE 8000 8501

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
