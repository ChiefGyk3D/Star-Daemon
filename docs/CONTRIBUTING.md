# Contributing to Star-Daemon

Thank you for your interest in contributing to Star-Daemon! This document provides guidelines and instructions for contributing.

## 🎯 How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/ChiefGyk3D/Star-Daemon/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, Docker version if applicable)
   - Relevant logs (with sensitive information redacted)

### Suggesting Enhancements

1. Check existing [Issues](https://github.com/ChiefGyk3D/Star-Daemon/issues) and [Discussions](https://github.com/ChiefGyk3D/Star-Daemon/discussions)
2. Create a new issue or discussion with:
   - Clear description of the enhancement
   - Use cases and benefits
   - Potential implementation approach (if applicable)

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/Star-Daemon.git
   cd Star-Daemon
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the code style guidelines below
   - Add tests if applicable
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Run linting
   flake8 *.py connectors/*.py
   
   # Test manually
   python star-daemon.py
   ```

5. **Commit with clear messages**
   ```bash
   git commit -m "Add feature: brief description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide a clear title and description
   - Reference any related issues
   - Ensure CI checks pass

## 📝 Code Style Guidelines

### Python Code

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Use type hints where appropriate
- Add docstrings to all functions, classes, and modules

Example:
```python
def post_message(self, message: str, metadata: Dict[str, Any] = None) -> bool:
    """
    Post a message to the platform.
    
    Args:
        message: The message to post
        metadata: Optional metadata about the repository
    
    Returns:
        True if successful, False otherwise
    """
    pass
```

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line: brief summary (50 chars or less)
- Optionally, add detailed description after blank line

Example:
```
Add BlueSky connector with rich metadata

- Implement BlueSky API integration using atproto
- Add support for embedded links and metadata
- Include comprehensive error handling
```

## 🏗️ Project Structure

```
Star-Daemon/
├── star-daemon.py          # Main application entry point
├── config.py               # Configuration management
├── connectors/             # Platform connectors
│   ├── __init__.py
│   ├── base.py            # Base connector class
│   ├── mastodon_connector.py
│   ├── bluesky_connector.py
│   ├── discord_connector.py
│   └── matrix_connector.py
├── requirements.txt        # Python dependencies
├── requirements.in         # Unpinned dependencies
├── Dockerfile             # Container definition
├── docker-compose.yml     # Docker orchestration
├── .env.example           # Example configuration
└── docs/                  # Documentation
```

## 🔧 Adding a New Platform Connector

To add support for a new social platform:

1. **Create connector file**
   ```bash
   touch connectors/newplatform_connector.py
   ```

2. **Implement connector class**
   ```python
   from typing import Dict, Any
   import logging
   from .base import Connector
   
   logger = logging.getLogger(__name__)
   
   class NewPlatformConnector(Connector):
       """Connector for NewPlatform"""
       
       def __init__(self, api_key: str):
           super().__init__("NewPlatform", enabled=True)
           self.api_key = api_key
           self.client = None
       
       def initialize(self) -> bool:
           """Initialize NewPlatform client"""
           # Implementation
           pass
       
       def post_message(self, message: str, metadata: Dict[str, Any] = None) -> bool:
           """Post to NewPlatform"""
           # Implementation
           pass
       
       def test_connection(self) -> bool:
           """Test connection to NewPlatform"""
           # Implementation
           pass
   ```

3. **Update `connectors/__init__.py`**
   ```python
   from .newplatform_connector import NewPlatformConnector
   
   __all__ = [
       # ... existing connectors
       'NewPlatformConnector'
   ]
   ```

4. **Add configuration to `config.py`**
   ```python
   # In Config.__init__
   self.newplatform_enabled = self._get_bool('NEWPLATFORM_ENABLED', False)
   self.newplatform_api_key = self._get_env('NEWPLATFORM_API_KEY', '')
   
   # In Config.validate
   if self.newplatform_enabled:
       if not self.newplatform_api_key:
           errors.append("NewPlatform enabled but missing API key")
   ```

5. **Initialize in `star-daemon.py`**
   ```python
   # In StarDaemon._initialize_connectors
   if config.newplatform_enabled:
       connector = NewPlatformConnector(api_key=config.newplatform_api_key)
       if connector.initialize() and connector.test_connection():
           self.connectors.append(connector)
   ```

6. **Update `.env.example`**
   ```bash
   # =============================================================================
   # NewPlatform Configuration
   # =============================================================================
   # Enable NewPlatform posting (true/false)
   NEWPLATFORM_ENABLED=false
   
   # NewPlatform API key
   NEWPLATFORM_API_KEY=your_api_key_here
   ```

7. **Add dependencies to `requirements.in`**
   ```
   newplatform-sdk
   ```

8. **Update documentation**
   - Add platform section to README.md
   - Create setup guide in `docs/NEWPLATFORM_SETUP.md`

## 🧪 Testing

### Manual Testing

1. Configure your `.env` file with test credentials
2. Run the daemon with debug logging:
   ```bash
   LOG_LEVEL=DEBUG python star-daemon.py
   ```
3. Star a repository on GitHub
4. Verify posts appear on configured platforms

### Testing with Docker

```bash
docker-compose build
docker-compose up
```

## 📚 Documentation

- Update README.md for user-facing changes
- Add docstrings for code changes
- Create setup guides in `docs/` for new platforms
- Update configuration examples

## 🔐 Security

- Never commit secrets or credentials
- Use `.env.example` for examples only
- Report security vulnerabilities privately (see [SECURITY.md](SECURITY.md))
- Ensure new dependencies are scanned by Snyk

## 📋 Checklist for Pull Requests

Before submitting your PR, ensure:

- [ ] Code follows PEP 8 style guidelines
- [ ] All functions have docstrings
- [ ] Type hints are used where appropriate
- [ ] Changes are tested manually
- [ ] Documentation is updated
- [ ] `.env.example` is updated if new config is added
- [ ] No secrets or credentials are committed
- [ ] Commit messages are clear and descriptive

## 💬 Questions?

- Open a [Discussion](https://github.com/ChiefGyk3D/Star-Daemon/discussions)
- Join our community chat (if applicable)
- Check existing [Issues](https://github.com/ChiefGyk3D/Star-Daemon/issues)

## 📜 License

By contributing, you agree that your contributions will be licensed under the Mozilla Public License Version 2.0 (MPL-2.0) under the terms described in the project's `LICENSE` file.

---

Thank you for contributing to Star-Daemon! 🌟
