import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from itsdangerous import URLSafeTimedSerializer

from app.config import get_settings
from app.database import get_db
from app.models import MagicLink, User

logger = logging.getLogger(__name__)
settings = get_settings()
security = HTTPBasic()


def verify_admin_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Verify admin credentials using HTTP Basic Auth"""
    correct_username = settings.admin_username
    correct_password = settings.admin_password
    
    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)
    
    if not (is_correct_username and is_correct_password):
        logger.warning(f"Failed admin login attempt for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username


def generate_magic_token() -> str:
    """Generate a secure random token for magic links"""
    return secrets.token_urlsafe(32)


def create_magic_link(db: Session, user_id: int, expires_hours: int = 24) -> MagicLink:
    """Create a new magic link for a user"""
    token = generate_magic_token()
    expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
    
    magic_link = MagicLink(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    db.add(magic_link)
    db.commit()
    db.refresh(magic_link)
    
    return magic_link


def validate_magic_link(db: Session, token: str) -> Optional[User]:
    """Validate a magic link token and return the user if valid"""
    magic_link = db.query(MagicLink).filter(
        MagicLink.token == token,
        MagicLink.used == False,
        MagicLink.expires_at > datetime.utcnow()
    ).first()
    
    if not magic_link:
        return None
    
    # Mark as used
    magic_link.used = True
    db.commit()
    
    return magic_link.user


def generate_ticket_number() -> str:
    """Generate a unique ticket number"""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_part = secrets.token_hex(4).upper()
    return f"ICT-{timestamp}-{random_part}"


class SessionManager:
    """Manage user sessions via signed cookies"""
    
    def __init__(self):
        self.serializer = URLSafeTimedSerializer(settings.secret_key)
    
    def create_session(self, user_id: int) -> str:
        """Create a signed session token"""
        return self.serializer.dumps({"user_id": user_id})
    
    def validate_session(self, token: str, max_age: int = 86400) -> Optional[int]:
        """Validate a session token and return user_id if valid"""
        try:
            data = self.serializer.loads(token, max_age=max_age)
            return data.get("user_id")
        except Exception:
            return None


session_manager = SessionManager()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user from session cookie"""
    session_token = request.cookies.get("session")
    if not session_token:
        return None
    
    user_id = session_manager.validate_session(session_token)
    if not user_id:
        return None
    
    return db.query(User).filter(User.id == user_id).first()


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Require a logged in user, raise 401 if not authenticated"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"Location": "/login"},
        )
    return user
