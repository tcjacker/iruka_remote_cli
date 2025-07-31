#!/bin/bash

# Gemini CLI Docker System Cleanup Script
# This script stops all services and cleans up Docker containers
echo "🧹 Gemini CLI Docker Integration - Cleanup Script"
echo "================================================"

# Stop main service if running
echo "🛑 Stopping main service..."
pkill -f "python.*main.py" || echo "   No main service process found"
pkill -f "python.*main_service.py" || echo "   No legacy main_service process found"

# Stop and remove all agent-service containers
echo "Stopping agent containers..."
docker stop $(docker ps -q --filter "ancestor=agent-service:latest") 2>/dev/null || true
docker rm $(docker ps -aq --filter "ancestor=agent-service:latest") 2>/dev/null || true

# Clean up any orphaned containers (optional - be careful with this)
# Uncomment the following lines if you want to clean up ALL containers
# echo "Cleaning up all containers..."
# docker stop $(docker ps -aq) 2>/dev/null || true
# docker rm $(docker ps -aq) 2>/dev/null || true

# Show final status
echo "📊 Final Docker status:"
docker ps -a

echo "✅ Cleanup completed!"
