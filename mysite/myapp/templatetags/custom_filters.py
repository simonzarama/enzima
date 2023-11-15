from django import template

register = template.Library()

@register.filter(name='endswith')
def endswith(value, arg):
    """Comprueba si el valor termina con el argumento proporcionado."""
    return str(value).endswith(str(arg))
