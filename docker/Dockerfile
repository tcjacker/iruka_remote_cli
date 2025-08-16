# Use an official Python runtime as a parent image
FROM python:3.11-slim

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
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (version 20.x) and npm
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install Google Gemini CLI globally via npm
RUN if [ -n "${http_proxy}" ]; then npm config set proxy ${http_proxy}; fi && \
    if [ -n "${https_proxy}" ]; then npm config set https-proxy ${https_proxy}; fi && \
    npm install -g @google/gemini-cli && \
    npm config delete proxy && \
    npm config delete https-proxy

# Install Anthropic (Claude) Python library via pip
RUN pip install --proxy ${https_proxy} anthropic

# Set the default command to a bash shell
CMD ["/bin/bash"]
