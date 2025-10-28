# Migration Guide: star-and-toot → Star-Daemon

This guide helps you migrate from the original `star-and-toot` project to the new `Star-Daemon`.

## What's Changed?

### Project Rename
- **Old**: star-and-toot
- **New**: Star-Daemon

### Major Changes

1. **Configuration System**
   - ❌ Old: `config.ini` file
   - ✅ New: `.env` file with optional Doppler support

2. **Platform Support**
   - ✅ Added: BlueSky
   - ✅ Added: Discord
   - ✅ Added: Matrix
   - ✅ Improved: Mastodon (better error handling)
   - 📝 Maintained: Twitter/X (legacy support)

3. **Architecture**
   - ✅ Modular connector system
   - ✅ Better error handling
   - ✅ Improved logging

4. **Deployment**
   - ✅ Docker support
   - ✅ Docker Compose orchestration
   - ✅ Enhanced systemd service template

5. **Security**
   - ✅ Doppler integration
   - ✅ Snyk security scanning
   - ✅ Pinned dependencies with hash support
   - ✅ Non-root Docker user

## Migration Steps

### Step 1: Backup Current Configuration

```bash
# Backup your old config
cp config.ini config.ini.backup
```

### Step 2: Clone Star-Daemon

```bash
cd ..
git clone https://github.com/ChiefGyk3D/Star-Daemon.git
cd Star-Daemon
```

### Step 3: Convert Configuration

Copy your old `config.ini` values to the new `.env` file:

#### Old config.ini:
```ini
[GitHub]
access_token = ghp_xxxxx

[Mastodon]
access_token = your_token
api_base_url = https://mastodon.social
client_id = your_client_id
client_secret = your_client_secret

[Twitter]
enable_twitter = true
consumer_key = xxx
consumer_secret = xxx
access_token = xxx
access_token_secret = xxx
```

#### New .env:
```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your values:
GITHUB_ACCESS_TOKEN=ghp_xxxxx

MASTODON_ENABLED=true
MASTODON_API_BASE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=your_token
MASTODON_CLIENT_ID=your_client_id
MASTODON_CLIENT_SECRET=your_client_secret

TWITTER_ENABLED=true
TWITTER_API_KEY=xxx
TWITTER_API_SECRET=xxx
TWITTER_ACCESS_TOKEN=xxx
TWITTER_ACCESS_TOKEN_SECRET=xxx
```

### Step 4: Install Dependencies

#### Docker Method (Recommended):
```bash
docker-compose up -d
```

#### Local Method:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 5: Test Configuration

```bash
# Docker
docker-compose logs -f

# Local
python star-daemon.py
```

### Step 6: Update systemd Service (if applicable)

If you're using systemd, update your service file:

```bash
sudo nano /etc/systemd/system/star-daemon.service
```

Update the paths:
```ini
[Unit]
Description=Star-Daemon - GitHub starring notification daemon
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/Star-Daemon
Environment="PATH=/path/to/Star-Daemon/venv/bin"
ExecStart=/path/to/Star-Daemon/venv/bin/python star-daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart star-daemon
sudo systemctl status star-daemon
```

### Step 7: Add New Platforms (Optional)

Take advantage of new platform support:

#### BlueSky
```bash
# Add to .env
BLUESKY_ENABLED=true
BLUESKY_HANDLE=your.handle.bsky.social
BLUESKY_APP_PASSWORD=your_app_password
```

#### Discord
```bash
# Add to .env
DISCORD_ENABLED=true
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook
```

#### Matrix
```bash
# Add to .env
MATRIX_ENABLED=true
MATRIX_HOMESERVER=https://matrix.org
MATRIX_USER_ID=@user:matrix.org
MATRIX_PASSWORD=your_password
MATRIX_ROOM_ID=!room:matrix.org
```

## Configuration Mapping

| Old (config.ini) | New (.env) | Notes |
|-----------------|------------|-------|
| `[GitHub] access_token` | `GITHUB_ACCESS_TOKEN` | Same token |
| `[Mastodon] access_token` | `MASTODON_ACCESS_TOKEN` | Same token |
| `[Mastodon] api_base_url` | `MASTODON_API_BASE_URL` | Same URL |
| `[Mastodon] client_id` | `MASTODON_CLIENT_ID` | Optional in new version |
| `[Mastodon] client_secret` | `MASTODON_CLIENT_SECRET` | Optional in new version |
| `[Twitter] enable_twitter` | `TWITTER_ENABLED` | Boolean (true/false) |
| `[Twitter] consumer_key` | `TWITTER_API_KEY` | Renamed |
| `[Twitter] consumer_secret` | `TWITTER_API_SECRET` | Renamed |
| `[Twitter] access_token` | `TWITTER_ACCESS_TOKEN` | Same |
| `[Twitter] access_token_secret` | `TWITTER_ACCESS_TOKEN_SECRET` | Same |
| N/A | `CHECK_INTERVAL` | New: configurable interval |
| N/A | `LOG_LEVEL` | New: configurable logging |

## New Features to Explore

### 1. Message Templates
Customize your messages:
```bash
MESSAGE_TEMPLATE="🌟 Just starred: {name} - {url}"
```

### 2. Doppler Integration
For enhanced security:
```bash
# Install Doppler CLI
curl -sLf https://cli.doppler.com/install.sh | sh

# Run with Doppler
doppler run -- python star-daemon.py
```

### 3. Docker Deployment
Easier deployment and management:
```bash
docker-compose up -d
docker-compose logs -f
docker-compose restart
```

### 4. Multiple Platforms
Post to multiple platforms simultaneously - just enable them all!

## Troubleshooting

### Issue: Module not found errors
**Solution**: Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Configuration not loading
**Solution**: Ensure `.env` file is in the same directory as `star-daemon.py`

### Issue: Old systemd service still running
**Solution**: Stop the old service first:
```bash
sudo systemctl stop star-and-toot
sudo systemctl disable star-and-toot
```

### Issue: Docker container won't start
**Solution**: Check logs for configuration errors:
```bash
docker-compose logs
```

## Rollback Procedure

If you need to rollback to the old version:

1. Stop Star-Daemon:
   ```bash
   # Docker
   docker-compose down
   
   # systemd
   sudo systemctl stop star-daemon
   
   # Local
   # Just Ctrl+C to stop
   ```

2. Return to old directory:
   ```bash
   cd ../star-and-toot
   ```

3. Restore backup:
   ```bash
   cp config.ini.backup config.ini
   ```

4. Restart old version:
   ```bash
   python star-and-toot.py
   ```

## Support

If you encounter issues during migration:

- Check the [README.md](README.md) for detailed setup instructions
- Review [SECURITY.md](SECURITY.md) for security best practices
- Open an [issue](https://github.com/ChiefGyk3D/Star-Daemon/issues) on GitHub
- Check existing [discussions](https://github.com/ChiefGyk3D/Star-Daemon/discussions)

## Checklist

- [ ] Backed up old configuration
- [ ] Cloned Star-Daemon repository
- [ ] Created and configured `.env` file
- [ ] Tested configuration
- [ ] Updated systemd service (if applicable)
- [ ] Verified all platforms are working
- [ ] Configured new platforms (optional)
- [ ] Stopped old service
- [ ] Started new service
- [ ] Verified in logs that everything works

---

Welcome to Star-Daemon! 🌟
