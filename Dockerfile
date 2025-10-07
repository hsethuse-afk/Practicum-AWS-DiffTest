# Dockerfile - Env Builder (robust defaults for builds + wheelhouse)
FROM python:3.10-bullseye

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    HOME=/workspace

# Install common build deps and tools used by many Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ make curl git ca-certificates \
    python3-dev libssl-dev libffi-dev zlib1g-dev \
    libpq-dev libxml2-dev libxslt1-dev libjpeg-dev \
    cargo pkg-config && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy repository into image (ensures local editable installs in requirements work)
COPY . /workspace

# Install helper Python tools globally for environment scanning
RUN python -m pip install --upgrade pip setuptools wheel \
    pip-tools pipreqs toml

# Prepare persistent dirs for wheelhouse and runs
RUN mkdir -p /wheelhouse /runs /workspace/.env_cache
VOLUME ["/wheelhouse", "/runs"]

# Normalize entrypoint
COPY entrypoint.sh /workspace/entrypoint.sh
RUN chmod +x /workspace/entrypoint.sh

# Copy tools (if any new ones added after IMAGE build, mount repo instead)
COPY tools /workspace/tools
RUN chmod +x /workspace/tools/*.py || true

ENTRYPOINT ["/workspace/entrypoint.sh"]
