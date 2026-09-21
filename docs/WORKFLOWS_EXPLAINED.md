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

The three files in `.github/workflows/` are thin callers. The jobs themselves
live in [ChiefGyk3D/git-your-ship-together](https://github.com/ChiefGyk3D/git-your-ship-together),
shared with Typo Sniper, Stream Daemon and Boon Tube Daemon, so a pipeline fix
or a new scan step lands once. Each caller says only what is specific to
Star-Daemon: Python versions, the lint and test commands, the Dockerfile path,
the Doppler project.

### 1. `ci.yml` - CI

**Triggers**: Every push and pull request to `main` or `develop`, manual runs

**What it does**:
- **Linting**: Black, isort and Flake8
- **Testing**: `py_compile` over every module, then `pytest` on Python 3.11, 3.12 and 3.13
- **Docker Build**: Builds the image and checks its modules compile
- **CI green**: One gate job that fails if any of the above failed; point branch protection at it

### 2. `release.yml` - Container release

**Triggers**: Push to `main`, `v*.*.*` tags, pull requests, manual runs

**What it does**:
- On every pull request: build, test, scan with Trivy (results in the Security tab)
- On `main` and tags: publish a multi-arch (amd64 + arm64) image to `ghcr.io/chiefgyk3d/star-daemon` and to Docker Hub
- Sign the image with cosign (keyless), attach a syft SPDX SBOM, record SLSA build provenance

Verify a published image:

```sh
cosign verify ghcr.io/chiefgyk3d/star-daemon:latest \
  --certificate-identity-regexp '^https://github.com/ChiefGyk3D/git-your-ship-together/' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

### 3. `security.yml` - Security

**Triggers**: Push and pull requests to `main` or `develop`, weekly on Monday, manual runs

**What it does**:
- **CodeQL**: Static analysis, findings in the Security tab
- **gitleaks**: Secret scan over the full git history
- **pip-audit**: Known vulnerabilities in `requirements.txt`
- **Dependency Review**: What a pull request's dependency changes bring in

## Secrets: Doppler, not GitHub

Nothing is stored in this repository's GitHub secrets. A job authenticates to
Doppler with a short-lived token minted from its own GitHub OIDC identity (a
Doppler Service Account Identity) and reads the `ci` config of the
`star-daemon` project. For Star-Daemon that config holds:

- `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` - Docker Hub publishing

The one per-repository setting is the **repository variable**
`DOPPLER_IDENTITY_ID` (Settings → Secrets and variables → Actions →
Variables): the UUID of the identity. It is an identifier, not a secret.

Until it is set, the pipelines still run: Docker Hub publishing skips with a
notice, and GHCR publishing works regardless because it uses the job's own
`GITHUB_TOKEN`. The setup runbook and the fallback path (a Doppler Service
Token as the single GitHub secret `DOPPLER_TOKEN`) are in the
git-your-ship-together README.

## How to Check They're Working

1. Go to your repository on GitHub
2. Click the "Actions" tab
3. You should see CI, Release and Security listed

## Monitoring Workflow Runs

1. Click on any workflow to see its runs
2. Click on a specific run to see detailed logs
3. Green checkmark ✅ = passed, Red X ❌ = failed
4. Security findings (CodeQL, Trivy) are under the "Security" tab

## Customizing Workflows

Everything Star-Daemon-specific is a `with:` input in the caller, for
example the Python versions or the test command. Everything shared - the
steps, the pinned action versions, the signing - is in git-your-ship-together,
and a change there applies to every caller on its next run.

## Understanding Workflow Status

### Badges

```markdown
[![CI](https://github.com/ChiefGyk3D/Star-Daemon/actions/workflows/ci.yml/badge.svg)](https://github.com/ChiefGyk3D/Star-Daemon/actions/workflows/ci.yml)
[![Release](https://github.com/ChiefGyk3D/Star-Daemon/actions/workflows/release.yml/badge.svg)](https://github.com/ChiefGyk3D/Star-Daemon/actions/workflows/release.yml)
[![Security](https://github.com/ChiefGyk3D/Star-Daemon/actions/workflows/security.yml/badge.svg)](https://github.com/ChiefGyk3D/Star-Daemon/actions/workflows/security.yml)
```

### Common Issues

**"Workflow failed"**
- Check the logs in the Actions tab
- Most common: Linting errors or failing tests
- Fix locally and push again

**"Docker Hub publish skipped"**
- `DOPPLER_IDENTITY_ID` is not set, or the Doppler `ci` config has no
  `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`. GHCR is published either way.

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
