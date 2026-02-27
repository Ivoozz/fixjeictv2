from pydantic_settings import BaseSettings
from functools import lru_cache
import secrets


class Settings(BaseSettings):
    app_name: str = "FixJeICT"
    debug: bool = False
    
    # Security
    secret_key: str = secrets.token_urlsafe(32)
    admin_username: str = "admin"
    admin_password: str = "admin"
    
    # Database
    database_url: str = "sqlite:///opt/fixjeictv2/data/fixjeict.db"
    
    # Email (Resend)
    resend_api_key: str = ""
    from_email: str = "noreply@fixjeict.nl"
    
    # URLs
    public_url: str = "https://fixjeict.nl"
    admin_url: str = "https://admin.fixjeict.nl"
    
    # Server
    public_host: str = "0.0.0.0"
    public_port: int = 5000
    admin_host: str = "0.0.0.0"
    admin_port: int = 5001
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
