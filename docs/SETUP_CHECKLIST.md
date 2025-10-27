# Star-Daemon Setup Checklist

Use this checklist to ensure everything is properly configured after the overhaul.

## 📋 Pre-Deployment Checklist

### Repository Setup
- [ ] Repository renamed to "Star-Daemon" (or keep current name)
- [ ] Repository description updated
- [ ] Topics/tags added (docker, python, mastodon, bluesky, discord, matrix, github-stars)
- [ ] Default branch set to `main`

### GitHub Settings
- [ ] **Settings → Secrets → Actions**
  - [ ] Add `SNYK_TOKEN` (get from https://snyk.io)
  - [ ] Add `DOCKER_USERNAME` (if publishing to Docker Hub)
  - [ ] Add `DOCKER_PASSWORD` (if publishing to Docker Hub)

- [ ] **Settings → Security**
  - [ ] Enable Dependabot alerts
  - [ ] Enable Dependabot security updates
  - [ ] Enable Secret scanning

- [ ] **Settings → Code security and analysis**
  - [ ] Enable Dependency graph
  - [ ] Enable Code scanning (for Snyk SARIF uploads)

- [ ] **Settings → General**
  - [ ] Enable Issues
  - [ ] Enable Discussions (optional)
  - [ ] Disable Wiki (documentation is in repo)

### Branch Protection (Optional but Recommended)
- [ ] **Settings → Branches → Add rule for `main`**
  - [ ] Require pull request reviews
  - [ ] Require status checks (lint, test, security-scan)
  - [ ] Require branches to be up to date
  - [ ] Include administrators

## 🔧 Local Setup Checklist

### Initial Configuration
- [ ] Clone/update repository
- [ ] Run `./setup.sh` or manual setup
- [ ] Create `.env` file from `.env.example`
- [ ] Add GitHub Personal Access Token
- [ ] Configure at least one platform (Mastodon, BlueSky, Discord, or Matrix)

### Platform Credentials

#### GitHub
- [ ] Create Personal Access Token at https://github.com/settings/tokens
- [ ] Select scopes: `repo`, `user`
- [ ] Add to `.env` as `GITHUB_ACCESS_TOKEN`

#### Mastodon (if using)
- [ ] Go to your instance → Preferences → Development
- [ ] Create new application
- [ ] Copy credentials to `.env`
- [ ] Set `MASTODON_ENABLED=true`

#### BlueSky (if using)
- [ ] Create app password at https://bsky.app/settings/app-passwords
- [ ] Copy to `.env` as `BLUESKY_APP_PASSWORD`
- [ ] Add your handle as `BLUESKY_HANDLE`
- [ ] Set `BLUESKY_ENABLED=true`

#### Discord (if using)
- [ ] Create webhook in Discord server settings
- [ ] Copy webhook URL to `DISCORD_WEBHOOK_URL`
- [ ] Set `DISCORD_ENABLED=true`

#### Matrix (if using)
- [ ] Get homeserver URL, user ID, password/token
- [ ] Get room ID where you want to post
- [ ] Add all to `.env`
- [ ] Set `MATRIX_ENABLED=true`

## 🐳 Docker Deployment Checklist

- [ ] Docker and Docker Compose installed
- [ ] `.env` file configured
- [ ] Run `docker-compose up -d`
- [ ] Check logs: `docker-compose logs -f`
- [ ] Verify all platforms connect successfully
- [ ] Star a test repository on GitHub
- [ ] Verify posts appear on configured platforms

## 🐍 Local Python Deployment Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created: `python3 -m venv venv`
- [ ] Virtual environment activated
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file configured
- [ ] Run `python star-daemon.py`
- [ ] Verify connections
- [ ] Test with a starred repository

## ⚙️ systemd Service Deployment Checklist

- [ ] Python virtual environment set up
- [ ] Service file created at `/etc/systemd/system/star-daemon.service`
- [ ] Service file configured with correct paths
- [ ] Daemon reloaded: `sudo systemctl daemon-reload`
- [ ] Service enabled: `sudo systemctl enable star-daemon`
- [ ] Service started: `sudo systemctl start star-daemon`
- [ ] Service status checked: `sudo systemctl status star-daemon`
- [ ] Logs verified: `sudo journalctl -u star-daemon -f`

## 🔒 Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] `.env` file is NOT committed to repository
- [ ] Snyk token added to GitHub secrets
- [ ] GitHub security features enabled
- [ ] API tokens have minimal required scopes
- [ ] Using app-specific passwords where available
- [ ] Docker running as non-root user
- [ ] Review SECURITY.md

## 🧪 Testing Checklist

- [ ] All Python files compile: `python -m py_compile *.py connectors/*.py`
- [ ] Configuration loads without errors
- [ ] All enabled connectors initialize successfully
- [ ] Connection tests pass for all platforms
- [ ] Star a repository on GitHub
- [ ] Verify posts appear on all enabled platforms
- [ ] Check error handling (try invalid credentials)
- [ ] Verify logging works correctly
- [ ] Test restart/recovery

## 📚 Documentation Checklist

- [ ] README.md reviewed and accurate
- [ ] CONTRIBUTING.md in place
- [ ] SECURITY.md in place
- [ ] MIGRATION.md in place (if applicable)
- [ ] CHANGELOG.md updated
- [ ] LICENSE file present
- [ ] All documentation links working

## 🚀 CI/CD Checklist

- [ ] `.github/workflows/ci-cd.yml` present
- [ ] `.github/workflows/snyk.yml` present
- [ ] `.github/workflows/dependency-update.yml` present
- [ ] GitHub Actions enabled
- [ ] First workflow run successful
- [ ] Snyk integration working
- [ ] Docker build workflow successful (if using)

## 📊 Monitoring Checklist

- [ ] Logs are accessible and readable
- [ ] Error notifications configured (if desired)
- [ ] Monitoring GitHub rate limits
- [ ] Snyk weekly scans running
- [ ] Dependabot alerts reviewed regularly

## 🎯 Production Readiness Checklist

- [ ] All tests passing
- [ ] All platforms tested
- [ ] Documentation complete
- [ ] Security scanning enabled
- [ ] Backup plan in place
- [ ] Rollback procedure documented (MIGRATION.md)
- [ ] Support channels identified (Issues, Discussions)
- [ ] Resource limits set (Docker)
- [ ] Log rotation configured

## 📝 Post-Deployment Checklist

- [ ] Monitor for first 24 hours
- [ ] Verify scheduled checks are working
- [ ] Check platform posts are successful
- [ ] Review logs for any errors
- [ ] Adjust `CHECK_INTERVAL` if needed
- [ ] Document any custom configuration
- [ ] Share with community (optional)

## 🎉 Optional Enhancements

- [ ] Set up Doppler for advanced secrets management
- [ ] Configure custom message templates
- [ ] Add monitoring/alerting (e.g., Prometheus, Grafana)
- [ ] Set up log aggregation (e.g., ELK stack)
- [ ] Create custom Docker image and publish
- [ ] Add more platforms (create custom connectors)
- [ ] Contribute improvements back to project

## 🐛 Troubleshooting Reference

If you encounter issues, check:

1. **Configuration**
   - `.env` file exists and is readable
   - All required variables are set
   - No syntax errors in `.env`

2. **Credentials**
   - GitHub token is valid and has correct scopes
   - Platform credentials are correct
   - API endpoints are accessible

3. **Logs**
   - Check logs for specific error messages
   - Enable DEBUG logging: `LOG_LEVEL=DEBUG`
   - Review platform-specific errors

4. **Network**
   - Internet connection is stable
   - No firewall blocking API calls
   - Rate limits not exceeded

5. **Documentation**
   - Review README.md
   - Check QUICKSTART.md
   - See MIGRATION.md if upgrading

## 📞 Getting Help

- [ ] Read documentation first
- [ ] Search existing issues
- [ ] Check discussions
- [ ] Create issue with full details
- [ ] Include logs (redact secrets!)

---

## ✅ Final Verification

Once all checklists are complete:

1. Star a repository on GitHub
2. Wait for `CHECK_INTERVAL` seconds
3. Verify posts appear on all enabled platforms
4. Check logs for any errors
5. Celebrate! 🎉

**Your Star-Daemon is now ready for production!** 🌟

---

Last updated: October 26, 2025
