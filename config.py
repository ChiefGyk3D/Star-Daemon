"""
Configuration management for Star-Daemon
Supports multiple secrets management solutions:
- Doppler
- AWS Secrets Manager
- HashiCorp Vault
- Local .env files (fallback)
"""

import json
import logging
import os
from typing import Dict, Optional

from dotenv import load_dotenv  # Import but don't call yet

logger = logging.getLogger(__name__)


class SecretsManager:
    """Base class for secrets management providers"""

    def __init__(self):
        self.secrets_cache: Dict[str, str] = {}

    def load_secrets(self) -> bool:
        """Load secrets from the provider. Returns True if successful."""
        raise NotImplementedError

    def get_secret(self, key: str, default: str = "") -> str:
        """Get a secret value"""
        return self.secrets_cache.get(key, default)

    def has_secret(self, key: str) -> bool:
        """Check if a secret exists in the cache"""
        return key in self.secrets_cache


class DopplerSecretsManager(SecretsManager):
    """Doppler secrets management using SDK"""

    def load_secrets(self) -> bool:
        doppler_token = os.getenv("DOPPLER_TOKEN")
        if not doppler_token:
            return False

        try:
            from dopplersdk import DopplerSDK

            logger.info("Using Doppler SDK for secrets management")

            # Initialize Doppler SDK
            sdk = DopplerSDK()
            sdk.set_access_token(doppler_token)

            # Get project and config from environment or use defaults
            project = os.getenv("DOPPLER_PROJECT", "star-daemon")
            config_name = os.getenv("DOPPLER_CONFIG", "dev")

            # Fetch secrets from Doppler API
            response = sdk.secrets.list(project=project, config=config_name)

            if hasattr(response, "secrets") and response.secrets:
                # Extract secret values into cache
                # Secrets are returned as dict of dicts with 'computed' key containing the value
                for key, secret_data in response.secrets.items():
                    if isinstance(secret_data, dict) and "computed" in secret_data:
                        self.secrets_cache[key] = secret_data["computed"]
                    elif isinstance(secret_data, dict) and "raw" in secret_data:
                        self.secrets_cache[key] = secret_data["raw"]

                logger.info(
                    f"Loaded {len(self.secrets_cache)} secrets from Doppler (project={project}, config={config_name})"
                )
                return True
            else:
                logger.error("Doppler API returned no secrets")
                return False

        except ImportError:
            logger.error(
                "doppler-sdk not installed. Install with: pip install doppler-sdk"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to load secrets from Doppler: {e}")
            return False


class AWSSecretsManager(SecretsManager):
    """AWS Secrets Manager integration"""

    def load_secrets(self) -> bool:
        aws_secret_name = os.getenv("AWS_SECRET_NAME")
        aws_region = os.getenv("AWS_REGION", "us-east-1")

        if not aws_secret_name:
            return False

        try:
            import boto3
            from botocore.exceptions import ClientError

            logger.info(f"Loading secrets from AWS Secrets Manager: {aws_secret_name}")

            session = boto3.session.Session()
            client = session.client(
                service_name="secretsmanager", region_name=aws_region
            )

            try:
                response = client.get_secret_value(SecretId=aws_secret_name)

                if "SecretString" in response:
                    secret_data = json.loads(response["SecretString"])
                    self.secrets_cache.update(secret_data)
                    logger.info(
                        f"Loaded {len(secret_data)} secrets from AWS Secrets Manager"
                    )
                    return True
                else:
                    logger.error("AWS secret does not contain SecretString")
                    return False

            except ClientError as e:
                logger.error(f"Failed to retrieve secret from AWS: {e}")
                return False

        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            return False


class VaultSecretsManager(SecretsManager):
    """HashiCorp Vault integration"""

    def load_secrets(self) -> bool:
        vault_addr = os.getenv("VAULT_ADDR")
        vault_token = os.getenv("VAULT_TOKEN")
        vault_path = os.getenv("VAULT_SECRET_PATH", "secret/data/star-daemon")

        if not vault_addr or not vault_token:
            return False

        try:
            import hvac

            logger.info(f"Loading secrets from HashiCorp Vault: {vault_addr}")

            client = hvac.Client(url=vault_addr, token=vault_token)

            if not client.is_authenticated():
                logger.error("Vault authentication failed")
                return False

            # Read secrets from KV v2 engine
            try:
                response = client.secrets.kv.v2.read_secret_version(
                    path=vault_path.replace("secret/data/", "")
                )

                if response and "data" in response and "data" in response["data"]:
                    secret_data = response["data"]["data"]
                    self.secrets_cache.update(secret_data)
                    logger.info(f"Loaded {len(secret_data)} secrets from Vault")
                    return True
                else:
                    logger.error("Vault secret not found or has unexpected format")
                    return False

            except Exception as e:
                logger.error(f"Failed to read secret from Vault: {e}")
                return False

        except ImportError:
            logger.error("hvac not installed. Install with: pip install hvac")
            return False


class Config:
    """Configuration manager with multiple secrets management support"""

    def __init__(self):
        # Try secrets managers in order of preference
        self.secrets_manager: Optional[SecretsManager] = None

        # Try Doppler first (before loading .env!)
        doppler = DopplerSecretsManager()
        if doppler.load_secrets():
            self.secrets_manager = doppler

        # Try AWS Secrets Manager
        if not self.secrets_manager:
            aws_sm = AWSSecretsManager()
            if aws_sm.load_secrets():
                self.secrets_manager = aws_sm

        # Try HashiCorp Vault
        if not self.secrets_manager:
            vault = VaultSecretsManager()
            if vault.load_secrets():
                self.secrets_manager = vault

        # Fallback to .env file
        if not self.secrets_manager:
            logger.info("Loading configuration from .env file")
            load_dotenv()  # Only load .env if no secrets manager worked
            # Create a simple secrets manager for .env
            env_manager = SecretsManager()
            env_manager.secrets_cache = dict(os.environ)
            self.secrets_manager = env_manager

        # Core settings
        self.check_interval = int(self._get_env("CHECK_INTERVAL", "60"))
        self.log_level = self._get_env("LOG_LEVEL", "INFO")

        # GitHub
        self.github_token = self._get_env("GITHUB_ACCESS_TOKEN", required=True)
        self.github_username = self._get_env("GITHUB_USERNAME", "")

        # Mastodon
        self.mastodon_enabled = self._get_bool("MASTODON_ENABLED", False)
        self.mastodon_api_base_url = self._get_env("MASTODON_API_BASE_URL", "")
        self.mastodon_client_id = self._get_env("MASTODON_CLIENT_ID", "")
        self.mastodon_client_secret = self._get_env("MASTODON_CLIENT_SECRET", "")
        self.mastodon_access_token = self._get_env("MASTODON_ACCESS_TOKEN", "")

        # BlueSky
        self.bluesky_enabled = self._get_bool("BLUESKY_ENABLED", False)
        self.bluesky_handle = self._get_env("BLUESKY_HANDLE", "")
        self.bluesky_app_password = self._get_env("BLUESKY_APP_PASSWORD", "")

        # Discord
        self.discord_enabled = self._get_bool("DISCORD_ENABLED", False)
        self.discord_webhook_url = self._get_env("DISCORD_WEBHOOK_URL", "")
        self.discord_role_id = self._get_env(
            "DISCORD_ROLE_ID", ""
        )  # Optional role mention
        self.discord_bot_token = self._get_env("DISCORD_BOT_TOKEN", "")
        self.discord_channel_id = self._get_env("DISCORD_CHANNEL_ID", "")

        # Matrix
        self.matrix_enabled = self._get_bool("MATRIX_ENABLED", False)
        self.matrix_homeserver = self._get_env("MATRIX_HOMESERVER", "")
        self.matrix_user_id = self._get_env("MATRIX_USER_ID", "")
        self.matrix_password = self._get_env("MATRIX_PASSWORD", "")
        self.matrix_access_token = self._get_env("MATRIX_ACCESS_TOKEN", "")
        self.matrix_room_id = self._get_env("MATRIX_ROOM_ID", "")

        # Message customization
        self.message_template = self._get_env(
            "MESSAGE_TEMPLATE", "I just starred {name} on GitHub: {url}"
        )
        self.include_description = self._get_bool("INCLUDE_DESCRIPTION", False)
        self.max_message_length = int(self._get_env("MAX_MESSAGE_LENGTH", "500"))

    def _get_env(self, key: str, default: str = "", required: bool = False) -> str:
        """Get environment variable with optional default and required check"""
        # If secrets manager exists and has this key, use it (Doppler takes precedence)
        if self.secrets_manager and self.secrets_manager.has_secret(key):
            value = self.secrets_manager.get_secret(key, default)
        else:
            # Key not in Doppler, fall back to environment or default
            value = os.getenv(key, default)

        if required and not value:
            raise ValueError(f"Required environment variable {key} is not set")

        return value

    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable with secrets manager fallback"""
        # If secrets manager exists and has this key, use it (Doppler takes precedence)
        if self.secrets_manager and self.secrets_manager.has_secret(key):
            value = self.secrets_manager.get_secret(key, str(default))
        else:
            # Key not in Doppler, fall back to environment or default
            value = os.getenv(key, str(default))

        return str(value).lower() in ("true", "1", "yes", "on")

    def validate(self) -> bool:
        """Validate configuration"""
        errors = []

        # Check if at least one platform is enabled
        platforms_enabled = any(
            [
                self.mastodon_enabled,
                self.bluesky_enabled,
                self.discord_enabled,
                self.matrix_enabled,
            ]
        )

        if not platforms_enabled:
            errors.append(
                "No platforms enabled. Enable at least one platform (Mastodon, BlueSky, Discord, Matrix, or Twitter)"
            )

        # Validate platform-specific configuration
        if self.mastodon_enabled:
            if not all([self.mastodon_api_base_url, self.mastodon_access_token]):
                errors.append("Mastodon enabled but missing required configuration")

        if self.bluesky_enabled:
            if not all([self.bluesky_handle, self.bluesky_app_password]):
                errors.append("BlueSky enabled but missing required configuration")

        if self.discord_enabled:
            if not self.discord_webhook_url and not (
                self.discord_bot_token and self.discord_channel_id
            ):
                errors.append(
                    "Discord enabled but missing webhook URL or bot configuration"
                )

        if self.matrix_enabled:
            if not all(
                [self.matrix_homeserver, self.matrix_user_id, self.matrix_room_id]
            ):
                errors.append("Matrix enabled but missing required configuration")
            if not self.matrix_password and not self.matrix_access_token:
                errors.append("Matrix enabled but missing password or access token")

        if errors:
            for error in errors:
                logger.error(error)
            return False

        return True


# Global config instance
config = Config()
