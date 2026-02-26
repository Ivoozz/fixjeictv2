#!/bin/bash

# FixJeICT v2 - Start Services Script
# Starts both the main app and admin portal

echo "FixJeICT v2 - Starting Services"
echo "================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Start main app
echo "Starting main app (port 5000)..."
systemctl start fixjeict.service
if [ $? -eq 0 ]; then
    echo "✓ Main app started"
else
    echo "✗ Failed to start main app"
fi

# Start admin portal
echo "Starting admin portal (port 5001)..."
systemctl start fixjeict-admin.service
if [ $? -eq 0 ]; then
    echo "✓ Admin portal started"
else
    echo "✗ Failed to start admin portal"
fi

echo
echo "Services status:"
systemctl status fixjeict.service --no-pager -l | grep -E "Active:|Loaded:"
systemctl status fixjeict-admin.service --no-pager -l | grep -E "Active:|Loaded:"

echo
echo "Main app: http://0.0.0.0:5000"
echo "Admin portal: http://0.0.0.0:5001"
