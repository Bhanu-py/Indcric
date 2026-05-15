from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter(name='mul')
def mul(value, arg):
    return value * arg


ROLE_EMOJI = {
    "batsman": "\U0001f3cf",      # cricket bat
    "bat": "\U0001f3cf",
    "batting": "\U0001f3cf",
    "bowler": "\U0001f3af",       # dart / target
    "bowl": "\U0001f3af",
    "bowling": "\U0001f3af",
    "allrounder": "⭐",       # star
    "all-rounder": "⭐",
    "allr": "⭐",
    "fielding": "\U0001f938",     # gymnast
    "field": "\U0001f938",
    "keeper": "\U0001f9e4",       # gloves
    "wicketkeeper": "\U0001f9e4",
}


@register.filter(name="role_emoji")
def role_emoji(role):
    if not role:
        return ""
    return ROLE_EMOJI.get(str(role).strip().lower(), "")
