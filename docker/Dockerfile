# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set memory limit and optimization environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_OPTIONS="--max-old-space-size=512"
ENV NPM_CONFIG_CACHE=/tmp/.npm

# Set up proxy configuration
ARG http_proxy
ARG https_proxy

ENV http_proxy=${http_proxy}
ENV https_proxy=${https_proxy}

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for Node.js setup and git
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Node.js (version 20.x) and npm
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Google Gemini CLI globally via npm with memory optimization
RUN if [ -n "${http_proxy}" ]; then npm config set proxy ${http_proxy}; fi && \
    if [ -n "${https_proxy}" ]; then npm config set https-proxy ${https_proxy}; fi && \
    npm install -g @google/gemini-cli --no-audit --no-fund && \
    npm config delete proxy && \
    npm config delete https-proxy && \
    npm cache clean --force

# Install Anthropic (Claude) Python library via pip with no cache
RUN pip install --no-cache-dir --proxy ${https_proxy} anthropic

# Add memory limit labels for container runtime
LABEL memory.limit="1g"
LABEL memory.swap.limit="1g"

# Note: To enforce 1GB memory limit at runtime, use:
# docker run --memory=1g --memory-swap=1g <image_name>

# Set the default command to a bash shell
CMD ["/bin/bash"]
