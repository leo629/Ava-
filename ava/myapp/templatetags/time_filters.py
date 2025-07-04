from django import template
from django.utils.timesince import timesince
from datetime import datetime

register = template.Library()

@register.filter
def humanize_timesince(value):
    if not value or not isinstance(value, datetime):
        return "Unknown"
    return timesince(value).replace(",", "")
