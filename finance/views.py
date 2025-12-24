from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Count, Q
from .models import (
    Contract, Payment, PaymentPlan, Debt, PaymentReminder, FinancialReport
)
from accounts.mixins import RoleRequiredMixin, AdminRequiredMixin, TailwindFormMixin


class ContractListView(RoleRequiredMixin, ListView):
    """
    Shartnomalar ro'yxati
    """
    model = Contract
    template_name = 'finance/contract_list.html'
    context_object_name = 'contracts'
    allowed_roles = ['admin', 'manager', 'accountant']
    paginate_by = 30
    
    def get_queryset(self):
        from courses.models import Course, Group
        queryset = Contract.objects.select_related('student', 'course', 'group')
        
        # Filtrlash
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        course_id = self.request.GET.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        group_id = self.request.GET.get('group')
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        
        # Sana oralig'i
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        from courses.models import Course, Group
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.filter(is_active=True)
        context['groups'] = Group.objects.filter(is_active=True)
        context['total_contracts'] = self.get_queryset().count()
        context['total_amount'] = self.get_queryset().aggregate(total=Sum('total_amount'))['total'] or 0
        # Permissions
        user = self.request.user
        context['can_create'] = user.is_superuser or (hasattr(user, 'is_admin') and user.is_admin) or (hasattr(user, 'is_manager') and user.is_manager)
        context['can_edit'] = context['can_create']
        context['can_delete'] = False  # Contracts usually shouldn't be deleted
        return context


class ContractDetailView(RoleRequiredMixin, DetailView):
    """
    Shartnoma batafsil ma'lumotlari
    """
    model = Contract
    template_name = 'finance/contract_detail.html'
    context_object_name = 'contract'
    allowed_roles = ['admin', 'manager', 'accountant']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract = self.object
        
        # To'lov rejalari
        context['payment_plans'] = PaymentPlan.objects.filter(
            contract=contract
        ).order_by('installment_number')
        
        # To'lovlar
        context['payments'] = Payment.objects.filter(
            contract=contract
        ).order_by('-paid_at')
        
        # Qarzlar
        context['debts'] = Debt.objects.filter(
            contract=contract,
            is_paid=False
        ).order_by('due_date')
        
        # Eslatmalar
        context['reminders'] = PaymentReminder.objects.filter(
            contract=contract,
            is_sent=False
        ).order_by('reminder_date')
        
        return context


class ContractCreateView(TailwindFormMixin, RoleRequiredMixin, CreateView):
    """
    Yangi shartnoma yaratish
    """
    model = Contract
    template_name = 'finance/contract_form.html'
    fields = ['student', 'course', 'group', 'lead', 'start_date', 'end_date',
              'total_amount', 'discount_amount', 'discount_percentage', 'notes']
    allowed_roles = ['admin', 'manager', 'accountant']
    
    def form_valid(self, form):
        # Shartnoma raqamini yaratish
        from datetime import datetime
        contract_number = f"CNT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        form.instance.contract_number = contract_number
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Shartnoma muvaffaqiyatli yaratildi.')
        return super().form_valid(form)


class PaymentListView(RoleRequiredMixin, ListView):
    paginate_by = 30
    """
    To'lovlar ro'yxati
    """
    model = Payment
    template_name = 'finance/payment_list.html'
    context_object_name = 'payments'
    allowed_roles = ['admin', 'manager', 'accountant']
    
    def get_queryset(self):
        queryset = Payment.objects.select_related('contract', 'contract__student')
        
        # Filtrlash
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        payment_method = self.request.GET.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        # Sana oralig'i
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(paid_at__date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(paid_at__date__lte=date_to)
        
        # Summa oralig'i
        amount_min = self.request.GET.get('amount_min')
        if amount_min:
            queryset = queryset.filter(amount__gte=amount_min)
        
        amount_max = self.request.GET.get('amount_max')
        if amount_max:
            queryset = queryset.filter(amount__lte=amount_max)
        
        return queryset.order_by('-paid_at', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_amount'] = self.get_queryset().aggregate(total=Sum('amount'))['total'] or 0
        context['total_count'] = self.get_queryset().count()
        # Permissions
        user = self.request.user
        context['can_create'] = user.is_superuser or (hasattr(user, 'is_admin') and user.is_admin) or (hasattr(user, 'is_manager') and user.is_manager)
        context['can_edit'] = context['can_create']
        context['can_delete'] = False  # Payments usually shouldn't be deleted
        return context


class PaymentCreateView(TailwindFormMixin, RoleRequiredMixin, CreateView):
    """
    To'lov yaratish
    """
    model = Payment
    template_name = 'finance/payment_form.html'
    fields = ['contract', 'payment_plan', 'amount', 'payment_method', 'receipt_number', 'notes']
    allowed_roles = ['admin', 'manager', 'accountant']
    
    def form_valid(self, form):
        # To'lov raqamini yaratish
        from datetime import datetime
        payment_number = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        form.instance.payment_number = payment_number
        form.instance.status = 'completed'
        form.instance.created_by = self.request.user
        
        messages.success(self.request, 'To\'lov muvaffaqiyatli yaratildi.')
        return super().form_valid(form)


class DebtListView(RoleRequiredMixin, ListView):
    """
    Qarzlar ro'yxati
    """
    model = Debt
    template_name = 'finance/debt_list.html'
    context_object_name = 'debts'
    allowed_roles = ['admin', 'manager', 'accountant']
    
    def get_queryset(self):
        queryset = Debt.objects.select_related('contract', 'contract__student')
        
        # Faqat to'lanmagan qarzlar
        show_all = self.request.GET.get('show_all')
        if not show_all:
            queryset = queryset.filter(is_paid=False)
        
        # Overdue qarzlar
        overdue = self.request.GET.get('overdue')
        if overdue:
            today = timezone.now().date()
            queryset = queryset.filter(due_date__lt=today, is_paid=False)
        
        # Qarz miqdori
        amount_min = self.request.GET.get('amount_min')
        if amount_min:
            queryset = queryset.filter(amount__gte=amount_min)
        
        amount_max = self.request.GET.get('amount_max')
        if amount_max:
            queryset = queryset.filter(amount__lte=amount_max)
        
        return queryset.order_by('due_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        context['total_debt'] = self.get_queryset().aggregate(total=Sum('amount'))['total'] or 0
        context['overdue_count'] = self.get_queryset().filter(due_date__lt=today, is_paid=False).count()
        context['overdue_amount'] = self.get_queryset().filter(due_date__lt=today, is_paid=False).aggregate(total=Sum('amount'))['total'] or 0
        return context


class FinancialReportListView(AdminRequiredMixin, ListView):
    """
    Moliya hisobotlari ro'yxati
    """
    model = FinancialReport
    template_name = 'finance/financial_report_list.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        return FinancialReport.objects.select_related('branch').order_by('-period_end', '-period_start')


class FinancialReportDetailView(AdminRequiredMixin, DetailView):
    """
    Moliya hisoboti batafsil ma'lumotlari
    """
    model = FinancialReport
    template_name = 'finance/financial_report_detail.html'
    context_object_name = 'report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.object
        
        # Shartnomalar
        contracts = Contract.objects.filter(
            created_at__gte=report.period_start,
            created_at__lte=report.period_end
        )
        if report.branch:
            contracts = contracts.filter(course__branch=report.branch)
        
        context['contracts'] = contracts
        
        # To'lovlar
        payments = Payment.objects.filter(
            paid_at__gte=report.period_start,
            paid_at__lte=report.period_end,
            status='completed'
        )
        if report.branch:
            payments = payments.filter(contract__course__branch=report.branch)
        
        context['payments'] = payments
        
        return context


class DashboardView(RoleRequiredMixin, TemplateView):
    """
    Moliya dashboard
    """
    template_name = 'finance/dashboard.html'
    allowed_roles = ['admin', 'manager', 'accountant']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Umumiy statistika
        context['total_contracts'] = Contract.objects.count()
        context['active_contracts'] = Contract.objects.filter(status='active').count()
        context['total_revenue'] = Contract.objects.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        context['total_paid'] = Contract.objects.aggregate(
            total=Sum('paid_amount')
        )['total'] or 0
        
        # Bu oy
        context['contracts_this_month'] = Contract.objects.filter(
            created_at__gte=this_month_start
        ).count()
        context['revenue_this_month'] = Contract.objects.filter(
            created_at__gte=this_month_start
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        context['payments_this_month'] = Payment.objects.filter(
            paid_at__gte=this_month_start,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Qarzlar
        context['total_debts'] = Debt.objects.filter(is_paid=False).aggregate(
            total=Sum('amount')
        )['total'] or 0
        context['overdue_debts'] = Debt.objects.filter(
            is_paid=False,
            due_date__lt=now.date()
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Eslatmalar
        context['pending_reminders'] = PaymentReminder.objects.filter(
            is_sent=False,
            reminder_date__lte=now.date()
        ).count()
        
        # Oylik statistika (chart uchun)
        from datetime import timedelta
        monthly_data = []
        for i in range(6):
            month_start = (now - timedelta(days=30*i)).replace(day=1)
            if i < 5:
                month_end = (now - timedelta(days=30*(i-1))).replace(day=1) - timedelta(days=1)
            else:
                month_end = now
            
            payments_sum = Payment.objects.filter(
                paid_at__gte=month_start,
                paid_at__lte=month_end,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_data.append({
                'month': month_start.strftime('%b'),
                'amount': payments_sum
            })
        
        context['monthly_data'] = list(reversed(monthly_data))
        
        # Template uchun to'g'ri nomlar
        context['monthly_income'] = context['payments_this_month']
        context['total_debt'] = context['total_debts']
        context['contracts_count'] = context['total_contracts']
        context['pending_payments'] = PaymentPlan.objects.filter(
            is_paid=False,
            due_date__gte=now.date()
        ).count()
        
        # So'nggi to'lovlar
        context['recent_payments'] = Payment.objects.select_related(
            'contract', 'contract__student'
        ).order_by('-paid_at')[:10]
        
        return context


class ReportsView(RoleRequiredMixin, TemplateView):
    """
    Moliya hisobotlari
    """
    template_name = 'finance/reports.html'
    allowed_roles = ['admin', 'manager', 'accountant']
    
    def get_context_data(self, **kwargs):
        from datetime import timedelta
        from courses.models import Course
        
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        
        # Kurslar bo'yicha daromad
        courses_data = []
        for course in Course.objects.filter(is_active=True):
            revenue = Contract.objects.filter(course=course).aggregate(total=Sum('total_amount'))['total'] or 0
            paid = Contract.objects.filter(course=course).aggregate(total=Sum('paid_amount'))['total'] or 0
            courses_data.append({
                'name': course.name,
                'revenue': revenue,
                'paid': paid,
                'contracts': Contract.objects.filter(course=course).count()
            })
        context['courses_data'] = courses_data
        
        # Oylik trend
        monthly_trend = []
        for i in range(12):
            month_start = (now - timedelta(days=30*i)).replace(day=1)
            payments_sum = Payment.objects.filter(
                paid_at__year=month_start.year,
                paid_at__month=month_start.month,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            contracts_sum = Contract.objects.filter(
                created_at__year=month_start.year,
                created_at__month=month_start.month
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            monthly_trend.append({
                'month': month_start.strftime('%Y-%m'),
                'payments': payments_sum,
                'contracts': contracts_sum
            })
        
        context['monthly_trend'] = list(reversed(monthly_trend))
        
        return context
