from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..auth import check_ticket_access, require_fixer, require_login
from ..database import get_db
from ..email_service import email_service
from ..models import Category, Message, Ticket, TicketNote, TimeLog
from ..services.template_service import template_service

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(require_login), db: Session = Depends(get_db)):
    """User dashboard"""
    if user.role == "client":
        tickets = (
            db.query(Ticket)
            .filter_by(client_id=user.id)
            .order_by(Ticket.updated_at.desc())
            .all()
        )
        return template_service.render_template(
            "dashboard.html",
            {
                "request": request,
                "user": user,
                "tickets": tickets,
            },
        )

    elif user.role == "fixer":
        my_tickets = (
            db.query(Ticket)
            .filter_by(fixer_id=user.id)
            .order_by(Ticket.updated_at.desc())
            .all()
        )
        available_tickets = (
            db.query(Ticket)
            .filter((Ticket.fixer_id == None) | (Ticket.fixer_id == user.id))
            .order_by(Ticket.created_at.desc())
            .all()
        )
        return template_service.render_template(
            "dashboard_fixer.html",
            {
                "request": request,
                "user": user,
                "my_tickets": my_tickets,
                "available_tickets": available_tickets,
            },
        )

    return template_service.render_template(
        "dashboard.html",
        {
            "request": request,
            "user": user,
        },
    )


@router.get("/tickets/new", response_class=HTMLResponse)
async def new_ticket(request: Request, user=Depends(require_login), db: Session = Depends(get_db)):
    """Create new ticket page"""
    categories = (
        db.query(Category)
        .filter_by(is_active=True)
        .order_by(Category.order)
        .all()
    )
    return template_service.render_template(
        "new_ticket.html",
        {
            "request": request,
            "user": user,
            "categories": categories,
        },
    )


@router.post("/tickets/new", response_class=HTMLResponse)
async def new_ticket_submit(request: Request, user=Depends(require_login), db: Session = Depends(get_db)):
    """Handle new ticket creation"""
    form_data = await request.form()

    ticket = Ticket(
        title=form_data.get("title"),
        description=form_data.get("description"),
        client_id=user.id,
        category_id=form_data.get("category_id") or None,
        priority=form_data.get("priority", "normaal"),
    )
    db.add(ticket)
    db.commit()

    # Send email notification
    email_service.send_ticket_created(ticket, user.email)

    return RedirectResponse(
        url=f"/tickets/{ticket.id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def ticket_detail(
    request: Request,
    ticket_id: int,
    user=Depends(require_login),
    db: Session = Depends(get_db),
):
    """Ticket detail page"""
    check_ticket_access(user, ticket_id, db)

    ticket = db.query(Ticket).filter_by(id=ticket_id).first_or_404()

    messages = (
        db.query(Message)
        .filter_by(ticket_id=ticket_id, is_internal=False)
        .order_by(Message.created_at)
        .all()
    )

    notes = []
    time_logs = []
    if user.role in ["fixer", "admin"]:
        notes = (
            db.query(TicketNote)
            .filter_by(ticket_id=ticket_id)
            .order_by(TicketNote.created_at)
            .all()
        )
        time_logs = (
            db.query(TimeLog)
            .filter_by(ticket_id=ticket_id)
            .order_by(TimeLog.created_at.desc())
            .all()
        )

    return template_service.render_template(
        "ticket_detail.html",
        {
            "request": request,
            "user": user,
            "ticket": ticket,
            "messages": messages,
            "notes": notes,
            "time_logs": time_logs,
        },
    )


@router.post("/tickets/{ticket_id}/message", response_class=HTMLResponse)
async def add_message(
    request: Request,
    ticket_id: int,
    user=Depends(require_login),
    db: Session = Depends(get_db),
):
    """Add message to ticket"""
    check_ticket_access(user, ticket_id, db)

    form_data = await request.form()
    content = form_data.get("content")
    is_internal = form_data.get("is_internal") == "on" and user.role in ["fixer", "admin"]

    message = Message(ticket_id=ticket_id, user_id=user.id, content=content, is_internal=is_internal)
    db.add(message)
    db.commit()

    # Send notification to client if fixer responds
    if user.role in ["fixer", "admin"] and not is_internal:
        ticket = db.query(Ticket).filter_by(id=ticket_id).first()
        if ticket:
            email_service.send_message_notification(ticket, message, ticket.client.email)

    return RedirectResponse(
        url=f"/tickets/{ticket_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/tickets/{ticket_id}/note", response_class=HTMLResponse)
async def add_note(
    request: Request,
    ticket_id: int,
    user=Depends(require_fixer),
    db: Session = Depends(get_db),
):
    """Add note to ticket (fixer only)"""
    form_data = await request.form()
    content = form_data.get("content")

    note = TicketNote(ticket_id=ticket_id, user_id=user.id, content=content)
    db.add(note)
    db.commit()

    return RedirectResponse(
        url=f"/tickets/{ticket_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/tickets/{ticket_id}/time", response_class=HTMLResponse)
async def log_time(
    request: Request,
    ticket_id: int,
    user=Depends(require_fixer),
    db: Session = Depends(get_db),
):
    """Log time for ticket (fixer only)"""
    form_data = await request.form()

    hours = int(form_data.get("hours", 0))
    minutes = int(form_data.get("minutes", 0))
    description = form_data.get("description")

    time_log = TimeLog(
        ticket_id=ticket_id, user_id=user.id, hours=hours, minutes=minutes, description=description
    )
    db.add(time_log)

    # Update ticket actual_hours
    ticket = db.query(Ticket).filter_by(id=ticket_id).first()
    time_logs = db.query(TimeLog).filter_by(ticket_id=ticket_id).all()
    ticket.actual_hours = sum(tl.total_hours for tl in time_logs)

    db.commit()

    return RedirectResponse(
        url=f"/tickets/{ticket_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/tickets/{ticket_id}/claim", response_class=HTMLResponse)
async def claim_ticket(
    request: Request,
    ticket_id: int,
    user=Depends(require_fixer),
    db: Session = Depends(get_db),
):
    """Claim a ticket (fixer only)"""
    ticket = db.query(Ticket).filter_by(id=ticket_id).first_or_404()

    if ticket.fixer_id:
        raise HTTPException(status_code=400, detail="Ticket is already claimed")

    ticket.fixer_id = user.id
    db.commit()

    return RedirectResponse(
        url=f"/tickets/{ticket_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/tickets/{ticket_id}/status", response_class=HTMLResponse)
async def update_status(
    request: Request,
    ticket_id: int,
    user=Depends(require_fixer),
    db: Session = Depends(get_db),
):
    """Update ticket status (fixer only)"""
    form_data = await request.form()
    new_status = form_data.get("status")

    ticket = db.query(Ticket).filter_by(id=ticket_id).first_or_404()
    old_status = ticket.status
    ticket.status = new_status

    if new_status == "Gereed":
        ticket.closed_at = datetime.utcnow()
    elif new_status == "Open" and ticket.closed_at:
        ticket.closed_at = None

    db.commit()

    # Send email notification to client
    if old_status != new_status:
        email_service.send_ticket_updated(ticket, ticket.client.email, new_status)

    return RedirectResponse(
        url=f"/tickets/{ticket_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, user=Depends(require_login)):
    """User profile page"""
    return template_service.render_template(
        "profile.html",
        {
            "request": request,
            "user": user,
        },
    )


@router.post("/profile", response_class=HTMLResponse)
async def profile_update(request: Request, user=Depends(require_login), db: Session = Depends(get_db)):
    """Update user profile"""
    form_data = await request.form()

    user.name = form_data.get("name")
    user.company = form_data.get("company")
    db.commit()

    return RedirectResponse(
        url="/profile",
        status_code=status.HTTP_303_SEE_OTHER,
    )
