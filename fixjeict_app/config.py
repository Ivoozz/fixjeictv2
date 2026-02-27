import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration with environment variable support"""

    # Application
    APP_NAME: str = "FixJeICT"
    APP_VERSION: str = "3.0.0"
    APP_URL: str = "http://localhost:5000"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///fixjeict.db",
        description="Database connection URL"
    )

    # Security
    SECRET_KEY: str = Field(
        default="change-this-in-production",
        description="Secret key for session signing"
    )

    # Admin credentials
    ADMIN_USERNAME: str = Field(default="admin", description="Admin username")
    ADMIN_PASSWORD: str = Field(default="fixjeict2026", description="Admin password")

    # Email (Resend)
    RESEND_API_KEY: Optional[str] = Field(default=None, description="Resend API key")
    RESEND_FROM: str = Field(
        default="noreply@fixjeict.nl",
        description="From email address"
    )

    # Cloudflare
    CLOUDFLARE_API_KEY: Optional[str] = Field(
        default=None,
        description="Cloudflare API key"
    )
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = Field(
        default=None,
        description="Cloudflare account ID"
    )
    CLOUDFLARE_ZONE_ID: Optional[str] = Field(
        default=None,
        description="Cloudflare zone ID"
    )
    EMAIL_DOMAIN: str = Field(
        default="fixjeict.nl",
        description="Email domain for routing"
    )

    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=5000, description="Server port")
    ADMIN_PORT: int = Field(default=5001, description="Admin port (optional)")
    WORKERS: int = Field(default=4, description="Number of worker processes")

    # Paths
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

    @property
    def database_path(self) -> Optional[Path]:
        """Get database file path if using SQLite"""
        if self.DATABASE_URL.startswith("sqlite:///"):
            return Path(self.DATABASE_URL.replace("sqlite:///", ""))
        elif self.DATABASE_URL.startswith("sqlite:////"):
            return Path(self.DATABASE_URL.replace("sqlite:////", ""))
        return None

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEBUG


# Global settings instance
settings = Settings()
