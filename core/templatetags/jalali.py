import jdatetime
from django import template

register = template.Library()


@register.filter
def jalali_date(value, show_time=False):
    if not value:
        return "-"
    dt = value if hasattr(value, "hour") else None
    date_value = value.date() if hasattr(value, "date") else value
    try:
        result = jdatetime.date.fromgregorian(date=date_value).strftime("%Y/%m/%d")
        if show_time and dt:
            result += f" {dt:%H:%M}"
        return result
    except (TypeError, ValueError):
        return value
