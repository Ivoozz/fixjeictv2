from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import BlogPost, Testimonial
from ..services.template_service import template_service

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Home page"""
    featured_posts = (
        db.query(BlogPost)
        .filter_by(is_published=True)
        .order_by(BlogPost.published_at.desc())
        .limit(3)
        .all()
    )

    testimonials = db.query(Testimonial).filter_by(is_published=True).all()

    return template_service.render_template(
        "index.html",
        {
            "request": request,
            "featured_posts": featured_posts,
            "testimonials": testimonials,
        },
    )


@router.get("/services", response_class=HTMLResponse)
async def services(request: Request):
    """Services page"""
    return template_service.render_template("services.html", {"request": request})


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About page"""
    return template_service.render_template("about.html", {"request": request})


@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    """Contact page"""
    return template_service.render_template("contact.html", {"request": request})


@router.post("/contact", response_class=HTMLResponse)
async def contact_submit(request: Request, db: Session = Depends(get_db)):
    """Handle contact form submission"""
    form_data = await request.form()

    from ..models import Lead
    from ..email_service import email_service

    lead = Lead(
        name=form_data.get("name"),
        email=form_data.get("email"),
        company=form_data.get("company"),
        phone=form_data.get("phone"),
        message=form_data.get("message"),
    )
    db.add(lead)
    db.commit()

    # Send email notification
    email_service.send_lead_notification(lead)

    return template_service.render_template(
        "contact.html",
        {
            "request": request,
            "success_message": "Bedankt voor uw bericht! We nemen zo snel mogelijk contact op.",
        },
    )


@router.get("/blog", response_class=HTMLResponse)
async def blog(request: Request, db: Session = Depends(get_db)):
    """Blog listing page"""
    posts = (
        db.query(BlogPost)
        .filter_by(is_published=True)
        .order_by(BlogPost.published_at.desc())
        .all()
    )

    return template_service.render_template("blog.html", {"request": request, "posts": posts})


@router.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_post(request: Request, slug: str, db: Session = Depends(get_db)):
    """Single blog post page"""
    post = (
        db.query(BlogPost)
        .filter_by(slug=slug, is_published=True)
        .first_or_404()
    )

    return template_service.render_template("blog_post.html", {"request": request, "post": post})


@router.get("/knowledge-base", response_class=HTMLResponse)
async def knowledge_base(request: Request, db: Session = Depends(get_db)):
    """Knowledge base listing page"""
    from ..models import KnowledgeBase

    posts = (
        db.query(KnowledgeBase)
        .filter_by(is_published=True)
        .order_by(KnowledgeBase.views.desc())
        .all()
    )

    # Get distinct categories
    categories = (
        db.query(KnowledgeBase.category)
        .filter(KnowledgeBase.category.isnot(None))
        .distinct()
        .all()
    )
    categories = [c[0] for c in categories if c[0]]

    return template_service.render_template(
        "knowledge_base.html",
        {
            "request": request,
            "posts": posts,
            "categories": categories,
        },
    )


@router.get("/knowledge-base/{slug}", response_class=HTMLResponse)
async def kb_post(request: Request, slug: str, db: Session = Depends(get_db)):
    """Single knowledge base article page"""
    from ..models import KnowledgeBase

    post = (
        db.query(KnowledgeBase)
        .filter_by(slug=slug, is_published=True)
        .first_or_404()
    )

    # Increment view count
    post.views += 1
    db.commit()

    return template_service.render_template("kb_post.html", {"request": request, "post": post})
