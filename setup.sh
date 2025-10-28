#!/bin/bash

# Star-Daemon Quick Setup Script
# This script helps you set up Star-Daemon quickly

set -e

echo "🌟 Star-Daemon Setup Script"
echo "=============================="
echo ""

# Check if .env exists
if [ -f .env ]; then
    read -p ".env file already exists. Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file"
    else
        cp .env.example .env
        echo "✅ Created new .env from template"
    fi
else
    cp .env.example .env
    echo "✅ Created .env from template"
fi

echo ""
echo "⚙️  Configuration"
echo "================="

# Get GitHub token
read -p "Enter your GitHub Personal Access Token: " github_token
if [ -n "$github_token" ]; then
    sed -i "s/GITHUB_ACCESS_TOKEN=.*/GITHUB_ACCESS_TOKEN=$github_token/" .env
    echo "✅ GitHub token configured"
fi

echo ""
read -p "Do you want to configure Mastodon? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Mastodon instance URL (e.g., https://mastodon.social): " mastodon_url
    read -p "Mastodon access token: " mastodon_token
    
    sed -i "s/MASTODON_ENABLED=.*/MASTODON_ENABLED=true/" .env
    sed -i "s|MASTODON_API_BASE_URL=.*|MASTODON_API_BASE_URL=$mastodon_url|" .env
    sed -i "s/MASTODON_ACCESS_TOKEN=.*/MASTODON_ACCESS_TOKEN=$mastodon_token/" .env
    echo "✅ Mastodon configured"
fi

echo ""
read -p "Do you want to configure BlueSky? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "BlueSky handle (e.g., user.bsky.social): " bluesky_handle
    read -p "BlueSky app password: " bluesky_password
    
    sed -i "s/BLUESKY_ENABLED=.*/BLUESKY_ENABLED=true/" .env
    sed -i "s/BLUESKY_HANDLE=.*/BLUESKY_HANDLE=$bluesky_handle/" .env
    sed -i "s/BLUESKY_APP_PASSWORD=.*/BLUESKY_APP_PASSWORD=$bluesky_password/" .env
    echo "✅ BlueSky configured"
fi

echo ""
read -p "Do you want to configure Discord? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Discord webhook URL: " discord_webhook
    
    sed -i "s/DISCORD_ENABLED=.*/DISCORD_ENABLED=true/" .env
    sed -i "s|DISCORD_WEBHOOK_URL=.*|DISCORD_WEBHOOK_URL=$discord_webhook|" .env
    echo "✅ Discord configured"
fi

echo ""
read -p "Do you want to configure Matrix? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Matrix homeserver URL (e.g., https://matrix.org): " matrix_server
    read -p "Matrix user ID (e.g., @user:matrix.org): " matrix_user
    read -p "Matrix password: " matrix_password
    read -p "Matrix room ID (e.g., !room:matrix.org): " matrix_room
    
    sed -i "s/MATRIX_ENABLED=.*/MATRIX_ENABLED=true/" .env
    sed -i "s|MATRIX_HOMESERVER=.*|MATRIX_HOMESERVER=$matrix_server|" .env
    sed -i "s/MATRIX_USER_ID=.*/MATRIX_USER_ID=$matrix_user/" .env
    sed -i "s/MATRIX_PASSWORD=.*/MATRIX_PASSWORD=$matrix_password/" .env
    sed -i "s/MATRIX_ROOM_ID=.*/MATRIX_ROOM_ID=$matrix_room/" .env
    echo "✅ Matrix configured"
fi

echo ""
echo "📦 Deployment Method"
echo "===================="
echo "1) Docker (recommended)"
echo "2) Local Python"
echo "3) systemd Service"
read -p "Choose deployment method (1/2/3): " -n 1 -r
echo

case $REPLY in
    1)
        echo "🐳 Starting Docker deployment..."
        if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
            cd docker
            docker-compose up -d
            echo ""
            echo "✅ Star-Daemon is running in Docker!"
            echo "📊 View logs: cd docker && docker-compose logs -f"
            echo "🛑 Stop: cd docker && docker-compose down"
        else
            echo "❌ Docker not found. Please install Docker first."
            exit 1
        fi
        ;;
    2)
        echo "🐍 Setting up local Python environment..."
        if command -v python3 &> /dev/null; then
            python3 -m venv venv
            source venv/bin/activate
            pip install -r requirements.txt
            echo ""
            echo "✅ Python environment ready!"
            echo "🚀 Run: python star-daemon.py"
            echo "🛑 Stop: Press Ctrl+C"
        else
            echo "❌ Python 3 not found. Please install Python 3.11+ first."
            exit 1
        fi
        ;;
    3)
        echo "⚙️  Setting up systemd service..."
        SERVICE_FILE="/etc/systemd/system/star-daemon.service"
        WORKING_DIR=$(pwd)
        
        sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Star-Daemon - GitHub starring notification daemon
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORKING_DIR
Environment="PATH=$WORKING_DIR/venv/bin"
ExecStart=$WORKING_DIR/venv/bin/python star-daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        # Set up Python environment if not exists
        if [ ! -d "venv" ]; then
            python3 -m venv venv
            source venv/bin/activate
            pip install -r requirements.txt
        fi
        
        sudo systemctl daemon-reload
        sudo systemctl enable star-daemon
        sudo systemctl start star-daemon
        
        echo ""
        echo "✅ systemd service installed and started!"
        echo "📊 View logs: sudo journalctl -u star-daemon -f"
        echo "🔄 Restart: sudo systemctl restart star-daemon"
        echo "🛑 Stop: sudo systemctl stop star-daemon"
        ;;
    *)
        echo "Invalid option. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "=============================="
echo "🎉 Setup Complete!"
echo "=============================="
echo ""
echo "Next steps:"
echo "1. ⭐ Star a repository on GitHub to test"
echo "2. 📊 Check the logs to verify it's working"
echo "3. 📚 Read the README.md for advanced configuration"
echo ""
echo "For support, visit: https://github.com/ChiefGyk3D/Star-Daemon"
echo ""
