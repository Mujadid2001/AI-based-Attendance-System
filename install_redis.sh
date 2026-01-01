#!/bin/bash

# Redis Installation Script for WSL/Ubuntu
# This script installs Redis server required for Django Channels WebSocket support

echo "======================================"
echo "Redis Installation for WebSocket Support"
echo "======================================"
echo ""

# Update package list
echo "[1/4] Updating package list..."
sudo apt-get update -qq

# Install Redis
echo "[2/4] Installing Redis server..."
sudo apt-get install -y redis-server

# Verify installation
echo "[3/4] Verifying installation..."
redis-server --version

# Configure Redis to start automatically (optional)
echo "[4/4] Configuring Redis..."
sudo sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf

echo ""
echo "======================================"
echo "Redis Installation Complete!"
echo "======================================"
echo ""
echo "To start Redis:"
echo "  redis-server"
echo ""
echo "To start Redis in background:"
echo "  redis-server --daemonize yes"
echo ""
echo "To test Redis:"
echo "  redis-cli ping"
echo "  (Should return 'PONG')"
echo ""
echo "To stop Redis:"
echo "  redis-cli shutdown"
echo ""
