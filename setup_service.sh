#!/bin/bash

# This script sets up the YouTube Monitor service on a Linux server

# Exit on any error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Create service user if it doesn't exist
if ! id -u youtube-monitor > /dev/null 2>&1; then
    useradd -r -s /bin/false youtube-monitor
fi

# Create necessary directories
mkdir -p /var/log/youtube-monitor
mkdir -p /opt/youtube-monitor

# Copy files to installation directory
cp -r ./* /opt/youtube-monitor/

# Set ownership and permissions
chown -R youtube-monitor:youtube-monitor /opt/youtube-monitor
chown -R youtube-monitor:youtube-monitor /var/log/youtube-monitor
chmod 755 /opt/youtube-monitor
chmod 644 /opt/youtube-monitor/*.py
chmod 644 /opt/youtube-monitor/*.txt
chmod 600 /opt/youtube-monitor/.env

# Update service file with correct paths
sed -i "s|User=your_service_user|User=youtube-monitor|" youtube-monitor.service
sed -i "s|WorkingDirectory=/path/to/bot|WorkingDirectory=/opt/youtube-monitor|" youtube-monitor.service

# Install service
cp youtube-monitor.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable youtube-monitor.service

echo "Installation complete. Please:"
echo "1. Update /opt/youtube-monitor/.env with your configuration"
echo "2. Install required dependencies: pip3 install -r /opt/youtube-monitor/requirements.txt"
echo "3. Start the service: systemctl start youtube-monitor"
echo "4. Check status: systemctl status youtube-monitor"
echo "5. View logs: tail -f /var/log/youtube-monitor/output.log"
