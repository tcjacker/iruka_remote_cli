#!/bin/bash

echo "Starting agent service with Gemini CLI support..."

# Verify Gemini CLI is available (should be pre-installed)
if command -v gemini &> /dev/null; then
    echo "✅ Gemini CLI is available and ready"
else
    echo "❌ Warning: Gemini CLI not found in PATH"
    exit 1
fi

# Configure Git (set default user for commits)
git config --global user.name "Gemini Agent"
git config --global user.email "agent@gemini.local"
git config --global init.defaultBranch main

echo "🚀 Starting Python agent service..."
exec python -u agent.py
