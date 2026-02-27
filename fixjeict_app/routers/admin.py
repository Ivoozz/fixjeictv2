import re
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from ..auth import verify_admin
from ..database import get_db
from ..models import (
    BlogPost,
    Category,
    KnowledgeBase,
    Lead,
    SiteConfig,
    Testimonial,
    Ticket,
    User,
)
from ..services.template_service import template_service

router = APIRouter()
security = HTTPBasic()


@router.get("/admin", response_class=HTMLResponse)
async def admin_index(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin dashboard"""
    verify_admin(credentials)

    stats = {
        "tickets": db.query(Ticket).count(),
        "open_tickets": db.query(Ticket).filter_by(status="Open").count(),
        "users": db.query(User).count(),
        "leads": db.query(Lead).filter_by(status="new").count(),
    }

    recent_tickets = (
        db.query(Ticket)
        .order_by(Ticket.created_at.desc())
        .limit(5)
        .all()
    )

    recent_leads = (
        db.query(Lead)
        .filter_by(status="new")
        .order_by(Lead.created_at.desc())
        .limit(5)
        .all()
    )

    return template_service.render_template(
        "admin_index.html",
        {
            "request": request,
            "stats": stats,
            "recent_tickets": recent_tickets,
            "recent_leads": recent_leads,
        },
    )


# Ticket routes
@router.get("/admin/tickets", response_class=HTMLResponse)
async def admin_tickets(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin tickets listing"""
    verify_admin(credentials)

    status_filter = request.query_params.get("status")
    query = db.query(Ticket)

    if status_filter:
        query = query.filter_by(status=status_filter)

    tickets = query.order_by(Ticket.updated_at.desc()).all()

    return template_service.render_template(
        "admin_tickets.html",
        {
            "request": request,
            "tickets": tickets,
            "status_filter": status_filter,
        },
    )


@router.get("/admin/tickets/{ticket_id}", response_class=HTMLResponse)
async def admin_ticket_detail(
    request: Request,
    ticket_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin ticket detail"""
    verify_admin(credentials)

    ticket = db.query(Ticket).filter_by(id=ticket_id).first_or_404()

    from ..models import Message, TicketNote, TimeLog

    messages = (
        db.query(Message)
        .filter_by(ticket_id=ticket_id)
        .order_by(Message.created_at)
        .all()
    )
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
        "admin_ticket_detail.html",
        {
            "request": request,
            "ticket": ticket,
            "messages": messages,
            "notes": notes,
            "time_logs": time_logs,
        },
    )


@router.get("/admin/tickets/{ticket_id}/edit", response_class=HTMLResponse)
async def admin_ticket_edit(
    request: Request,
    ticket_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin ticket edit form"""
    verify_admin(credentials)

    ticket = db.query(Ticket).filter_by(id=ticket_id).first_or_404()
    categories = db.query(Category).filter_by(is_active=True).order_by(Category.order).all()
    fixers = db.query(User).filter(User.role.in_(["fixer", "admin"])).all()

    return template_service.render_template(
        "admin_ticket_edit.html",
        {
            "request": request,
            "ticket": ticket,
            "categories": categories,
            "fixers": fixers,
        },
    )


@router.post("/admin/tickets/{ticket_id}/edit", response_class=HTMLResponse)
async def admin_ticket_edit_submit(
    request: Request,
    ticket_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin ticket edit submission"""
    verify_admin(credentials)

    ticket = db.query(Ticket).filter_by(id=ticket_id).first_or_404()
    form_data = await request.form()

    ticket.title = form_data.get("title")
    ticket.description = form_data.get("description")
    ticket.status = form_data.get("status")
    ticket.priority = form_data.get("priority")
    ticket.category_id = form_data.get("category_id") or None
    ticket.estimated_hours = float(form_data.get("estimated_hours")) if form_data.get("estimated_hours") else None

    fixer_id = form_data.get("fixer_id")
    ticket.fixer_id = int(fixer_id) if fixer_id else None

    if ticket.status == "Gereed" and not ticket.closed_at:
        ticket.closed_at = datetime.utcnow()
    elif ticket.status != "Gereed" and ticket.closed_at:
        ticket.closed_at = None

    db.commit()

    return RedirectResponse(
        url=f"/admin/tickets/{ticket_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/admin/tickets/{ticket_id}/delete", response_class=HTMLResponse)
async def admin_ticket_delete(
    request: Request,
    ticket_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin ticket delete"""
    verify_admin(credentials)

    ticket = db.query(Ticket).filter_by(id=ticket_id).first_or_404()
    db.delete(ticket)
    db.commit()

    return RedirectResponse(
        url="/admin/tickets",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/admin/tickets/{ticket_id}/message", response_class=HTMLResponse)
async def admin_ticket_message(
    request: Request,
    ticket_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin add message to ticket"""
    verify_admin(credentials)

    ticket = db.query(Ticket).filter_by(id=ticket_id).first_or_404()
    form_data = await request.form()

    # Get or create admin user
    admin_user = db.query(User).filter_by(role="admin").first()
    if not admin_user:
        admin_user = User(email="admin@fixjeict.nl", name="Admin", role="admin")
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

    from ..models import Message

    content = form_data.get("content")
    is_internal = form_data.get("is_internal") == "on"

    message = Message(ticket_id=ticket_id, user_id=admin_user.id, content=content, is_internal=is_internal)
    db.add(message)
    db.commit()

    return RedirectResponse(
        url=f"/admin/tickets/{ticket_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/admin/tickets/{ticket_id}/time", response_class=HTMLResponse)
async def admin_ticket_time(
    request: Request,
    ticket_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin log time for ticket"""
    verify_admin(credentials)

    ticket = db.query(Ticket).filter_by(id=ticket_id).first_or_404()
    form_data = await request.form()

    # Get or create admin user
    admin_user = db.query(User).filter_by(role="admin").first()
    if not admin_user:
        admin_user = User(email="admin@fixjeict.nl", name="Admin", role="admin")
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

    hours = int(form_data.get("hours", 0))
    minutes = int(form_data.get("minutes", 0))
    description = form_data.get("description")

    time_log = TimeLog(
        ticket_id=ticket_id, user_id=admin_user.id, hours=hours, minutes=minutes, description=description
    )
    db.add(time_log)

    from ..models import TimeLog

    time_logs = db.query(TimeLog).filter_by(ticket_id=ticket_id).all()
    ticket.actual_hours = sum(tl.total_hours for tl in time_logs)
    db.commit()

    return RedirectResponse(
        url=f"/admin/tickets/{ticket_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# User routes
@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin users listing"""
    verify_admin(credentials)

    users = db.query(User).order_by(User.created_at.desc()).all()

    return template_service.render_template(
        "admin_users.html",
        {
            "request": request,
            "users": users,
        },
    )


@router.get("/admin/users/{user_id}/edit", response_class=HTMLResponse)
async def admin_user_edit(
    request: Request,
    user_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin user edit form"""
    verify_admin(credentials)

    user = db.query(User).filter_by(id=user_id).first_or_404()

    return template_service.render_template(
        "admin_user_edit.html",
        {
            "request": request,
            "user": user,
        },
    )


@router.post("/admin/users/{user_id}/edit", response_class=HTMLResponse)
async def admin_user_edit_submit(
    request: Request,
    user_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin user edit submission"""
    verify_admin(credentials)

    user = db.query(User).filter_by(id=user_id).first_or_404()
    form_data = await request.form()

    user.name = form_data.get("name")
    user.company = form_data.get("company")
    user.role = form_data.get("role")
    user.is_active = form_data.get("is_active") == "on"
    db.commit()

    return RedirectResponse(
        url="/admin/users",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/admin/users/{user_id}/delete", response_class=HTMLResponse)
async def admin_user_delete(
    request: Request,
    user_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin user delete"""
    verify_admin(credentials)

    user = db.query(User).filter_by(id=user_id).first_or_404()
    db.delete(user)
    db.commit()

    return RedirectResponse(
        url="/admin/users",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# Category routes
@router.get("/admin/categories", response_class=HTMLResponse)
async def admin_categories(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin categories listing"""
    verify_admin(credentials)

    categories = db.query(Category).order_by(Category.order).all()

    return template_service.render_template(
        "admin_categories.html",
        {
            "request": request,
            "categories": categories,
        },
    )


@router.get("/admin/categories/new", response_class=HTMLResponse)
async def admin_category_new(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
):
    """Admin new category form"""
    verify_admin(credentials)

    return template_service.render_template(
        "admin_category_edit.html",
        {
            "request": request,
            "category": None,
        },
    )


@router.post("/admin/categories/new", response_class=HTMLResponse)
async def admin_category_new_submit(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin new category submission"""
    verify_admin(credentials)

    form_data = await request.form()

    category = Category(
        name=form_data.get("name"),
        description=form_data.get("description"),
        icon=form_data.get("icon"),
        order=int(form_data.get("order", 0)),
    )
    db.add(category)
    db.commit()

    return RedirectResponse(
        url="/admin/categories",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/admin/categories/{category_id}/edit", response_class=HTMLResponse)
async def admin_category_edit(
    request: Request,
    category_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin category edit form"""
    verify_admin(credentials)

    category = db.query(Category).filter_by(id=category_id).first_or_404()

    return template_service.render_template(
        "admin_category_edit.html",
        {
            "request": request,
            "category": category,
        },
    )


@router.post("/admin/categories/{category_id}/edit", response_class=HTMLResponse)
async def admin_category_edit_submit(
    request: Request,
    category_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin category edit submission"""
    verify_admin(credentials)

    category = db.query(Category).filter_by(id=category_id).first_or_404()
    form_data = await request.form()

    category.name = form_data.get("name")
    category.description = form_data.get("description")
    category.icon = form_data.get("icon")
    category.order = int(form_data.get("order", 0))
    category.is_active = form_data.get("is_active") == "on"
    db.commit()

    return RedirectResponse(
        url="/admin/categories",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/admin/categories/{category_id}/delete", response_class=HTMLResponse)
async def admin_category_delete(
    request: Request,
    category_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin category delete"""
    verify_admin(credentials)

    category = db.query(Category).filter_by(id=category_id).first_or_404()
    db.delete(category)
    db.commit()

    return RedirectResponse(
        url="/admin/categories",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# Blog routes
@router.get("/admin/blog", response_class=HTMLResponse)
async def admin_blog(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin blog listing"""
    verify_admin(credentials)

    posts = db.query(BlogPost).order_by(BlogPost.created_at.desc()).all()

    return template_service.render_template(
        "admin_blog.html",
        {
            "request": request,
            "posts": posts,
        },
    )


@router.get("/admin/blog/new", response_class=HTMLResponse)
async def admin_blog_new(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
):
    """Admin new blog post form"""
    verify_admin(credentials)

    return template_service.render_template(
        "admin_blog_edit.html",
        {
            "request": request,
            "post": None,
        },
    )


@router.post("/admin/blog/new", response_class=HTMLResponse)
async def admin_blog_new_submit(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin new blog post submission"""
    verify_admin(credentials)

    form_data = await request.form()
    title = form_data.get("title")
    slug = re.sub(r"[^\w\-]", "-", title.lower()).strip("-")

    post = BlogPost(
        title=title,
        slug=slug,
        content=form_data.get("content"),
        excerpt=form_data.get("excerpt"),
        image_url=form_data.get("image_url"),
        is_published=form_data.get("is_published") == "on",
        published_at=datetime.utcnow() if form_data.get("is_published") == "on" else None,
    )
    db.add(post)
    db.commit()

    return RedirectResponse(
        url="/admin/blog",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/admin/blog/{post_id}/edit", response_class=HTMLResponse)
async def admin_blog_edit(
    request: Request,
    post_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin blog post edit form"""
    verify_admin(credentials)

    post = db.query(BlogPost).filter_by(id=post_id).first_or_404()

    return template_service.render_template(
        "admin_blog_edit.html",
        {
            "request": request,
            "post": post,
        },
    )


@router.post("/admin/blog/{post_id}/edit", response_class=HTMLResponse)
async def admin_blog_edit_submit(
    request: Request,
    post_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin blog post edit submission"""
    verify_admin(credentials)

    post = db.query(BlogPost).filter_by(id=post_id).first_or_404()
    form_data = await request.form()

    post.title = form_data.get("title")
    post.content = form_data.get("content")
    post.excerpt = form_data.get("excerpt")
    post.image_url = form_data.get("image_url")
    post.is_published = form_data.get("is_published") == "on"

    was_published = post.published_at is not None
    is_now_published = post.is_published

    if is_now_published and not was_published:
        post.published_at = datetime.utcnow()

    db.commit()

    return RedirectResponse(
        url="/admin/blog",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/admin/blog/{post_id}/delete", response_class=HTMLResponse)
async def admin_blog_delete(
    request: Request,
    post_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin blog post delete"""
    verify_admin(credentials)

    post = db.query(BlogPost).filter_by(id=post_id).first_or_404()
    db.delete(post)
    db.commit()

    return RedirectResponse(
        url="/admin/blog",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# Knowledge Base routes
@router.get("/admin/kb", response_class=HTMLResponse)
async def admin_kb(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin knowledge base listing"""
    verify_admin(credentials)

    posts = db.query(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()).all()

    return template_service.render_template(
        "admin_kb.html",
        {
            "request": request,
            "posts": posts,
        },
    )


@router.get("/admin/kb/new", response_class=HTMLResponse)
async def admin_kb_new(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
):
    """Admin new KB article form"""
    verify_admin(credentials)

    return template_service.render_template(
        "admin_kb_edit.html",
        {
            "request": request,
            "post": None,
        },
    )


@router.post("/admin/kb/new", response_class=HTMLResponse)
async def admin_kb_new_submit(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin new KB article submission"""
    verify_admin(credentials)

    form_data = await request.form()
    title = form_data.get("title")
    slug = re.sub(r"[^\w\-]", "-", title.lower()).strip("-")

    post = KnowledgeBase(
        title=title,
        slug=slug,
        content=form_data.get("content"),
        category=form_data.get("category"),
        is_published=form_data.get("is_published") == "on",
    )
    db.add(post)
    db.commit()

    return RedirectResponse(
        url="/admin/kb",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/admin/kb/{post_id}/edit", response_class=HTMLResponse)
async def admin_kb_edit(
    request: Request,
    post_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin KB article edit form"""
    verify_admin(credentials)

    post = db.query(KnowledgeBase).filter_by(id=post_id).first_or_404()

    return template_service.render_template(
        "admin_kb_edit.html",
        {
            "request": request,
            "post": post,
        },
    )


@router.post("/admin/kb/{post_id}/edit", response_class=HTMLResponse)
async def admin_kb_edit_submit(
    request: Request,
    post_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin KB article edit submission"""
    verify_admin(credentials)

    post = db.query(KnowledgeBase).filter_by(id=post_id).first_or_404()
    form_data = await request.form()

    post.title = form_data.get("title")
    post.content = form_data.get("content")
    post.category = form_data.get("category")
    post.is_published = form_data.get("is_published") == "on"
    db.commit()

    return RedirectResponse(
        url="/admin/kb",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/admin/kb/{post_id}/delete", response_class=HTMLResponse)
async def admin_kb_delete(
    request: Request,
    post_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin KB article delete"""
    verify_admin(credentials)

    post = db.query(KnowledgeBase).filter_by(id=post_id).first_or_404()
    db.delete(post)
    db.commit()

    return RedirectResponse(
        url="/admin/kb",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# Lead routes
@router.get("/admin/leads", response_class=HTMLResponse)
async def admin_leads(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin leads listing"""
    verify_admin(credentials)

    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()

    return template_service.render_template(
        "admin_leads.html",
        {
            "request": request,
            "leads": leads,
        },
    )


@router.get("/admin/leads/{lead_id}/edit", response_class=HTMLResponse)
async def admin_lead_edit(
    request: Request,
    lead_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin lead edit form"""
    verify_admin(credentials)

    lead = db.query(Lead).filter_by(id=lead_id).first_or_404()

    return template_service.render_template(
        "admin_lead_edit.html",
        {
            "request": request,
            "lead": lead,
        },
    )


@router.post("/admin/leads/{lead_id}/edit", response_class=HTMLResponse)
async def admin_lead_edit_submit(
    request: Request,
    lead_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin lead edit submission"""
    verify_admin(credentials)

    lead = db.query(Lead).filter_by(id=lead_id).first_or_404()
    form_data = await request.form()

    lead.status = form_data.get("status")
    db.commit()

    return RedirectResponse(
        url="/admin/leads",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/admin/leads/{lead_id}/delete", response_class=HTMLResponse)
async def admin_lead_delete(
    request: Request,
    lead_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin lead delete"""
    verify_admin(credentials)

    lead = db.query(Lead).filter_by(id=lead_id).first_or_404()
    db.delete(lead)
    db.commit()

    return RedirectResponse(
        url="/admin/leads",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# Testimonial routes
@router.get("/admin/testimonials", response_class=HTMLResponse)
async def admin_testimonials(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin testimonials listing"""
    verify_admin(credentials)

    testimonials = db.query(Testimonial).order_by(Testimonial.created_at.desc()).all()

    return template_service.render_template(
        "admin_testimonials.html",
        {
            "request": request,
            "testimonials": testimonials,
        },
    )


@router.get("/admin/testimonials/new", response_class=HTMLResponse)
async def admin_testimonial_new(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
):
    """Admin new testimonial form"""
    verify_admin(credentials)

    return template_service.render_template(
        "admin_testimonial_edit.html",
        {
            "request": request,
            "testimonial": None,
        },
    )


@router.post("/admin/testimonials/new", response_class=HTMLResponse)
async def admin_testimonial_new_submit(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin new testimonial submission"""
    verify_admin(credentials)

    form_data = await request.form()

    testimonial = Testimonial(
        name=form_data.get("name"),
        company=form_data.get("company"),
        content=form_data.get("content"),
        rating=int(form_data.get("rating", 5)),
        is_published=form_data.get("is_published") == "on",
    )
    db.add(testimonial)
    db.commit()

    return RedirectResponse(
        url="/admin/testimonials",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/admin/testimonials/{testimonial_id}/edit", response_class=HTMLResponse)
async def admin_testimonial_edit(
    request: Request,
    testimonial_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin testimonial edit form"""
    verify_admin(credentials)

    testimonial = db.query(Testimonial).filter_by(id=testimonial_id).first_or_404()

    return template_service.render_template(
        "admin_testimonial_edit.html",
        {
            "request": request,
            "testimonial": testimonial,
        },
    )


@router.post("/admin/testimonials/{testimonial_id}/edit", response_class=HTMLResponse)
async def admin_testimonial_edit_submit(
    request: Request,
    testimonial_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin testimonial edit submission"""
    verify_admin(credentials)

    testimonial = db.query(Testimonial).filter_by(id=testimonial_id).first_or_404()
    form_data = await request.form()

    testimonial.name = form_data.get("name")
    testimonial.company = form_data.get("company")
    testimonial.content = form_data.get("content")
    testimonial.rating = int(form_data.get("rating", 5))
    testimonial.is_published = form_data.get("is_published") == "on"
    db.commit()

    return RedirectResponse(
        url="/admin/testimonials",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/admin/testimonials/{testimonial_id}/delete", response_class=HTMLResponse)
async def admin_testimonial_delete(
    request: Request,
    testimonial_id: int,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin testimonial delete"""
    verify_admin(credentials)

    testimonial = db.query(Testimonial).filter_by(id=testimonial_id).first_or_404()
    db.delete(testimonial)
    db.commit()

    return RedirectResponse(
        url="/admin/testimonials",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# Settings routes
@router.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin settings page"""
    verify_admin(credentials)

    production_mode = db.query(SiteConfig).filter_by(key="production_mode").first()
    production_mode_value = production_mode.value if production_mode else "false"

    maintenance_mode = db.query(SiteConfig).filter_by(key="maintenance_mode").first()
    maintenance_mode_value = maintenance_mode.value if maintenance_mode else "false"

    configs = db.query(SiteConfig).order_by(SiteConfig.key).all()

    return template_service.render_template(
        "admin_settings.html",
        {
            "request": request,
            "production_mode": production_mode_value,
            "maintenance_mode": maintenance_mode_value,
            "configs": configs,
        },
    )


@router.post("/admin/settings/toggle/{key}", response_class=HTMLResponse)
async def admin_setting_toggle(
    request: Request,
    key: str,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Admin setting toggle"""
    verify_admin(credentials)

    config = db.query(SiteConfig).filter_by(key=key).first()
    if not config:
        config = SiteConfig(
            key=key,
            value="false",
            description="Production mode toggle"
            if key == "production_mode"
            else "Maintenance mode toggle",
        )
        db.add(config)

    # Toggle value
    config.value = "true" if config.value != "true" else "false"
    db.commit()

    return RedirectResponse(
        url="/admin/settings",
        status_code=status.HTTP_303_SEE_OTHER,
    )
