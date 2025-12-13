"""
Mixin classes for role-based access control
"""
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect


class RoleRequiredMixin:
    """
    Mixin to check if user has required role
    Usage: class MyView(RoleRequiredMixin, View):
              allowed_roles = ['admin', 'manager']
    """
    allowed_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Iltimos, avval tizimga kiring.')
            return redirect('accounts:login')
        
        if not request.user.is_superuser and request.user.role not in self.allowed_roles:
            messages.error(request, 'Sizda bu sahifaga kirish huquqi yo\'q.')
            return redirect('accounts:login')
        
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin:
    """
    Mixin to check if user is admin
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Iltimos, avval tizimga kiring.')
            return redirect('accounts:login')
        
        if not request.user.is_superuser and not request.user.is_admin:
            messages.error(request, 'Sizda bu sahifaga kirish huquqi yo\'q.')
            return redirect('accounts:login')
        
        return super().dispatch(request, *args, **kwargs)


class MentorRequiredMixin:
    """
    Mixin to check if user is mentor
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Iltimos, avval tizimga kiring.')
            return redirect('accounts:login')
        
        if not request.user.is_superuser and not request.user.is_admin and not request.user.is_mentor:
            messages.error(request, 'Sizda bu sahifaga kirish huquqi yo\'q.')
            return redirect('accounts:login')
        
        return super().dispatch(request, *args, **kwargs)

