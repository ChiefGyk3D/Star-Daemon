# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2025-10-26

### Removed
- **Twitter/X Integration**: Removed due to significant API changes and restrictive free tier pricing
  - The Twitter API has changed substantially since the original implementation
  - The free tier is too limiting for this use case
  - The maintainer no longer uses Twitter/X
  - Users are encouraged to use Mastodon or BlueSky instead

### Changed
- **Project Structure**: Reorganized for better maintainability
  - Docker files moved to `docker/` directory
  - Documentation moved to `docs/` directory
  - Updated paths in docker-compose.yml and documentation

## [2.0.0] - 2025-10-26

### 🎉 Major Release - Project Rebranded as Star-Daemon

This is a complete overhaul of the original star-and-toot project with significant improvements and new features.

### Added
- **Multi-Platform Support**
  - BlueSky integration via AT Protocol
  - Discord webhook support with rich embeds
  - Matrix protocol support
  - Maintained Mastodon support with improvements
  
- **Docker Support**
  - Complete Dockerfile for containerization
  - docker-compose.yml for easy deployment
  - Non-root user for enhanced security
  - Health checks and resource limits
  
- **Configuration Management**
  - Environment variable-based configuration (.env)
  - Doppler secrets management integration
  - Flexible platform enable/disable options
  - Customizable message templates
  
- **Architecture Improvements**
  - Modular connector architecture
  - Base connector class for easy extension
  - Independent platform connectors
  - Better error handling and logging
  
- **Security Features**
  - Snyk integration for dependency scanning
  - Pinned dependencies with version locking
  - Support for hash verification
  - GitHub Actions workflows for CI/CD
  - Security scanning automation
  
- **Documentation**
  - Comprehensive README with setup guides
  - CONTRIBUTING.md with contribution guidelines
  - SECURITY.md with security policies
  - MIGRATION.md for upgrading from v1.x
  - Platform-specific setup guides
  
- **Developer Tools**
  - Automated setup script (setup.sh)
  - GitHub Actions workflows
  - Dependency update automation
  - Code quality checks
  
### Changed
- **Breaking**: Configuration format changed from config.ini to .env
- **Breaking**: Main script renamed from star-and-toot.py to star-daemon.py
- **Breaking**: Project name changed to Star-Daemon
- Improved logging with configurable levels
- Enhanced error messages and debugging
- Better rate limit handling
- Improved systemd service template

### Deprecated
- config.ini format (use .env instead)

### Removed
- config_template.ini (replaced by .env.example)

### Fixed
- Mastodon API compatibility with newer versions
- Rate limiting issues with GitHub API
- Error handling for network failures
- Log rotation and management

### Security
- Non-root Docker container execution
- Secrets management via Doppler
- Environment variable protection
- Automated security scanning
- Dependency vulnerability monitoring

## [1.x.x] - Legacy

### Original star-and-toot Features
- GitHub starred repository monitoring
- Mastodon posting
- Optional Twitter posting
- config.ini based configuration
- Basic systemd service support

---

## Migration Guide

For detailed migration instructions from v1.x to v2.0, see [MIGRATION.md](MIGRATION.md).

## Upgrade Instructions

### From v1.x to v2.0

1. **Backup your configuration**
   ```bash
   cp config.ini config.ini.backup
   ```

2. **Pull the latest version**
   ```bash
   git pull origin main
   ```

3. **Create new configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Install new dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Test the new version**
   ```bash
   python star-daemon.py
   ```

For detailed instructions, see [MIGRATION.md](MIGRATION.md).

## Support

- **Issues**: [GitHub Issues](https://github.com/ChiefGyk3D/Star-Daemon/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ChiefGyk3D/Star-Daemon/discussions)
- **Security**: See [SECURITY.md](SECURITY.md)
