"""
Utility functions for FixJeICT v3
"""


def flash(request, message: str, category: str = "info"):
    """
    Add a flash message to the session (Flask compatibility)

    Args:
        request: FastAPI Request object
        message: Message text
        category: Message category (info, success, warning, danger)
    """
    if "_flashes" not in request.session:
        request.session["_flashes"] = []

    request.session["_flashes"].append({
        "category": category,
        "message": message
    })


def get_flashed_messages(request):
    """
    Get and clear flash messages from session (Flask compatibility)

    Args:
        request: FastAPI Request object

    Returns:
        List of flash messages
    """
    messages = request.session.pop("_flashes", [])
    return messages
