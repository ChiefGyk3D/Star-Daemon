FROM python:3.13-slim

# Set build arguments for platform detection (automatically set by buildx)
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Set working directory
WORKDIR /app

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY star-daemon.py /app/
COPY config.py /app/
COPY connectors/ /app/connectors/
COPY .env.example /app/

# Create non-root user for security
RUN useradd -m -u 1000 stardaemon && \
    chown -R stardaemon:stardaemon /app && \
    mkdir -p /home/stardaemon && \
    chown -R stardaemon:stardaemon /home/stardaemon

USER stardaemon

# Set home directory for state file persistence
ENV HOME=/home/stardaemon

# Run the application
CMD ["python", "star-daemon.py"]
