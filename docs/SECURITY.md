# Security Policy

## Supported Versions

Currently supported versions of Star-Daemon:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x.x   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

### Preferred Method: GitHub Security Advisories

1. Go to the [Security tab](https://github.com/ChiefGyk3D/Star-Daemon/security)
2. Click "Report a vulnerability"
3. Fill out the form with details about the vulnerability

### Alternative Method: Email

Send an email to: **security@[maintainer-domain]** (replace with actual contact)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Status Updates**: Every 7 days until resolved
- **Resolution**: Depends on severity and complexity

## Severity Levels

We follow the [CVSS v3.1](https://www.first.org/cvss/v3.1/specification-document) scoring system:

- **Critical (9.0-10.0)**: Immediate attention, patch within 24-48 hours
- **High (7.0-8.9)**: High priority, patch within 7 days
- **Medium (4.0-6.9)**: Medium priority, patch within 30 days
- **Low (0.1-3.9)**: Low priority, patch in next release

## Security Measures

### Current Security Features

1. **Secrets Management**
   - Support for Doppler secrets management
   - Environment variable-based configuration
   - No hardcoded credentials

2. **Dependency Management**
   - Snyk integration for automated vulnerability scanning
   - Pinned dependency versions
   - Hash verification support (`--require-hashes`)

3. **Container Security**
   - Non-root user in Docker containers
   - Minimal base image (python:3.11-slim)
   - No unnecessary packages

4. **Code Security**
   - Input validation
   - Error handling without information leakage
   - Secure API token handling

### Security Best Practices for Users

1. **API Tokens and Credentials**
   - Use environment variables or Doppler for secrets
   - Never commit `.env` files
   - Use app-specific passwords where available
   - Rotate tokens regularly

2. **Docker Security**
   - Run containers with limited resources
   - Use read-only filesystem where possible
   - Keep Docker images updated

3. **Network Security**
   - Use HTTPS for all API endpoints
   - Implement firewall rules if needed
   - Monitor outbound connections

4. **Access Control**
   - Limit GitHub token scopes to minimum required
   - Use separate service accounts
   - Implement principle of least privilege

## Vulnerability Disclosure Policy

### Responsible Disclosure

We follow responsible disclosure practices:

1. **Private Disclosure**: Report received privately
2. **Acknowledgment**: Reporter acknowledged within 48 hours
3. **Assessment**: Vulnerability assessed and confirmed
4. **Development**: Fix developed and tested
5. **Coordinated Release**: 
   - Security advisory published
   - Fixed version released
   - CVE requested if applicable
6. **Public Disclosure**: After fix is available (typically 90 days)

### Credit

We believe in giving credit where it's due:

- Security researchers will be credited in release notes
- Names listed in SECURITY.md (with permission)
- Recognition in GitHub Security Advisories

## Security Scanning

### Automated Scanning

Star-Daemon uses:

1. **Snyk** - Dependency vulnerability scanning
   - Automated PR checks
   - Weekly scans
   - Email notifications

2. **Dependabot** - Automated dependency updates
   - Security updates
   - Version updates

### Manual Audits

Periodic security audits cover:
- Code review for common vulnerabilities
- Dependency analysis
- Configuration security
- Container security

## Known Security Considerations

### API Rate Limiting

Star-Daemon makes periodic API calls. Consider:
- GitHub rate limits: 5,000 requests/hour (authenticated)
- Platform-specific rate limits
- Implement appropriate `CHECK_INTERVAL` values

### Credential Storage

**Never store credentials in:**
- Source code
- Git repository
- Public documentation
- Log files
- Error messages

**Always use:**
- Environment variables
- Doppler or similar secrets management
- Secure key storage systems

### Log Sanitization

Logs are sanitized to prevent credential leakage:
- API tokens are never logged
- Passwords are never logged
- URLs with tokens are sanitized

## Security Updates

### Notification Channels

Stay informed about security updates:

1. **GitHub Watch**: Click "Watch" → "Custom" → "Security alerts"
2. **Release Notes**: Check release notes for security fixes
3. **Security Advisories**: Subscribe to GitHub Security Advisories
4. **Email**: Register for security notifications (if available)

### Update Process

When a security update is released:

1. **Review the advisory**: Understand the impact
2. **Test in staging**: If applicable
3. **Update immediately**: For critical/high severity
4. **Update soon**: For medium/low severity

```bash
# Pull latest version
git pull origin main

# Rebuild Docker containers
docker-compose pull
docker-compose up -d --build

# Or update Python dependencies
pip install -r requirements.txt --upgrade
```

## Compliance

Star-Daemon aims to follow:

- OWASP Top 10 best practices
- CWE/SANS Top 25 mitigations
- NIST Cybersecurity Framework guidelines

## Security Checklist for Deployments

- [ ] Secrets stored in environment variables or Doppler
- [ ] `.env` file not committed to version control
- [ ] API tokens have minimal required scopes
- [ ] Container running as non-root user
- [ ] Dependencies up to date
- [ ] Snyk scanning enabled
- [ ] Logs monitored for suspicious activity
- [ ] Regular security updates applied
- [ ] Network access restricted as needed
- [ ] Backup and recovery plan in place

## Questions?

For security questions that are not vulnerabilities:
- Open a [Discussion](https://github.com/ChiefGyk3D/Star-Daemon/discussions)
- Check existing [Issues](https://github.com/ChiefGyk3D/Star-Daemon/issues)

---

Last updated: October 26, 2025
