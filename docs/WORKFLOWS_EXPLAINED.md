# GitHub Workflows Explanation

## What is `.github/workflows/`?

The `.github/workflows/` directory contains **GitHub Actions** workflow files. GitHub Actions is a CI/CD (Continuous Integration/Continuous Deployment) platform that automates your software development workflows directly in your GitHub repository.

## Why Use GitHub Actions?

- ✅ **Free for public repositories** (unlimited minutes)
- ✅ **Automated testing** - Catches bugs before they reach production
- ✅ **Security scanning** - Identifies vulnerabilities in dependencies
- ✅ **Consistency** - Ensures code quality standards are met
- ✅ **Time-saving** - Automates repetitive tasks
- ✅ **Professional** - Industry-standard practice

## What Do Star-Daemon's Workflows Do?

### 1. `ci-cd.yml` - Main CI/CD Pipeline

**Triggers**: Every push and pull request to `main` or `develop` branches

**What it does**:
- **Linting**: Checks code style with Black, isort, and Flake8
- **Testing**: Validates Python syntax and imports
- **Docker Build**: Tests that Docker image builds correctly
- **Docker Publish**: Publishes to Docker Hub (only on main branch)
- **Dependency Review**: Checks for security issues in PRs

> **Note**: Security scanning with Snyk is commented out by default. To enable it, you need to:
> 1. Sign up at https://snyk.io (free for open source)
> 2. Connect your GitHub repository
> 3. Add `SNYK_TOKEN` to your repository secrets
> 4. Uncomment the security-scan job in `.github/workflows/ci-cd.yml`

**Benefits**:
- Catches syntax errors before deployment
- Ensures consistent code formatting
- Verifies Docker builds work
- Can be extended with Snyk for security scanning (optional)

### 2. ~~snyk.yml - Weekly Security Scanning~~ (Optional - Not Included)

> **Note**: Snyk integration is **optional** and requires manual setup. The workflow file is not included by default.

**If you want to add Snyk scanning:**

1. Sign up at https://snyk.io (free for open source)
2. Connect your GitHub repository to Snyk
3. Get your Snyk token
4. Add `SNYK_TOKEN` to repository secrets
5. Uncomment the security-scan job in `ci-cd.yml` or create a separate `snyk.yml` workflow

**What it would do** (if enabled):
- Scans all dependencies for known vulnerabilities
- Uploads results to GitHub Security tab
- Monitors project continuously in Snyk dashboard

**Benefits**:
- Proactive security monitoring
- Early warning of vulnerable dependencies
- Automated security alerts
- Compliance tracking

### 3. `dependency-update.yml` - Automated Dependency Updates

**Triggers**: 
- Every Monday at 6 AM UTC (scheduled)
- Can be manually triggered

**What it does**:
- Checks for newer versions of dependencies
- Creates pull requests with updates
- Labels PRs as "dependencies" and "automated"

**Benefits**:
- Keeps dependencies up-to-date
- Reduces manual maintenance
- Security patches applied faster
- Clear changelog of dependency changes

## How to Use These Workflows

### 1. Enable GitHub Actions

GitHub Actions are automatically enabled for most repositories. To verify:

1. Go to your repository on GitHub
2. Click the "Actions" tab
3. You should see the workflows listed

### 2. Required Secrets

Some workflows need secrets to function fully. Add these in:
**Settings → Secrets and variables → Actions → New repository secret**

**Optional (only if you want these features):**
- `SNYK_TOKEN` - For security scanning (requires signing up at snyk.io)
- `DOCKER_USERNAME` - For Docker Hub publishing (only if you want to publish)
- `DOCKER_PASSWORD` - For Docker Hub password/token (only if you want to publish)

> Most users don't need these secrets. The basic workflows run fine without them!

### 3. Monitoring Workflow Runs

1. Go to the "Actions" tab in your repository
2. Click on any workflow to see its runs
3. Click on a specific run to see detailed logs
4. Green checkmark ✅ = passed, Red X ❌ = failed

### 4. Viewing Security Results

Security scan results appear in:
1. **Security tab** → Code scanning alerts
2. **Pull request checks** (if running on PR)
3. **Snyk dashboard** (if you've connected your account)

## Customizing Workflows

### Change Schedule Times

Edit the cron expression in the workflow file:

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # Monday at 9 AM UTC
```

Use [crontab.guru](https://crontab.guru/) to help create cron expressions.

### Disable a Workflow

Three options:

1. **Delete the file** from `.github/workflows/`
2. **Disable in GitHub**: Actions tab → Select workflow → "..." → Disable workflow
3. **Comment out triggers** in the workflow file

### Modify What Gets Tested

Edit the workflow file directly:

```yaml
jobs:
  lint:
    name: Lint Code
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      # Add, remove, or modify steps here
```

## Understanding Workflow Status

### Badges

Add status badges to your README:

```markdown
[![CI/CD](https://github.com/ChiefGyk3D/Star-Daemon/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/ChiefGyk3D/Star-Daemon/actions/workflows/ci-cd.yml)
```

### Common Issues

**"Workflow failed"**
- Check the logs in the Actions tab
- Most common: Linting errors or failing tests
- Fix locally and push again

**"Snyk token not found"**
- This is expected! Snyk is optional and not configured by default
- Either add `SNYK_TOKEN` to repository secrets after signing up at snyk.io
- Or just ignore this - the workflow is commented out anyway

**"Docker push failed"**
- Add Docker Hub credentials to secrets
- Or remove the docker-publish job if you don't need it

## Cost and Limits

### GitHub Actions

**Public repositories**: 
- ✅ Unlimited minutes (free)
- ✅ Unlimited storage for artifacts

**Private repositories**:
- 2,000 minutes/month (free tier)
- Additional minutes available with paid plans

### Snyk

**Open source projects**:
- ✅ Free unlimited scans (if you set it up)
- ✅ Full vulnerability database
- ⚠️ Requires manual setup and configuration

**Private projects**:
- Limited free scans
- Paid plans available

## Should You Keep These Workflows?

### ✅ Keep if:
- You want automated testing
- You care about security
- You want professional code quality
- You're building for production
- You collaborate with others

### ❌ Remove if:
- You're just experimenting
- You don't want GitHub integration
- You prefer manual testing
- Repository is archived/inactive

## Quick Commands

```bash
# Manually trigger a workflow
# Go to Actions tab → Select workflow → "Run workflow"

# View workflow status locally
gh workflow list  # Requires GitHub CLI

# Check workflow runs
gh run list

# View specific run
gh run view <run-id>
```

## Learn More

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Snyk Documentation](https://docs.snyk.io/)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)

## TL;DR

The `.github/workflows/` folder contains automation scripts that:
1. Test your code automatically
2. Build Docker images
3. Keep dependencies updated
4. (Optional) Scan for security issues if you set up Snyk

**They run on GitHub's servers (not yours) and are free for public repos.** They're a best practice for modern software development and highly recommended to keep!

---

If you want to disable them, just delete the `.github/workflows/` folder. But we recommend keeping them for better code quality and security! 🔒
