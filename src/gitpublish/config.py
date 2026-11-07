"""Application configuration."""

APP_NAME = "Git Publish"
APP_VERSION = "5.0.0rc1"

DEFAULT_BRANCH = "main"
COMMAND_TIMEOUT = 60

SENSITIVE_NAMES = {
    ".netrc",
    ".npmrc",
    ".pypirc",
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.test",
    "credentials.json",
    "credentials.yaml",
    "credentials.yml",
    "secrets.json",
    "secrets.yaml",
    "secrets.yml",
    "secret.json",
    "secret.yaml",
    "secret.yml",
    "config.secret",
    "id_rsa",
    "id_ed25519",
    "token.txt",
    "password.txt",
}

SENSITIVE_DIRECTORIES = {
    ".aws",
    ".ssh",
    ".gnupg",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
}

SENSITIVE_EXTENSIONS = {
    ".pem", ".key", ".p12", ".pfx", ".crt",
}

SENSITIVE_PATTERNS = (
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.crt",
)
