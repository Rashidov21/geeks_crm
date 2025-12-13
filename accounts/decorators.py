from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*allowed_roles):
    """
    Decorator to check if user has required role
    Usage: @role_required('admin', 'manager')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Iltimos, avval tizimga kiring.')
                return redirect('accounts:login')
            
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, 'Sizda bu sahifaga kirish huquqi yo\'q.')
            return redirect('accounts:login')
        
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Decorator to check if user is admin
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Iltimos, avval tizimga kiring.')
            return redirect('accounts:login')
        
        if request.user.is_superuser or request.user.is_admin:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Sizda bu sahifaga kirish huquqi yo\'q.')
        return redirect('accounts:login')
    
    return wrapper


def mentor_required(view_func):
    """
    Decorator to check if user is mentor
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Iltimos, avval tizimga kiring.')
            return redirect('accounts:login')
        
        if request.user.is_superuser or request.user.is_admin or request.user.is_mentor:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Sizda bu sahifaga kirish huquqi yo\'q.')
        return redirect('accounts:login')
    
    return wrapper

