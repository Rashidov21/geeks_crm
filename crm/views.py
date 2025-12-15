from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from .models import (
    Lead, LeadStatus, FollowUp, TrialLesson, SalesProfile,
    WorkSchedule, Leave, SalesKPI, Message
)
from accounts.mixins import RoleRequiredMixin, AdminRequiredMixin, TailwindFormMixin
from courses.models import Group, Room


class LeadListView(LoginRequiredMixin, ListView):
    """
    Leadlar ro'yxati (Kanban board uchun)
    """
    model = Lead
    template_name = 'crm/lead_list.html'
    context_object_name = 'leads'
    
    def get_queryset(self):
        queryset = Lead.objects.select_related('status', 'sales', 'course', 'branch')
        
        # Role bo'yicha filtrlash
        if self.request.user.is_sales:
            queryset = queryset.filter(sales=self.request.user)
        elif self.request.user.is_sales_manager:
            # Manager o'z filialidagi barcha lidlarni ko'radi
            branch = None
            if hasattr(self.request.user, 'student_profile') and self.request.user.student_profile:
                branch = self.request.user.student_profile.branch
            if branch:
                queryset = queryset.filter(branch=branch)
        
        # Status bo'yicha filtrlash
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status__code=status_filter)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Barcha statuslar
        context['statuses'] = LeadStatus.objects.filter(is_active=True).order_by('order')
        
        # Stats for cards
        context['total_leads'] = Lead.objects.count()
        context['enrolled_leads'] = Lead.objects.filter(status__code='enrolled').count()
        context['pending_leads'] = Lead.objects.filter(
            status__code__in=['new', 'contacted', 'interested']
        ).count()
        from crm.models import FollowUp
        context['overdue_followups'] = FollowUp.objects.filter(
            is_completed=False,
            scheduled_at__lt=timezone.now()
        ).count()
        
        return context


class LeadDetailView(LoginRequiredMixin, DetailView):
    """
    Lead batafsil ma'lumotlari
    """
    model = Lead
    template_name = 'crm/lead_detail.html'
    context_object_name = 'lead'
    
    def get_queryset(self):
        queryset = Lead.objects.select_related('status', 'sales', 'course', 'branch', 'trial_group', 'trial_room')
        
        if self.request.user.is_sales:
            queryset = queryset.filter(sales=self.request.user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lead = self.object
        
        # Follow-up'lar
        context['followups'] = FollowUp.objects.filter(lead=lead).order_by('scheduled_at')
        
        # Tarix
        context['history'] = lead.history.all().order_by('-created_at')
        
        # Sinov darslari
        context['trial_lessons'] = TrialLesson.objects.filter(lead=lead).order_by('-date')
        
        return context


class LeadCreateView(TailwindFormMixin, RoleRequiredMixin, CreateView):
    """
    Yangi lead yaratish
    """
    model = Lead
    template_name = 'crm/lead_form.html'
    fields = ['first_name', 'last_name', 'phone', 'email', 'telegram_username',
              'status', 'source', 'course', 'branch', 'notes', 'expected_start_date']
    allowed_roles = ['admin', 'manager', 'sales_manager', 'sales']
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Lead muvaffaqiyatli yaratildi.')
        return super().form_valid(form)


class LeadUpdateView(TailwindFormMixin, RoleRequiredMixin, UpdateView):
    """
    Leadni tahrirlash
    """
    model = Lead
    template_name = 'crm/lead_form.html'
    fields = ['first_name', 'last_name', 'phone', 'email', 'telegram_username',
              'status', 'source', 'course', 'branch', 'sales', 'notes', 'expected_start_date']
    allowed_roles = ['admin', 'manager', 'sales_manager', 'sales']
    
    def get_queryset(self):
        queryset = Lead.objects.all()
        if self.request.user.is_sales:
            queryset = queryset.filter(sales=self.request.user)
        return queryset
    
    def form_valid(self, form):
        # Status o'zgarganda LeadHistory yaratiladi (signal orqali)
        messages.success(self.request, 'Lead muvaffaqiyatli yangilandi.')
        return super().form_valid(form)


class FollowUpListView(LoginRequiredMixin, ListView):
    """
    Follow-up'lar ro'yxati
    """
    model = FollowUp
    template_name = 'crm/followup_list.html'
    context_object_name = 'followups'
    
    def get_queryset(self):
        queryset = FollowUp.objects.select_related('lead', 'sales')
        
        if self.request.user.is_sales:
            queryset = queryset.filter(sales=self.request.user)
        
        # Bugungi follow-up'lar
        filter_type = self.request.GET.get('filter', 'today')
        today = timezone.now().date()
        
        if filter_type == 'today':
            queryset = queryset.filter(scheduled_at__date=today)
        elif filter_type == 'overdue':
            queryset = queryset.filter(is_overdue=True, is_completed=False)
        elif filter_type == 'upcoming':
            queryset = queryset.filter(scheduled_at__gt=timezone.now(), is_completed=False)
        
        return queryset.order_by('scheduled_at')


class FollowUpCreateView(TailwindFormMixin, RoleRequiredMixin, CreateView):
    """
    Follow-up yaratish
    """
    model = FollowUp
    template_name = 'crm/followup_form.html'
    fields = ['lead', 'title', 'description', 'scheduled_at', 'priority']
    allowed_roles = ['admin', 'manager', 'sales_manager', 'sales']
    
    def form_valid(self, form):
        form.instance.sales = self.request.user
        messages.success(self.request, 'Follow-up muvaffaqiyatli yaratildi.')
        return super().form_valid(form)


class FollowUpUpdateView(TailwindFormMixin, RoleRequiredMixin, UpdateView):
    """
    Follow-up ni tahrirlash yoki bajarilgan deb belgilash
    """
    model = FollowUp
    template_name = 'crm/followup_form.html'
    fields = ['title', 'description', 'scheduled_at', 'priority', 'is_completed']
    allowed_roles = ['admin', 'manager', 'sales_manager', 'sales']
    
    def get_queryset(self):
        queryset = FollowUp.objects.all()
        if self.request.user.is_sales:
            queryset = queryset.filter(sales=self.request.user)
        return queryset
    
    def form_valid(self, form):
        if form.instance.is_completed and not form.instance.completed_at:
            form.instance.completed_at = timezone.now()
        messages.success(self.request, 'Follow-up muvaffaqiyatli yangilandi.')
        return super().form_valid(form)


class TrialLessonCreateView(TailwindFormMixin, RoleRequiredMixin, CreateView):
    """
    Sinov darsiga yozish
    """
    model = TrialLesson
    template_name = 'crm/trial_lesson_form.html'
    fields = ['lead', 'group', 'room', 'date', 'start_time', 'end_time']
    allowed_roles = ['admin', 'manager', 'sales_manager', 'sales']
    
    def form_valid(self, form):
        messages.success(self.request, 'Sinov darsi muvaffaqiyatli yaratildi.')
        return super().form_valid(form)


class TrialLessonUpdateView(TailwindFormMixin, RoleRequiredMixin, UpdateView):
    """
    Sinov darsi natijasini kiritish
    """
    model = TrialLesson
    template_name = 'crm/trial_lesson_form.html'
    fields = ['result', 'notes']
    allowed_roles = ['admin', 'manager', 'sales_manager', 'sales']
    
    def form_valid(self, form):
        messages.success(self.request, 'Sinov darsi natijasi muvaffaqiyatli yangilandi.')
        return super().form_valid(form)


class SalesKPIDetailView(RoleRequiredMixin, DetailView):
    """
    Sotuvchi KPI ko'rish
    """
    model = SalesKPI
    template_name = 'crm/sales_kpi_detail.html'
    context_object_name = 'kpi'
    allowed_roles = ['admin', 'manager', 'sales_manager', 'sales']
    
    def get_object(self):
        if self.request.user.is_sales:
            sales = self.request.user
        else:
            from accounts.models import User
            sales_id = self.kwargs.get('sales_id')
            if sales_id:
                sales = get_object_or_404(User, pk=sales_id)
            else:
                sales = self.request.user
        
        month = self.kwargs.get('month', timezone.now().month)
        year = self.kwargs.get('year', timezone.now().year)
        
        kpi, created = SalesKPI.objects.get_or_create(
            sales=sales,
            month=month,
            year=year
        )
        
        if created:
            from .tasks import calculate_sales_kpi
            calculate_sales_kpi.delay(sales.id, month, year)
        
        return kpi


class SalesKPIRankingView(AdminRequiredMixin, ListView):
    """
    Sotuvchilar KPI reytingi
    """
    model = SalesKPI
    template_name = 'crm/sales_kpi_ranking.html'
    context_object_name = 'kpis'
    
    def get_queryset(self):
        month = self.kwargs.get('month', timezone.now().month)
        year = self.kwargs.get('year', timezone.now().year)
        
        return SalesKPI.objects.filter(
            month=month,
            year=year
        ).select_related('sales').order_by('-total_kpi_score')


class MessageListView(LoginRequiredMixin, ListView):
    """
    Xabarlar ro'yxati
    """
    model = Message
    template_name = 'crm/message_list.html'
    context_object_name = 'messages'
    
    def get_queryset(self):
        queryset = Message.objects.select_related('sender', 'recipient')
        
        if self.request.user.is_sales:
            # Sotuvchi uchun: o'ziga yuborilgan yoki barchaga yuborilgan
            queryset = queryset.filter(
                Q(recipient=self.request.user) | Q(recipient__isnull=True)
            )
        elif self.request.user.is_sales_manager or self.request.user.is_admin or self.request.user.is_manager:
            # Manager/Admin: barcha xabarlar
            pass
        
        return queryset.order_by('-created_at')


class MessageDetailView(LoginRequiredMixin, DetailView):
    """
    Xabar ko'rish
    """
    model = Message
    template_name = 'crm/message_detail.html'
    context_object_name = 'message'
    
    def get_queryset(self):
        queryset = Message.objects.all()
        if self.request.user.is_sales:
            queryset = queryset.filter(
                Q(recipient=self.request.user) | Q(recipient__isnull=True)
            )
        return queryset
    
    def get(self, request, *args, **kwargs):
        message = self.get_object()
        # O'qilgan deb belgilash
        if not message.is_read:
            message.is_read = True
            message.read_at = timezone.now()
            message.save()
        return super().get(request, *args, **kwargs)
