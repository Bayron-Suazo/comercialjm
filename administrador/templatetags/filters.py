from django import template

register = template.Library()

@register.filter(name='div')
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None  # o return 0, según tu necesidad