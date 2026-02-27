import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Form, Request, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.config import get_settings
from app.database import get_db
from app.models import User, Ticket, Comment, Setting
from app.auth import verify_admin_credentials
from app.templates import templates

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


def get_admin_context(request: Request, **kwargs) -> dict:
    """Helper to create template context with common admin data"""
    context = {
        "request": request,
        "admin_username": settings.admin_username,
        **kwargs
    }
    return context


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    username: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Admin dashboard with statistics"""
    try:
        # Statistics
        total_tickets = db.query(Ticket).count()
        open_tickets = db.query(Ticket).filter(Ticket.status == "open").count()
        in_progress_tickets = db.query(Ticket).filter(Ticket.status == "in_progress").count()
        resolved_tickets = db.query(Ticket).filter(Ticket.status == "resolved").count()
        total_users = db.query(User).count()
        
        # Recent tickets
        recent_tickets = db.query(Ticket).order_by(desc(Ticket.created_at)).limit(10).all()
        
        return templates.TemplateResponse("admin/dashboard.html", get_admin_context(
            request,
            title="Admin Dashboard",
            stats={
                "total_tickets": total_tickets,
                "open_tickets": open_tickets,
                "in_progress_tickets": in_progress_tickets,
                "resolved_tickets": resolved_tickets,
                "total_users": total_users
            },
            recent_tickets=recent_tickets
        ))
        
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/tickets", response_class=HTMLResponse)
async def admin_ticket_list(
    request: Request,
    username: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1)
):
    """Admin ticket list with filters"""
    try:
        query = db.query(Ticket)
        
        # Apply filters
        if status:
            query = query.filter(Ticket.status == status)
        if priority:
            query = query.filter(Ticket.priority == priority)
        if category:
            query = query.filter(Ticket.category == category)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                Ticket.subject.ilike(search_filter) |
                Ticket.description.ilike(search_filter) |
                Ticket.ticket_number.ilike(search_filter)
            )
        
        # Pagination
        per_page = 20
        total = query.count()
        tickets = query.order_by(desc(Ticket.created_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        total_pages = (total + per_page - 1) // per_page
        
        return templates.TemplateResponse("admin/tickets.html", get_admin_context(
            request,
            title="Alle Tickets",
            tickets=tickets,
            filters={
                "status": status,
                "priority": priority,
                "category": category,
                "search": search
            },
            pagination={
                "page": page,
                "total_pages": total_pages,
                "total": total,
                "has_prev": page > 1,
                "has_next": page < total_pages
            }
        ))
        
    except Exception as e:
        logger.error(f"Error loading ticket list: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def admin_view_ticket(
    request: Request,
    ticket_id: int,
    username: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """View ticket details as admin"""
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket niet gevonden")
        
        comments = db.query(Comment).filter(
            Comment.ticket_id == ticket.id
        ).order_by(Comment.created_at).all()
        
        return templates.TemplateResponse("admin/ticket_detail.html", get_admin_context(
            request,
            title=f"Ticket #{ticket.ticket_number}",
            ticket=ticket,
            comments=comments
        ))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing ticket: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/tickets/{ticket_id}/update")
async def admin_update_ticket(
    request: Request,
    ticket_id: int,
    status: str = Form(...),
    priority: str = Form(...),
    internal_note: Optional[str] = Form(None),
    username: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Update ticket status and priority"""
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket niet gevonden")
        
        old_status = ticket.status
        ticket.status = status
        ticket.priority = priority
        ticket.updated_at = datetime.utcnow()
        
        if status == "resolved" and old_status != "resolved":
            ticket.resolved_at = datetime.utcnow()
        
        # Add status change comment
        if old_status != status:
            comment = Comment(
                ticket_id=ticket.id,
                author_type="admin",
                author_name=f"Admin ({username})",
                content=f"Status gewijzigd van '{old_status}' naar '{status}'",
                is_internal=False
            )
            db.add(comment)
        
        # Add internal note if provided
        if internal_note:
            note_comment = Comment(
                ticket_id=ticket.id,
                author_type="admin",
                author_name=f"Admin ({username})",
                content=internal_note,
                is_internal=True
            )
            db.add(note_comment)
        
        db.commit()
        
        return RedirectResponse(
            url=f"/admin/tickets/{ticket.id}",
            status_code=status.HTTP_302_FOUND
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ticket: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/tickets/{ticket_id}/comment")
async def admin_add_comment(
    request: Request,
    ticket_id: int,
    content: str = Form(...),
    is_internal: bool = Form(False),
    username: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Add admin comment to ticket"""
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket niet gevonden")
        
        comment = Comment(
            ticket_id=ticket.id,
            author_type="admin",
            author_name=f"Admin ({username})",
            content=content,
            is_internal=is_internal
        )
        
        db.add(comment)
        ticket.updated_at = datetime.utcnow()
        db.commit()
        
        return RedirectResponse(
            url=f"/admin/tickets/{ticket.id}",
            status_code=status.HTTP_302_FOUND
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/users", response_class=HTMLResponse)
async def admin_user_list(
    request: Request,
    username: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1)
):
    """List all users"""
    try:
        query = db.query(User)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                User.name.ilike(search_filter) |
                User.email.ilike(search_filter) |
                User.company.ilike(search_filter)
            )
        
        per_page = 20
        total = query.count()
        users = query.order_by(desc(User.created_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        total_pages = (total + per_page - 1) // per_page
        
        return templates.TemplateResponse("admin/users.html", get_admin_context(
            request,
            title="Gebruikers",
            users=users,
            search=search,
            pagination={
                "page": page,
                "total_pages": total_pages,
                "total": total,
                "has_prev": page > 1,
                "has_next": page < total_pages
            }
        ))
        
    except Exception as e:
        logger.error(f"Error loading user list: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def admin_view_user(
    request: Request,
    user_id: int,
    username: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """View user details"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
        
        tickets = db.query(Ticket).filter(
            Ticket.user_id == user.id
        ).order_by(desc(Ticket.created_at)).all()
        
        return templates.TemplateResponse("admin/user_detail.html", get_admin_context(
            request,
            title=f"Gebruiker: {user.name}",
            user=user,
            tickets=tickets
        ))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing user: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(
    request: Request,
    username: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Admin settings page"""
    try:
        settings_list = db.query(Setting).all()
        
        return templates.TemplateResponse("admin/settings.html", get_admin_context(
            request,
            title="Instellingen",
            settings=settings_list
        ))
        
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
