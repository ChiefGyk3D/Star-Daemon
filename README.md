# Star-Daemon 🌟# Star and Toot



**Multi-platform GitHub starring notification daemon**## GitHub Starred Repo Notifier for Mastodon



Star-Daemon monitors your GitHub starred repositories and automatically posts updates to multiple social platforms including Mastodon, BlueSky, Discord, and Matrix."Star and Toot" is a bot that monitors when you star new repositories on GitHub and posts a status update ("Toot") on your Mastodon account. As a secondary feature, it can also post to Twitter. However, we emphasize a Mastodon-first approach to microblogging in this project.



[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker)](https://www.docker.com/)## Setup

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

1. Clone this repository.

## 🚀 Features2. Install the necessary dependencies using pip:



- **Multi-Platform Support**: Post to Mastodon, BlueSky, Discord, and Matrix simultaneously```

- **Dockerized**: Easy deployment with Docker and Docker Composepip install -r requirements.txt

- **Secure Configuration**: Supports both `.env` files and Doppler secrets management```

- **Flexible**: Enable/disable platforms individually

- **Customizable**: Template-based message formatting3. Obtain your GitHub Personal Access Token and Mastodon API Access Token.

- **Reliable**: Automatic retries and error handling4. Create a config.ini file in the project directory based on config_template.ini and add your GitHub and Mastodon API credentials:

- **Lightweight**: Minimal resource usage

- **Open Source**: MIT licensed```

[GitHub]

> **Note**: Twitter/X support has been removed due to significant API changes and the restrictive access_token = your_github_token

> pricing model of their free tier. The platform is no longer used by the maintainer. 

> We recommend using Mastodon or BlueSky as alternatives with better API support.[Mastodon]

access_token = your_access_token_here

## 📋 Requirementsapi_base_url = https://your.mastodon.instance

client_id = your_client_id_here

- Python 3.11+client_secret = your_client_secret_here

- GitHub Personal Access Token

- At least one platform account (Mastodon, BlueSky, Discord, or Matrix)[Twitter]

- Docker (optional, for containerized deployment)enable_twitter = false

consumer_key = your_consumer_key

## 🔧 Installationconsumer_secret = your_consumer_secret

access_token = your_access_token

### Option 1: Docker (Recommended)access_token_secret = your_access_token_secret

```

1. **Clone the repository**

   ```bash5. Run the bot:

   git clone https://github.com/ChiefGyk3D/Star-Daemon.git

   cd Star-Daemon```

   ```    python star-and-toot.py

```

2. **Configure environment**

   ```bash## Running as a systemd Service

   cp .env.example .env

   nano .env  # Edit with your credentialsIf you are running this bot on a system with systemd, you can configure it as a service so it starts automatically on system boot. Follow these steps:

   ```

1. Create a systemd service file, e.g., star-and-toot.service. Service files are typically stored in /etc/systemd/system/:

3. **Run with Docker Compose**

   ```bash```

   cd dockersudo nano /etc/systemd/system/star-and-toot.service

   docker-compose up -d```

   ```

2. In the service file, add the following content (replace user and /path/to/script with your actual username and the absolute path to your Python script):

4. **View logs**

   ```bash```

   docker-compose logs -f[Unit]

   ```Description=Star and Toot GitHub-Mastodon integration



### Option 2: Local Installation[Service]

ExecStart=/usr/bin/python3 /path/to/star-and-toot.py

1. **Clone the repository**User=user

   ```bashRestart=always

   git clone https://github.com/ChiefGyk3D/Star-Daemon.git

   cd Star-Daemon[Install]

   ```WantedBy=multi-user.target

```

2. **Create virtual environment**

   ```bash3. Reload the systemd manager configuration:

   python3 -m venv venv

   source venv/bin/activate  # On Windows: venv\Scripts\activate```

   ```sudo systemctl daemon-reload

```

3. **Install dependencies**

   ```bash4. Start the service:

   pip install -r requirements.txt

   ``````

sudo systemctl start star-and-toot.service

4. **Configure environment**```

   ```bash

   cp .env.example .env5. Enable the service to start on boot:

   nano .env  # Edit with your credentials

   ``````

sudo systemctl enable star-and-toot.service

5. **Run the daemon**```

   ```bash

   python star-daemon.py## Configuration

   ```

All configuration is done through the config.ini file. You'll need to provide your GitHub and Mastodon API credentials:

### Option 3: systemd Service

- GitHub.access_token: Your GitHub Personal Access Token.

1. **Create service file**- Mastodon.access_token: Your Mastodon API Access Token.

   ```bash- Mastodon.api_base_url: Your Mastodon instance URL.

   sudo nano /etc/systemd/system/star-daemon.service

   ```Remember to replace 'your_github_token', 'your_mastodon_token', and 'your_mastodon_instance_url' with your actual tokens and URLs in the config.ini file.

Contributing

2. **Add configuration**

   ```ini## Support

   [Unit]

   Description=Star-Daemon - GitHub starring notification daemonYou can also tip the author with the following cryptocurrency addresses:

   After=network.target

    Bitcoin: bc1q5grpa7ramcct4kjmwexfrh74dvjuw9wczn4w2f

   [Service]    Monero: 85YxVz8Xd7sW1xSiyzUC5PNqSjYLYk4W8FMERVkvznR38jGTBEViWQSLCnzRYZjmxgUkUKGhxTt2JSFNpJuAqghQLhHgPS5

   Type=simple    PIVX: DS1CuBQkiidwwPhkfVfQAGUw4RTWPnBXVM

   User=yourusername    Ethereum: 0x2a460d48ab404f191b14e9e0df05ee829cbf3733

   WorkingDirectory=/path/to/Star-Daemon

   Environment="PATH=/path/to/Star-Daemon/venv/bin"## Connect

   ExecStart=/path/to/Star-Daemon/venv/bin/python star-daemon.py- [ChiefGyk3D's Mastodon Account](https://social.chiefgyk3d.com/@chiefgyk3d)

   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable star-daemon
   sudo systemctl start star-daemon
   sudo systemctl status star-daemon
   ```

## ⚙️ Configuration

### Core Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CHECK_INTERVAL` | No | 60 | Check interval in seconds |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

### GitHub Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_ACCESS_TOKEN` | **Yes** | GitHub Personal Access Token with `repo` and `user` scopes |
| `GITHUB_USERNAME` | No | Monitor specific user (defaults to authenticated user) |

[How to create a GitHub Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

### Platform Configuration

#### Mastodon

| Variable | Required | Description |
|----------|----------|-------------|
| `MASTODON_ENABLED` | No | Set to `true` to enable |
| `MASTODON_API_BASE_URL` | Yes* | Your Mastodon instance URL (e.g., `https://mastodon.social`) |
| `MASTODON_ACCESS_TOKEN` | Yes* | Mastodon access token |
| `MASTODON_CLIENT_ID` | No | Optional client ID |
| `MASTODON_CLIENT_SECRET` | No | Optional client secret |

*Required if Mastodon is enabled

#### BlueSky

| Variable | Required | Description |
|----------|----------|-------------|
| `BLUESKY_ENABLED` | No | Set to `true` to enable |
| `BLUESKY_HANDLE` | Yes* | Your BlueSky handle (e.g., `user.bsky.social`) |
| `BLUESKY_APP_PASSWORD` | Yes* | BlueSky app password (not your main password!) |

*Required if BlueSky is enabled

[How to create a BlueSky app password](https://bsky.app/settings/app-passwords)

#### Discord

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_ENABLED` | No | Set to `true` to enable |
| `DISCORD_WEBHOOK_URL` | Yes* | Discord webhook URL |

*Required if Discord is enabled

#### Matrix

| Variable | Required | Description |
|----------|----------|-------------|
| `MATRIX_ENABLED` | No | Set to `true` to enable |
| `MATRIX_HOMESERVER` | Yes* | Matrix homeserver URL (e.g., `https://matrix.org`) |
| `MATRIX_USER_ID` | Yes* | Matrix user ID (e.g., `@user:matrix.org`) |
| `MATRIX_PASSWORD` | Yes** | Matrix password |
| `MATRIX_ACCESS_TOKEN` | Yes** | Matrix access token (alternative to password) |
| `MATRIX_ROOM_ID` | Yes* | Room ID to post to (e.g., `!roomid:matrix.org`) |

*Required if Matrix is enabled  
**Either password or access token required

### Doppler Integration (Optional)

For enhanced security, use [Doppler](https://doppler.com) for secrets management:

1. **Install Doppler CLI**
   ```bash
   curl -sLf https://cli.doppler.com/install.sh | sh
   ```

2. **Set up Doppler token**
   ```bash
   export DOPPLER_TOKEN=your_doppler_token
   ```

3. **Run with Doppler**
   ```bash
   doppler run -- python star-daemon.py
   ```

4. **Docker Compose with Doppler**
   Uncomment the Doppler section in `docker/docker-compose.yml`

## 📝 Message Customization

Customize notification messages using the `MESSAGE_TEMPLATE` variable:

```bash
MESSAGE_TEMPLATE="🌟 Just starred: {name} - {url}"
```

Available placeholders:
- `{url}` - Repository URL
- `{name}` - Repository full name (owner/repo)
- `{description}` - Repository description

## 🏗️ Project Structure

```
Star-Daemon/
├── docker/                    # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
├── docs/                      # Documentation
│   ├── CONTRIBUTING.md
│   ├── SECURITY.md
│   ├── MIGRATION.md
│   ├── CHANGELOG.md
│   ├── QUICKSTART.md
│   └── SETUP_CHECKLIST.md
├── .github/workflows/         # CI/CD automation
├── connectors/                # Platform connectors
│   ├── base.py
│   ├── mastodon_connector.py
│   ├── bluesky_connector.py
│   ├── discord_connector.py
│   └── matrix_connector.py
├── star-daemon.py             # Main daemon
├── config.py                  # Configuration management
├── .env.example               # Configuration template
└── requirements.txt           # Python dependencies
```

### Architecture

Star-Daemon uses a modular connector architecture where each platform is independent and can be enabled/disabled via configuration. The `.github/workflows/` folder contains GitHub Actions for automated testing and Docker builds.

## 🔒 Security

- **Secrets Management**: Supports Doppler or `.env` files
- **Container Security**: Non-root user in Docker
- **Pinned Dependencies**: Locked versions in `requirements.txt`
- **Hash Verification**: Support for `pip install --require-hashes`
- **Optional Security Scanning**: Snyk integration available (requires manual setup - see `docs/WORKFLOWS_EXPLAINED.md`)

### Generating Locked Requirements with Hashes

For maximum security (Shai-Hulud mitigations):

```bash
pip install pip-tools
pip-compile --generate-hashes requirements.in -o requirements-lock.txt
pip install -r requirements-lock.txt --require-hashes
```

## 🐛 Troubleshooting

### Common Issues

**Q: "No platforms enabled" error**  
A: Enable at least one platform by setting `*_ENABLED=true` in your `.env` file

**Q: GitHub rate limiting**  
A: Increase `CHECK_INTERVAL` to reduce API calls

**Q: Matrix connection fails**  
A: Ensure you're using an app password or access token, not your main password

**Q: Docker container exits immediately**  
A: Check logs with `cd docker && docker-compose logs` - likely a configuration error

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG
```

## 📚 Documentation

- [CONTRIBUTING.md](docs/CONTRIBUTING.md) - Contribution guidelines
- [SECURITY.md](docs/SECURITY.md) - Security policy and reporting
- [MIGRATION.md](docs/MIGRATION.md) - Migration guide from v1.x
- [CHANGELOG.md](docs/CHANGELOG.md) - Version history
- [QUICKSTART.md](docs/QUICKSTART.md) - Quick reference guide
- [WORKFLOWS_EXPLAINED.md](docs/WORKFLOWS_EXPLAINED.md) - GitHub Actions guide

## 🤝 Contributing

Contributions are welcome! Please see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original project: [star-and-toot](https://github.com/ChiefGyk3D/star-and-toot)
- Inspired by the need for multi-platform social media integration
- Built with love for the open source community

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/ChiefGyk3D/Star-Daemon/issues)
- **Security**: See [docs/SECURITY.md](docs/SECURITY.md)

---

Made with ❤️ by [ChiefGyk3D](https://github.com/ChiefGyk3D)
