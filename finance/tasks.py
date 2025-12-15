"""
Celery tasks for Finance app
Avtomatik eslatmalar va hisobotlar
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Q, Sum
from datetime import timedelta
from .models import Contract, PaymentPlan, Debt, PaymentReminder, FinancialReport
from telegram_bot.tasks import send_payment_reminder
import logging

logger = logging.getLogger(__name__)


@shared_task
def create_payment_reminders():
    """
    To'lov eslatmalarini avtomatik yaratish
    """
    try:
        now = timezone.now().date()
        
        # 1. PaymentPlan uchun eslatmalar (3 kun, 1 kun, 0 kun oldin)
        payment_plans = PaymentPlan.objects.filter(
            is_paid=False,
            due_date__gte=now,
            due_date__lte=now + timedelta(days=3)
        )
        
        for plan in payment_plans:
            days_before = (plan.due_date - now).days
            
            # 3 kun oldin
            if days_before == 3:
                reminder, created = PaymentReminder.objects.get_or_create(
                    contract=plan.contract,
                    payment_plan=plan,
                    reminder_date=now,
                    defaults={
                        'priority': 'medium',
                        'notes': f"To'lov muddati 3 kun qoldi"
                    }
                )
                if created:
                    send_payment_reminder.delay(reminder.id)
            
            # 1 kun oldin
            elif days_before == 1:
                reminder, created = PaymentReminder.objects.get_or_create(
                    contract=plan.contract,
                    payment_plan=plan,
                    reminder_date=now,
                    defaults={
                        'priority': 'high',
                        'notes': f"To'lov muddati 1 kun qoldi"
                    }
                )
                if created:
                    send_payment_reminder.delay(reminder.id)
            
            # Muddati o'tgan
            elif days_before < 0:
                reminder, created = PaymentReminder.objects.get_or_create(
                    contract=plan.contract,
                    payment_plan=plan,
                    reminder_date=now,
                    defaults={
                        'priority': 'urgent',
                        'notes': f"To'lov muddati o'tgan ({abs(days_before)} kun)"
                    }
                )
                if created:
                    send_payment_reminder.delay(reminder.id)
        
        # 2. Debt uchun eslatmalar
        debts = Debt.objects.filter(
            is_paid=False,
            due_date__lte=now + timedelta(days=3)
        )
        
        for debt in debts:
            days_before = (debt.due_date - now).days
            
            if days_before <= 0:
                priority = 'urgent'
                notes = f"Qarz muddati o'tgan ({abs(days_before)} kun)"
            elif days_before == 1:
                priority = 'high'
                notes = f"Qarz muddati 1 kun qoldi"
            else:
                priority = 'medium'
                notes = f"Qarz muddati {days_before} kun qoldi"
            
            reminder, created = PaymentReminder.objects.get_or_create(
                contract=debt.contract,
                debt=debt,
                reminder_date=now,
                defaults={
                    'priority': priority,
                    'notes': notes
                }
            )
            if created:
                send_payment_reminder.delay(reminder.id)
        
        logger.info(f"Payment reminders created: {payment_plans.count() + debts.count()}")
    
    except Exception as e:
        logger.error(f"Error creating payment reminders: {e}")


@shared_task
def generate_monthly_financial_report(month=None, year=None, branch_id=None):
    """
    Oylik moliya hisoboti yaratish
    """
    try:
        if not month or not year:
            now = timezone.now()
            month = month or now.month
            year = year or now.year
        
        # Oyning boshi va oxiri
        from datetime import datetime
        period_start = datetime(year, month, 1).date()
        if month == 12:
            period_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            period_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        # Hisobot yaratish
        report, created = FinancialReport.objects.get_or_create(
            report_type='monthly',
            period_start=period_start,
            period_end=period_end,
            branch_id=branch_id,
            defaults={
                'created_by_id': 1  # Admin user ID
            }
        )
        
        # Statistikalar
        contracts = Contract.objects.filter(
            created_at__date__gte=period_start,
            created_at__date__lte=period_end
        )
        if branch_id:
            contracts = contracts.filter(course__branch_id=branch_id)
        
        report.total_contracts = contracts.count()
        report.total_revenue = contracts.aggregate(total=Sum('total_amount'))['total'] or 0
        report.total_discounts = contracts.aggregate(total=Sum('discount_amount'))['total'] or 0
        
        # To'lovlar
        payments = Payment.objects.filter(
            paid_at__date__gte=period_start,
            paid_at__date__lte=period_end,
            status='completed'
        )
        if branch_id:
            payments = payments.filter(contract__course__branch_id=branch_id)
        
        report.total_payments = payments.aggregate(total=Sum('amount'))['total'] or 0
        
        # Qarzlar
        debts = Debt.objects.filter(
            due_date__gte=period_start,
            due_date__lte=period_end,
            is_paid=False
        )
        if branch_id:
            debts = debts.filter(contract__course__branch_id=branch_id)
        
        report.total_debts = debts.aggregate(total=Sum('amount'))['total'] or 0
        
        report.save()
        
        logger.info(f"Monthly financial report generated: {month}/{year}")
        return report.id
    
    except Exception as e:
        logger.error(f"Error generating monthly financial report: {e}")


@shared_task
def check_overdue_payments():
    """
    Muddati o'tgan to'lovlarni tekshirish
    """
    try:
        now = timezone.now().date()
        
        # Overdue payment plans
        overdue_plans = PaymentPlan.objects.filter(
            is_paid=False,
            due_date__lt=now
        )
        
        # Overdue debts
        overdue_debts = Debt.objects.filter(
            is_paid=False,
            due_date__lt=now
        )
        
        logger.info(f"Overdue payments: {overdue_plans.count()} plans, {overdue_debts.count()} debts")
        
        # Eslatmalar yuborish (har kuni)
        for plan in overdue_plans:
            reminder, created = PaymentReminder.objects.get_or_create(
                contract=plan.contract,
                payment_plan=plan,
                reminder_date=now,
                defaults={
                    'priority': 'urgent',
                    'notes': f"To'lov muddati o'tgan ({plan.days_overdue} kun)"
                }
            )
            if created:
                send_payment_reminder.delay(reminder.id)
        
        for debt in overdue_debts:
            reminder, created = PaymentReminder.objects.get_or_create(
                contract=debt.contract,
                debt=debt,
                reminder_date=now,
                defaults={
                    'priority': 'urgent',
                    'notes': f"Qarz muddati o'tgan ({debt.days_overdue} kun)"
                }
            )
            if created:
                send_payment_reminder.delay(reminder.id)
    
    except Exception as e:
        logger.error(f"Error checking overdue payments: {e}")

