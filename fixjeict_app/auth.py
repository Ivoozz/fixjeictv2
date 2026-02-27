import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import AuthToken, User


# HTTP Basic Auth for admin
security = HTTPBasic()


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """Verify admin username and password using timing-safe comparison"""
    is_correct_username = secrets.compare_digest(
        credentials.username,
        settings.ADMIN_USERNAME
    )
    is_correct_password = secrets.compare_digest(
        credentials.password,
        settings.ADMIN_PASSWORD
    )

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


def generate_auth_token(user_id: int, db: Session) -> str:
    """Generate a magic link token for user authentication"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)

    auth_token = AuthToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(auth_token)
    db.commit()

    return token


def verify_auth_token(token: str, db: Session) -> Optional[User]:
    """Verify magic link token and return user if valid"""
    auth_token = db.query(AuthToken).filter_by(token=token).first()

    if not auth_token:
        return None

    if auth_token.used:
        return None

    if auth_token.expires_at < datetime.utcnow():
        return None

    user = db.query(User).filter_by(id=auth_token.user_id).first()
    if not user:
        return None

    # Mark token as used
    auth_token.used = True
    user.last_login = datetime.utcnow()
    db.commit()

    return user


def get_or_create_user(email: str, db: Session) -> User:
    """Get existing user or create new one"""
    email = email.strip().lower()
    user = db.query(User).filter_by(email=email).first()

    if not user:
        # Create new user
        name = email.split("@")[0].replace(".", " ").title()
        user = User(email=email, name=name, role="client")
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user from session"""
    user_id = request.session.get("user_id")
    if user_id:
        return db.query(User).filter_by(id=user_id).first()
    return None


def require_login(user: Optional[User] = Depends(get_current_user)) -> User:
    """Require user to be logged in"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    return user


def require_fixer(user: User = Depends(require_login)) -> User:
    """Require user to have fixer or admin role"""
    if user.role not in ["fixer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fixer account required"
        )
    return user


def require_admin(user: User = Depends(require_login)) -> User:
    """Require user to have admin role"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


def has_ticket_access(user: User, ticket_id: int, db: Session) -> bool:
    """Check if user has access to a ticket"""
    from .models import Ticket

    ticket = db.query(Ticket).filter_by(id=ticket_id).first()
    if not ticket:
        return False

    # Admin and fixers have access to all tickets
    if user.role in ["admin", "fixer"]:
        # Fixers only have access if they're assigned or ticket is unassigned
        if user.role == "fixer" and ticket.fixer_id and ticket.fixer_id != user.id:
            return False
        return True

    # Clients only have access to their own tickets
    return ticket.client_id == user.id


def check_ticket_access(user: User, ticket_id: int, db: Session) -> None:
    """Raise exception if user doesn't have access to ticket"""
    if not has_ticket_access(user, ticket_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this ticket"
        )
