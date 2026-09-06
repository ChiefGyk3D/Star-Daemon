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
COPY star_daemon.py /app/
COPY star_announcer.py /app/
COPY github_stars.py /app/
COPY config.py /app/
COPY platforms.py /app/

# Create non-root user for security
RUN useradd -m -u 1000 stardaemon && \
    chown -R stardaemon:stardaemon /app && \
    mkdir -p /home/stardaemon && \
    chown -R stardaemon:stardaemon /home/stardaemon

USER stardaemon

# Set home directory for state file persistence
ENV HOME=/home/stardaemon

# Liveness probe against the daemon's /healthz endpoint (hypeman-social
# observability). Only meaningful when HEALTH_PORT is set; without it the
# check passes trivially so the container isn't marked unhealthy for
# choosing not to expose health. Uses urllib because slim images ship no curl.
HEALTHCHECK --interval=60s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import os,sys,urllib.request;port=os.getenv('HEALTH_PORT');sys.exit(0) if not port else urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz', timeout=4)"]

# Run the application
CMD ["python", "star-daemon.py"]
