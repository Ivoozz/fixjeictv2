#!/bin/bash

# FixJeICT v2 - Stop Services Script
# Stops both the main app and admin portal

echo "FixJeICT v2 - Stopping Services"
echo "==============================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Stop main app
echo "Stopping main app (port 5000)..."
systemctl stop fixjeict.service
if [ $? -eq 0 ]; then
    echo "✓ Main app stopped"
else
    echo "✗ Failed to stop main app"
fi

# Stop admin portal
echo "Stopping admin portal (port 5001)..."
systemctl stop fixjeict-admin.service
if [ $? -eq 0 ]; then
    echo "✓ Admin portal stopped"
else
    echo "✗ Failed to stop admin portal"
fi

echo
echo "Services stopped"
