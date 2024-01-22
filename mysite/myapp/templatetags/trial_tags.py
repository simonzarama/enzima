# En un archivo, por ejemplo, templatetags/trial_tags.py

from django import template

register = template.Library()

@register.filter
def percentage_of(value, total):
    try:
        return "%.2f%%" % ((float(value) / float(total)) * 100)
    except (ValueError, ZeroDivisionError):
        return "0%"
