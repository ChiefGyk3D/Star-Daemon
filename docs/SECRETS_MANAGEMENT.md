# Secrets Management Guide

Star-Daemon supports multiple secrets management solutions to help you securely store and manage your API credentials and tokens. You can choose the solution that best fits your infrastructure and security requirements.

## Supported Solutions

1. **Doppler** - Modern secrets management platform
2. **AWS Secrets Manager** - Cloud-native AWS solution
3. **HashiCorp Vault** - Enterprise-grade secrets management
4. **Local .env files** - Simple file-based configuration (default fallback)

## Priority Order

Star-Daemon checks for secrets in the following order:

1. **Doppler** (if `DOPPLER_TOKEN` is set)
2. **AWS Secrets Manager** (if `AWS_SECRET_NAME` is set)
3. **HashiCorp Vault** (if `VAULT_ADDR` and `VAULT_TOKEN` are set)
4. **Local .env file** (fallback)

Only the first available option is used. This allows you to easily switch between different secrets management solutions without changing your code.

---

## Option 1: Doppler

[Doppler](https://doppler.com) is a modern secrets management platform with excellent developer experience.

### Benefits
- ✅ Free tier available
- ✅ Easy CLI integration
- ✅ Automatic environment variable injection
- ✅ Team collaboration features
- ✅ Audit logs and version history

### Setup

1. **Sign up for Doppler**
   - Visit https://doppler.com
   - Create a free account

2. **Install Doppler CLI**
   ```bash
   # macOS/Linux
   curl -sLf https://cli.doppler.com/install.sh | sh
   
   # Or with Homebrew
   brew install dopplerhq/cli/doppler
   ```

3. **Login to Doppler**
   ```bash
   doppler login
   ```

4. **Create a project**
   ```bash
   doppler setup
   ```

5. **Add secrets**
   ```bash
   # Via CLI
   doppler secrets set GITHUB_ACCESS_TOKEN=ghp_xxxxx
   doppler secrets set MASTODON_ENABLED=true
   doppler secrets set MASTODON_ACCESS_TOKEN=xxxxx
   
   # Or via web dashboard
   # Visit https://dashboard.doppler.com and add secrets there
   ```

6. **Get your service token** (for production)
   ```bash
   doppler configs tokens create production --max-age 30d
   ```

7. **Run Star-Daemon with Doppler**
   
   **Local development:**
   ```bash
   doppler run -- python star-daemon.py
   ```
   
   **Production (with service token):**
   ```bash
   export DOPPLER_TOKEN=dp.st.xxxxx
   python star-daemon.py
   ```
   
   **Docker:**
   ```bash
   docker run -e DOPPLER_TOKEN=dp.st.xxxxx star-daemon
   ```

### Docker Compose Configuration

```yaml
services:
  star-daemon:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    environment:
      - DOPPLER_TOKEN=${DOPPLER_TOKEN}
    restart: unless-stopped
```

---

## Option 2: AWS Secrets Manager

[AWS Secrets Manager](https://aws.amazon.com/secrets-manager/) is ideal if you're already using AWS infrastructure.

### Benefits
- ✅ Integrated with AWS ecosystem
- ✅ Automatic rotation support
- ✅ IAM-based access control
- ✅ Encryption at rest
- ✅ CloudWatch integration

### Prerequisites

```bash
# Install AWS CLI and boto3
pip install boto3
# or add to requirements.txt (already included)

# Configure AWS credentials
aws configure
```

### Setup

1. **Create a secret in AWS**
   
   **Via AWS CLI:**
   ```bash
   # Create a secrets JSON file
   cat > secrets.json <<EOF
   {
     "GITHUB_ACCESS_TOKEN": "ghp_xxxxx",
     "MASTODON_ENABLED": "true",
     "MASTODON_API_BASE_URL": "https://mastodon.social",
     "MASTODON_ACCESS_TOKEN": "xxxxx",
     "BLUESKY_ENABLED": "false",
     "DISCORD_ENABLED": "false",
     "MATRIX_ENABLED": "false"
   }
   EOF
   
   # Create the secret
   aws secretsmanager create-secret \
     --name star-daemon/production \
     --description "Star-Daemon production secrets" \
     --secret-string file://secrets.json \
     --region us-east-1
   
   # Clean up the file
   rm secrets.json
   ```
   
   **Via AWS Console:**
   - Go to AWS Secrets Manager console
   - Click "Store a new secret"
   - Select "Other type of secret"
   - Add your key-value pairs
   - Name it `star-daemon/production`
   - Click "Store"

2. **Configure environment variables**
   ```bash
   export AWS_SECRET_NAME=star-daemon/production
   export AWS_REGION=us-east-1
   ```

3. **Set up AWS credentials**
   
   **Option A: AWS CLI configuration (recommended for local development)**
   ```bash
   aws configure
   ```
   
   **Option B: Environment variables**
   ```bash
   export AWS_ACCESS_KEY_ID=AKIAXXXXX
   export AWS_SECRET_ACCESS_KEY=xxxxx
   ```
   
   **Option C: IAM roles (recommended for EC2/ECS)**
   - Attach an IAM role to your EC2 instance or ECS task
   - Grant the role `secretsmanager:GetSecretValue` permission

4. **Run Star-Daemon**
   ```bash
   python star-daemon.py
   ```

### IAM Policy

Create an IAM policy with minimal permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:*:secret:star-daemon/*"
    }
  ]
}
```

### Docker Configuration

**With explicit credentials:**
```yaml
services:
  star-daemon:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    environment:
      - AWS_SECRET_NAME=star-daemon/production
      - AWS_REGION=us-east-1
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    restart: unless-stopped
```

**With IAM roles (on EC2):**
```yaml
services:
  star-daemon:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    environment:
      - AWS_SECRET_NAME=star-daemon/production
      - AWS_REGION=us-east-1
    restart: unless-stopped
```

### Updating Secrets

```bash
# Update a specific secret
aws secretsmanager update-secret \
  --secret-id star-daemon/production \
  --secret-string file://updated-secrets.json

# Restart Star-Daemon to pick up changes
# (secrets are loaded at startup)
```

---

## Option 3: HashiCorp Vault

[HashiCorp Vault](https://www.vaultproject.io/) is an enterprise-grade secrets management solution.

### Benefits
- ✅ Dynamic secrets support
- ✅ Advanced access control
- ✅ Audit logging
- ✅ Multi-cloud support
- ✅ Encryption as a service

### Prerequisites

```bash
# Install hvac Python library
pip install hvac
# or add to requirements.txt (already included)
```

### Setup

1. **Install Vault** (if running your own instance)
   ```bash
   # macOS
   brew install vault
   
   # Linux
   wget https://releases.hashicorp.com/vault/1.15.0/vault_1.15.0_linux_amd64.zip
   unzip vault_1.15.0_linux_amd64.zip
   sudo mv vault /usr/local/bin/
   ```

2. **Start Vault** (development mode for testing)
   ```bash
   vault server -dev
   
   # Note the Root Token and Unseal Key from the output
   export VAULT_ADDR='http://127.0.0.1:8200'
   export VAULT_TOKEN='hvs.xxxxx'  # Use the root token shown
   ```

3. **Enable KV secrets engine** (if not already enabled)
   ```bash
   vault secrets enable -version=2 kv
   ```

4. **Store secrets in Vault**
   ```bash
   # Store all secrets at once
   vault kv put secret/star-daemon \
     GITHUB_ACCESS_TOKEN=ghp_xxxxx \
     MASTODON_ENABLED=true \
     MASTODON_API_BASE_URL=https://mastodon.social \
     MASTODON_ACCESS_TOKEN=xxxxx \
     BLUESKY_ENABLED=false \
     DISCORD_ENABLED=false \
     MATRIX_ENABLED=false
   
   # Or store individual secrets
   vault kv put secret/star-daemon/github \
     GITHUB_ACCESS_TOKEN=ghp_xxxxx
   ```

5. **Generate a token for Star-Daemon**
   ```bash
   # Create a policy
   cat > star-daemon-policy.hcl <<EOF
   path "secret/data/star-daemon" {
     capabilities = ["read"]
   }
   EOF
   
   vault policy write star-daemon star-daemon-policy.hcl
   
   # Create a token with the policy
   vault token create -policy=star-daemon -ttl=720h
   # Note the token value
   ```

6. **Configure environment variables**
   ```bash
   export VAULT_ADDR=https://vault.example.com:8200
   export VAULT_TOKEN=hvs.xxxxx
   export VAULT_SECRET_PATH=secret/data/star-daemon
   ```

7. **Run Star-Daemon**
   ```bash
   python star-daemon.py
   ```

### Docker Configuration

```yaml
services:
  star-daemon:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    environment:
      - VAULT_ADDR=https://vault.example.com:8200
      - VAULT_TOKEN=${VAULT_TOKEN}
      - VAULT_SECRET_PATH=secret/data/star-daemon
    restart: unless-stopped
```

### Using Vault in Production

**AppRole Authentication** (recommended for production):

```bash
# Enable AppRole
vault auth enable approle

# Create role
vault write auth/approle/role/star-daemon \
  token_policies="star-daemon" \
  token_ttl=1h \
  token_max_ttl=4h

# Get RoleID and SecretID
vault read auth/approle/role/star-daemon/role-id
vault write -f auth/approle/role/star-daemon/secret-id

# Update config.py to use AppRole instead of token
# (requires custom implementation)
```

### Updating Secrets

```bash
# Update secrets
vault kv put secret/star-daemon \
  GITHUB_ACCESS_TOKEN=ghp_new_token \
  MASTODON_ENABLED=true

# Restart Star-Daemon to pick up changes
```

---

## Option 4: Local .env Files

The simplest option for development and small deployments.

### Setup

1. **Copy the example file**
   ```bash
   cp .env.example .env
   ```

2. **Edit the file**
   ```bash
   nano .env
   # or use your preferred editor
   ```

3. **Add your secrets**
   ```bash
   GITHUB_ACCESS_TOKEN=ghp_xxxxx
   MASTODON_ENABLED=true
   MASTODON_API_BASE_URL=https://mastodon.social
   MASTODON_ACCESS_TOKEN=xxxxx
   ```

4. **Run Star-Daemon**
   ```bash
   python star-daemon.py
   ```

### Security Considerations

- ⚠️ **Never commit .env files to git** (already in `.gitignore`)
- ⚠️ **Use proper file permissions**: `chmod 600 .env`
- ⚠️ **Consider using a secrets manager for production**

---

## Comparison Table

| Feature | Doppler | AWS Secrets Manager | HashiCorp Vault | .env Files |
|---------|---------|---------------------|-----------------|------------|
| **Ease of Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Cost** | Free tier | ~$0.40/secret/month | Self-hosted (free) | Free |
| **Security** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Team Collaboration** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| **Audit Logs** | ✅ | ✅ | ✅ | ❌ |
| **Version History** | ✅ | ✅ | ✅ | ❌ |
| **Automatic Rotation** | ✅ | ✅ | ✅ | ❌ |
| **Multi-Cloud** | ✅ | AWS only | ✅ | ✅ |
| **Best For** | Teams | AWS users | Enterprise | Local dev |

---

## Migration Between Solutions

### From .env to Doppler

```bash
# Install Doppler
curl -sLf https://cli.doppler.com/install.sh | sh

# Login and setup
doppler login
doppler setup

# Import from .env file
doppler secrets upload .env

# Test
doppler run -- python star-daemon.py
```

### From .env to AWS Secrets Manager

```bash
# Convert .env to JSON
python3 << EOF
import json
from dotenv import dotenv_values
config = dotenv_values('.env')
print(json.dumps(config, indent=2))
EOF > secrets.json

# Create secret
aws secretsmanager create-secret \
  --name star-daemon/production \
  --secret-string file://secrets.json

# Clean up
rm secrets.json
```

### From .env to Vault

```bash
# Read .env and store in Vault
while IFS='=' read -r key value; do
  [[ -z "$key" || "$key" =~ ^# ]] && continue
  vault kv put secret/star-daemon "$key=$value"
done < .env
```

---

## Troubleshooting

### Doppler Issues

**"Doppler token not found"**
```bash
doppler login
doppler setup
```

**"Permission denied"**
- Check your service token has access to the correct project/config

### AWS Secrets Manager Issues

**"Unable to locate credentials"**
```bash
aws configure
# or
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
```

**"AccessDeniedException"**
- Check IAM permissions include `secretsmanager:GetSecretValue`

**"Secret not found"**
```bash
# List all secrets
aws secretsmanager list-secrets

# Verify secret name matches AWS_SECRET_NAME
```

### HashiCorp Vault Issues

**"Connection refused"**
```bash
# Check Vault is running
vault status

# Verify VAULT_ADDR is correct
echo $VAULT_ADDR
```

**"Permission denied"**
```bash
# Check token is valid
vault token lookup

# Verify token has correct policy
vault token capabilities secret/data/star-daemon
```

### .env File Issues

**"Environment variable not found"**
- Check file is named exactly `.env` (not `.env.txt`)
- Verify file is in the correct directory
- Check file permissions: `ls -la .env`

---

## Best Practices

1. **Use secrets managers in production** - Don't rely on .env files for production deployments
2. **Rotate secrets regularly** - Use automatic rotation features when available
3. **Minimize permissions** - Use least-privilege access for service accounts
4. **Enable audit logging** - Track who accesses secrets and when
5. **Use different secrets per environment** - dev, staging, production should have separate secrets
6. **Never commit secrets to git** - Use `.gitignore` to prevent accidental commits
7. **Encrypt secrets at rest** - All recommended solutions do this automatically
8. **Use short-lived tokens** - Generate tokens with expiration when possible

---

## Additional Resources

- [Doppler Documentation](https://docs.doppler.com/)
- [AWS Secrets Manager Guide](https://docs.aws.amazon.com/secretsmanager/)
- [HashiCorp Vault Documentation](https://www.vaultproject.io/docs)
- [Twelve-Factor App: Config](https://12factor.net/config)

---

## Support

If you encounter issues with secrets management:

1. Check the troubleshooting section above
2. Review the logs: Star-Daemon will log which secrets manager it's using
3. Open an issue on GitHub with details about your setup
