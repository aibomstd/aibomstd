FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install aibomstd from PyPI
RUN pip install --no-cache-dir aibomstd>=0.3.0

# Copy action scripts
COPY entrypoint.sh /entrypoint.sh
COPY scripts/format-github.py /scripts/format-github.py
COPY src/ci-runner.py /src/ci-runner.py

# Make executable
RUN chmod +x /entrypoint.sh

# Set working directory
WORKDIR /github/workspace

ENTRYPOINT ["/entrypoint.sh"]
