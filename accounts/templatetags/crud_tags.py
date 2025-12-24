from django import template

register = template.Library()


@register.filter
def split(value, arg):
    """Split string by delimiter"""
    return value.split(arg)


@register.filter
def getattr(obj, attr):
    """Get attribute from object"""
    try:
        # Use object.__getattribute__ to avoid recursion with built-in getattr
        if hasattr(obj, attr):
            return object.__getattribute__(obj, attr)
        elif hasattr(obj, '__getitem__'):
            return obj[attr]
        return '-'
    except:
        return '-'


@register.filter
def get_field_icon(field_name):
    """Get icon for field name"""
    icons = {
        'phone': 'fa-phone',
        'email': 'fa-envelope',
        'date': 'fa-calendar',
        'status': 'fa-info-circle',
        'name': 'fa-user',
        'created_at': 'fa-clock',
        'updated_at': 'fa-clock',
    }
    return icons.get(field_name.lower(), 'fa-circle')


@register.simple_tag
def can_user_edit(user, obj=None):
    """Check if user can edit"""
    if user.is_superuser or user.is_admin:
        return True
    if hasattr(obj, 'created_by') and obj.created_by == user:
        return True
    return False


@register.simple_tag
def can_user_delete(user, obj=None):
    """Check if user can delete"""
    if user.is_superuser or user.is_admin:
        return True
    return False

