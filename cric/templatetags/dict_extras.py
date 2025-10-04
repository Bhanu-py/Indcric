from django import template

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    if dictionary is None:
        return None
    try:
        return dictionary.get(str(key))
    except (AttributeError, TypeError):
        return None


@register.filter(name='stringformat')
def stringformat(value, arg):
    """Format a value as a string with the given format"""
    try:
        return arg % value
    except (TypeError, ValueError):
        return str(value)
