from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..auth import generate_auth_token, get_or_create_user, verify_auth_token
from ..database import get_db
from ..email_service import email_service
from ..services.template_service import template_service

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """Login page"""
    return template_service.render_template("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, db: Session = Depends(get_db)):
    """Handle login form submission - send magic link"""
    form_data = await request.form()
    email = form_data.get("email", "").strip()

    if not email:
        return template_service.render_template(
            "login.html",
            {
                "request": request,
                "error_message": "Vul uw emailadres in.",
            },
        )

    # Get or create user
    user = get_or_create_user(email, db)
    was_new = user.created_at == user.last_login

    # Generate and send magic link
    token = generate_auth_token(user.id, db)
    email_service.send_magic_link(user.email, token, user.name)

    return template_service.render_template(
        "login_sent.html",
        {
            "request": request,
            "email": user.email,
            "new_account": was_new,
        },
    )


@router.get("/login/sent", response_class=HTMLResponse)
async def login_sent(request: Request):
    """Login sent confirmation page"""
    email = request.query_params.get("email", "")
    return template_service.render_template("login_sent.html", {"request": request, "email": email})


@router.get("/auth/verify/{token}", response_class=HTMLResponse)
async def auth_verify(request: Request, token: str, db: Session = Depends(get_db)):
    """Verify magic link token and login user"""
    user = verify_auth_token(token, db)

    if not user:
        return template_service.render_template(
            "login.html",
            {
                "request": request,
                "error_message": "Ongeldige of verlopen login link. Vraag een nieuwe aan.",
            },
        )

    # Set session
    request.session["user_id"] = user.id
    request.session["user_name"] = user.name
    request.session["user_role"] = user.role

    return RedirectResponse(
        url="/dashboard",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    """Logout user"""
    request.session.clear()
    return RedirectResponse(
        url="/",
        status_code=status.HTTP_303_SEE_OTHER,
    )
