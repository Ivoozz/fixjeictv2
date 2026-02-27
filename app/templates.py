from fastapi.templating import Jinja2Templates
import os

# Get the absolute path to the templates directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=templates_dir)


def format_datetime(value, format="%d-%m-%Y %H:%M"):
    """Format a datetime object"""
    if value is None:
        return ""
    return value.strftime(format)


def format_date(value, format="%d-%m-%Y"):
    """Format a date"""
    if value is None:
        return ""
    return value.strftime(format)


def status_color(status):
    """Get Bootstrap color class for status"""
    colors = {
        "open": "danger",
        "in_progress": "warning",
        "resolved": "success",
        "closed": "secondary"
    }
    return colors.get(status, "primary")


def priority_color(priority):
    """Get Bootstrap color class for priority"""
    colors = {
        "low": "success",
        "medium": "info",
        "high": "warning",
        "urgent": "danger"
    }
    return colors.get(priority, "primary")


def status_label(status):
    """Get Dutch label for status"""
    labels = {
        "open": "Open",
        "in_progress": "In behandeling",
        "resolved": "Opgelost",
        "closed": "Gesloten"
    }
    return labels.get(status, status)


def priority_label(priority):
    """Get Dutch label for priority"""
    labels = {
        "low": "Laag",
        "medium": "Normaal",
        "high": "Hoog",
        "urgent": "Spoed"
    }
    return labels.get(priority, priority)


# Register custom filters
templates.env.filters["datetime"] = format_datetime
templates.env.filters["date"] = format_date
templates.env.filters["status_color"] = status_color
templates.env.filters["priority_color"] = priority_color
templates.env.filters["status_label"] = status_label
templates.env.filters["priority_label"] = priority_label
