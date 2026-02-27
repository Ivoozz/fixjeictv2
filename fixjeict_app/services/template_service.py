from pathlib import Path
from typing import Any, Dict

from fastapi import Request
from fastapi.templating import Jinja2Templates

from ..config import settings


def url_for_static(filename: str) -> str:
    """Generate URL for static files (Flask compatibility)"""
    return f"/static/{filename}"


def url_for(route_name: str, **params: Any) -> str:
    """Generate URL for named routes (Flask compatibility)"""
    # Map Flask route names to FastAPI URLs
    route_map = {
        'index': '/',
        'services': '/services',
        'about': '/about',
        'contact': '/contact',
        'blog': '/blog',
        'knowledge_base': '/knowledge-base',
        'login': '/login',
        'dashboard': '/dashboard',
        'profile': '/profile',
        'logout': '/logout',
    }

    # Handle dynamic routes
    if route_name == 'blog_post':
        slug = params.get('slug', '')
        return f"/blog/{slug}"
    elif route_name == 'kb_post':
        slug = params.get('slug', '')
        return f"/knowledge-base/{slug}"
    elif route_name == 'ticket_detail':
        ticket_id = params.get('id', '')
        return f"/tickets/{ticket_id}"
    elif route_name == 'new_ticket':
        return '/tickets/new'

    return route_map.get(route_name, f"/{route_name}")


class TemplateService:
    """Jinja2 template service for FastAPI with Flask compatibility"""

    def __init__(self):
        # Set up template directory
        template_dir = Path(__file__).parent.parent / "templates"

        # If templates don't exist in fixjeict_app, use the root level
        if not template_dir.exists():
            template_dir = Path(__file__).parent.parent.parent / "fixjeict_app" / "templates"

        self.templates = Jinja2Templates(directory=str(template_dir))

        # Add Flask-compatible functions to global context
        self.templates.env.globals['url_for'] = url_for
        self.templates.env.globals['url_for_static'] = url_for_static

    def render_template(self, template_name: str, context: Dict[str, Any] = None):
        """Render a Jinja2 template"""
        if context is None:
            context = {}

        return self.templates.TemplateResponse(template_name, context)

    def get_url_for(self, name: str, **path_params: Any) -> str:
        """Get URL for a named route (helper for templates)"""
        return url_for(name, **path_params)


# Global template service instance
template_service = TemplateService()
