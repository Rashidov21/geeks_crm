from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Dictionary dan key bo'yicha qiymat olish"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def percentage(value, total):
    """Foiz hisoblash"""
    if total == 0:
        return 0
    return (value / total) * 100

