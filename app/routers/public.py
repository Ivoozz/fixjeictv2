import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config import get_settings
from app.database import get_db
from app.models import User, Ticket, Comment
from app.auth import (
    create_magic_link, 
    validate_magic_link, 
    generate_ticket_number,
    session_manager,
    get_current_user,
    require_user
)
from app.templates import templates

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Homepage with ticket creation form"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Welkom bij FixJeICT"
    })


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    """Login page with email form"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": "Inloggen",
        "error": error
    })


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle login form submission and send magic link"""
    try:
        # Normalize email
        email = email.lower().strip()
        
        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Create new user
            user = User(email=email, name=email.split("@")[0])
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create magic link
        magic_link = create_magic_link(db, user.id)
        
        # TODO: Send email with magic link
        # For now, we'll redirect to the magic link directly (for testing)
        logger.info(f"Magic link created for {email}: {magic_link.token}")
        
        return templates.TemplateResponse("login_sent.html", {
            "request": request,
            "title": "Magic Link Verstuurd",
            "email": email,
            "magic_token": magic_link.token  # Remove in production!
        })
        
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "title": "Inloggen",
            "error": "Er is een fout opgetreden. Probeer het later opnieuw."
        })


@router.get("/auth/magic/{token}")
async def magic_link_auth(
    token: str,
    db: Session = Depends(get_db)
):
    """Handle magic link authentication"""
    user = validate_magic_link(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ongeldige of verlopen link"
        )
    
    # Create session
    session_token = session_manager.create_session(user.id)
    
    response = RedirectResponse(url="/tickets", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax"
    )
    
    return response


@router.get("/logout")
async def logout():
    """Logout user"""
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session")
    return response


@router.get("/tickets", response_class=HTMLResponse)
async def ticket_list(
    request: Request,
    user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """List user's tickets"""
    tickets = db.query(Ticket).filter(
        Ticket.user_id == user.id
    ).order_by(desc(Ticket.created_at)).all()
    
    return templates.TemplateResponse("tickets.html", {
        "request": request,
        "title": "Mijn Tickets",
        "user": user,
        "tickets": tickets
    })


@router.get("/tickets/new", response_class=HTMLResponse)
async def new_ticket_page(
    request: Request,
    user: User = Depends(require_user)
):
    """New ticket creation page"""
    return templates.TemplateResponse("ticket_form.html", {
        "request": request,
        "title": "Nieuw Ticket",
        "user": user
    })


@router.post("/tickets/new")
async def create_ticket(
    request: Request,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    subject: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    priority: str = Form("medium")
):
    """Create a new ticket"""
    try:
        ticket = Ticket(
            ticket_number=generate_ticket_number(),
            user_id=user.id,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
            status="open"
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        # Add initial comment
        comment = Comment(
            ticket_id=ticket.id,
            author_type="system",
            author_name="Systeem",
            content=f"Ticket aangemaakt door {user.name}",
            is_internal=False
        )
        db.add(comment)
        db.commit()
        
        return RedirectResponse(
            url=f"/tickets/{ticket.id}",
            status_code=status.HTTP_302_FOUND
        )
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        return templates.TemplateResponse("ticket_form.html", {
            "request": request,
            "title": "Nieuw Ticket",
            "user": user,
            "error": "Er is een fout opgetreden bij het aanmaken van het ticket."
        })


@router.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def view_ticket(
    request: Request,
    ticket_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """View a specific ticket"""
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.user_id == user.id
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket niet gevonden")
    
    comments = db.query(Comment).filter(
        Comment.ticket_id == ticket.id,
        Comment.is_internal == False
    ).order_by(Comment.created_at).all()
    
    return templates.TemplateResponse("ticket_detail.html", {
        "request": request,
        "title": f"Ticket #{ticket.ticket_number}",
        "user": user,
        "ticket": ticket,
        "comments": comments
    })


@router.post("/tickets/{ticket_id}/comment")
async def add_comment(
    request: Request,
    ticket_id: int,
    content: str = Form(...),
    user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Add a comment to a ticket"""
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.user_id == user.id
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket niet gevonden")
    
    comment = Comment(
        ticket_id=ticket.id,
        author_type="user",
        author_name=user.name,
        content=content,
        is_internal=False
    )
    
    db.add(comment)
    
    # Update ticket timestamp
    ticket.updated_at = datetime.utcnow()
    
    db.commit()
    
    return RedirectResponse(
        url=f"/tickets/{ticket.id}",
        status_code=status.HTTP_302_FOUND
    )
