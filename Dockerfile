#Lightweight Python image
FROM python:3.11-slim


WORKDIR /app

# Install system deps required for building some packages (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*


COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


COPY . /app


RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser


EXPOSE 5000

# Healthcheck (simple)
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -fsS http://localhost:5000/ || exit 1


CMD ["python", "app.py"]
