# Star-Daemon Quick Reference

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/ChiefGyk3D/Star-Daemon.git
cd Star-Daemon

# Run setup script
./setup.sh

# Or manual Docker setup
cp .env.example .env
# Edit .env with your credentials
docker-compose up -d
```

## 📋 Common Commands

### Docker Commands
```bash
# Navigate to docker directory
cd docker

# Start daemon
docker-compose up -d

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build
```

### Local Python Commands
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run daemon
python star-daemon.py

# Run with debug logging
LOG_LEVEL=DEBUG python star-daemon.py
```

### systemd Commands
```bash
# Start
sudo systemctl start star-daemon

# Stop
sudo systemctl stop star-daemon

# Restart
sudo systemctl restart star-daemon

# View status
sudo systemctl status star-daemon

# View logs
sudo journalctl -u star-daemon -f

# Enable on boot
sudo systemctl enable star-daemon
```

## ⚙️ Configuration Quick Reference

### Required for All Setups
```bash
GITHUB_ACCESS_TOKEN=your_github_token_here
```

### Platform Enable/Disable
```bash
MASTODON_ENABLED=true|false
BLUESKY_ENABLED=true|false
DISCORD_ENABLED=true|false
MATRIX_ENABLED=true|false
```

### Core Settings
```bash
CHECK_INTERVAL=60          # Seconds between checks
LOG_LEVEL=INFO            # DEBUG, INFO, WARNING, ERROR
MESSAGE_TEMPLATE="..."    # Custom message format
```

## 🔧 Platform Setup Quick Links

### GitHub
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `user`
4. Copy token to `GITHUB_ACCESS_TOKEN`

### Mastodon
1. Go to your instance → Preferences → Development
2. Create new application
3. Copy credentials to `.env`

### BlueSky
1. Go to https://bsky.app/settings/app-passwords
2. Create app password
3. Copy to `BLUESKY_APP_PASSWORD`

### Discord
1. Go to Server Settings → Integrations → Webhooks
2. Create webhook
3. Copy URL to `DISCORD_WEBHOOK_URL`

### Matrix
1. Get your credentials from your Matrix client
2. Add to `.env` file

## 🐛 Troubleshooting

### "No platforms enabled" error
→ Enable at least one platform in `.env`

### Twitter/X not working
→ Twitter/X support has been removed. Use Mastodon or BlueSky instead.

### Import errors
→ Install dependencies: `pip install -r requirements.txt`

### Docker container exits
→ Check logs: `cd docker && docker-compose logs`

### Configuration not loading
→ Ensure `.env` is in the same directory as `star-daemon.py`

### Rate limiting
→ Increase `CHECK_INTERVAL` in `.env`

## 📊 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_ACCESS_TOKEN` | Yes | - | GitHub Personal Access Token |
| `CHECK_INTERVAL` | No | 60 | Check interval in seconds |
| `LOG_LEVEL` | No | INFO | Logging level |
| `MASTODON_ENABLED` | No | false | Enable Mastodon |
| `MASTODON_API_BASE_URL` | If enabled | - | Mastodon instance URL |
| `MASTODON_ACCESS_TOKEN` | If enabled | - | Mastodon access token |
| `BLUESKY_ENABLED` | No | false | Enable BlueSky |
| `BLUESKY_HANDLE` | If enabled | - | BlueSky handle |
| `BLUESKY_APP_PASSWORD` | If enabled | - | BlueSky app password |
| `DISCORD_ENABLED` | No | false | Enable Discord |
| `DISCORD_WEBHOOK_URL` | If enabled | - | Discord webhook URL |
| `MATRIX_ENABLED` | No | false | Enable Matrix |
| `MATRIX_HOMESERVER` | If enabled | - | Matrix homeserver URL |
| `MATRIX_USER_ID` | If enabled | - | Matrix user ID |
| `MATRIX_PASSWORD` | If enabled | - | Matrix password |
| `MATRIX_ROOM_ID` | If enabled | - | Matrix room ID |

## 🔒 Security Checklist

- [ ] Never commit `.env` file
- [ ] Use app-specific passwords where available
- [ ] Enable Snyk scanning in repository
- [ ] Keep dependencies updated
- [ ] Use minimal GitHub token scopes
- [ ] Run Docker as non-root user
- [ ] Review logs for suspicious activity

## 📚 Documentation

- [README.md](README.md) - Full documentation
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [SECURITY.md](SECURITY.md) - Security policies
- [MIGRATION.md](MIGRATION.md) - Migration guide from v1.x
- [CHANGELOG.md](CHANGELOG.md) - Version history

## 🆘 Getting Help

- Issues: https://github.com/ChiefGyk3D/Star-Daemon/issues
- Discussions: https://github.com/ChiefGyk3D/Star-Daemon/discussions

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

**Star-Daemon** - Multi-platform GitHub starring notifications
Made with ❤️ by [ChiefGyk3D](https://github.com/ChiefGyk3D)
