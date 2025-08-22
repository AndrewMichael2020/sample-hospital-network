FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    libssl-dev \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy runtime requirements and install Python runtime dependencies only (smaller image)
COPY requirements-runtime.txt ./requirements-runtime.txt
ARG INSTALL_FULL_REQUIREMENTS=false
RUN if [ "$INSTALL_FULL_REQUIREMENTS" = "true" ]; then \
            cp requirements.txt requirements-full.txt && \
            pip install --no-cache-dir -r requirements-full.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org ; \
        else \
            pip install --no-cache-dir -r requirements-runtime.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org ; \
        fi

# Copy application files
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Default command (can be overridden)
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]