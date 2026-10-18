from django import template

register = template.Library()


@register.filter
def duration(seconds):
    """Format seconds as m:ss, e.g. 95 -> '1:35'."""
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return ""
    return f"{seconds // 60}:{seconds % 60:02d}"
