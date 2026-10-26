from django import template

from core.i18n import DEFAULT_LANG, pick, tr

register = template.Library()


@register.filter
def has_group(user, group_name):
    if not getattr(user, 'is_authenticated', False):
        return False
    return user.groups.filter(name=group_name).exists()


@register.simple_tag(takes_context=True)
def t(context, key, **params):
    """{% t "login.title" %} — translated into the visitor's language."""
    return tr(context.get('LANG', DEFAULT_LANG), key, **params)


@register.simple_tag(takes_context=True)
def loc(context, value):
    """{% loc p.tagline %} — pick the visitor's language from a {'pl': .., 'en': ..} dict."""
    return pick(value, context.get('LANG', DEFAULT_LANG))
