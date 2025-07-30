# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies including Node.js 20+ and Git
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Gemini CLI globally during image build
RUN npm install -g @google/gemini-cli

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent script and startup script
COPY agent.py .
COPY startup.sh .
RUN chmod +x startup.sh

# Expose port 5000
EXPOSE 5000

# Run the startup script
CMD ["./startup.sh"]
