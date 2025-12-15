from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Count, Q
from .models import (
    Contract, Payment, PaymentPlan, Debt, PaymentReminder, FinancialReport
)
from accounts.mixins import RoleRequiredMixin, AdminRequiredMixin


class ContractListView(RoleRequiredMixin, ListView):
    """
    Shartnomalar ro'yxati
    """
    model = Contract
    template_name = 'finance/contract_list.html'
    context_object_name = 'contracts'
    allowed_roles = ['admin', 'manager', 'accountant']
    
    def get_queryset(self):
        queryset = Contract.objects.select_related('student', 'course', 'group')
        
        # Filtrlash
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        student_id = self.request.GET.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset.order_by('-created_at')


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


class ContractCreateView(RoleRequiredMixin, CreateView):
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
        
        contract_id = self.request.GET.get('contract')
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        
        return queryset.order_by('-paid_at', '-created_at')


class PaymentCreateView(RoleRequiredMixin, CreateView):
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
        
        return queryset.order_by('due_date')


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


class DashboardView(RoleRequiredMixin, ListView):
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
        
        return context
