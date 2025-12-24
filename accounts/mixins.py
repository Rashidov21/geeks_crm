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


class TailwindFormMixin:
    """
    Form mixin to add Tailwind CSS classes to fields.
    """
    input_class = "w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for name, field in form.fields.items():
            widget = field.widget
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {self.input_class}".strip()
            if widget.__class__.__name__ == "CheckboxInput":
                widget.attrs["class"] = widget.attrs["class"].replace(self.input_class, "").strip()
                widget.attrs["class"] += " rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        return form


class CrudListViewMixin:
    """
    Mixin for CRUD List Views with pagination, search, and filters
    """
    paginate_by = 20
    search_fields = []
    filter_fields = []
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search
        search_query = self.request.GET.get('search', '')
        if search_query and self.search_fields:
            from django.db.models import Q
            q = Q()
            for field in self.search_fields:
                q |= Q(**{f"{field}__icontains": search_query})
            queryset = queryset.filter(q)
        
        # Ordering
        if self.ordering:
            queryset = queryset.order_by(*self.ordering)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class CrudFormViewMixin(TailwindFormMixin):
    """
    Enhanced form mixin with better styling and validation
    """
    form_color = 'indigo'
    success_message = "Ma'lumot muvaffaqiyatli saqlandi!"
    
    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Iltimos, xatolarni tuzating va qayta urinib ko'ring.")
        return super().form_invalid(form)


class CrudDetailViewMixin:
    """
    Mixin for CRUD Detail Views with related objects
    """
    related_objects = []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_objects'] = self.get_related_objects()
        return context
    
    def get_related_objects(self):
        """Override this method to return related objects"""
        return []
