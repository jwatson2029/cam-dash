# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r nvr && useradd -r -g nvr nvr

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories with correct ownership
RUN mkdir -p recordings motion_events logs \
    && chown -R nvr:nvr /app

USER nvr

EXPOSE 8000

CMD ["python", "main.py"]
