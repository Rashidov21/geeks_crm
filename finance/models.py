from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator
from accounts.models import User, Branch
from courses.models import Course, Group
from crm.models import Lead


class ContractTemplate(models.Model):
    """
    Shartnoma shablonlari
    """
    name = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='contract_templates',
                               null=True, blank=True)  # null = umumiy shablon
    content = models.TextField()  # Shartnoma matni
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Shartnoma shabloni'
        verbose_name_plural = 'Shartnoma shablonlari'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Contract(models.Model):
    """
    Shartnomalar
    """
    STATUS_CHOICES = [
        ('draft', 'Qoralama'),
        ('active', 'Faol'),
        ('suspended', 'To\'xtatilgan'),
        ('completed', 'Yakunlangan'),
        ('cancelled', 'Bekor qilingan'),
    ]
    
    contract_number = models.CharField(max_length=50, unique=True)  # Shartnoma raqami
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contracts',
                               limit_choices_to={'role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='contracts')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='contracts')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True,
                           related_name='contracts')
    
    # Shartnoma ma'lumotlari
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField()
    end_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2,
                                      validators=[MinValueValidator(0)])
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                     validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                        validators=[MinValueValidator(0)])
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                            validators=[MinValueValidator(0)])
    
    # Qo'shimcha ma'lumotlar
    notes = models.TextField(blank=True, null=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='signed_contracts',
                                 limit_choices_to={'role__in': ['admin', 'manager', 'accountant']})
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='created_contracts',
                                  limit_choices_to={'role__in': ['admin', 'manager', 'accountant']})
    
    class Meta:
        verbose_name = 'Shartnoma'
        verbose_name_plural = 'Shartnomalar'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['contract_number']),
        ]
    
    def __str__(self):
        return f"{self.contract_number} - {self.student.username}"
    
    @property
    def remaining_amount(self):
        """Qolgan to'lov miqdori"""
        return self.total_amount - self.paid_amount - self.discount_amount
    
    @property
    def is_paid(self):
        """To'liq to'langanmi?"""
        return self.remaining_amount <= 0
    
    @property
    def payment_percentage(self):
        """To'lov foizi"""
        if self.total_amount == 0:
            return 0
        return (self.paid_amount / self.total_amount) * 100


class PaymentPlan(models.Model):
    """
    To'lov rejasi (shartnoma bo'yicha)
    """
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='payment_plans')
    installment_number = models.IntegerField()  # Oylik to'lov raqami (1, 2, 3...)
    amount = models.DecimalField(max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(0)])
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "To'lov rejasi"
        verbose_name_plural = "To'lov rejalari"
        ordering = ['contract', 'installment_number']
        unique_together = ['contract', 'installment_number']
        indexes = [
            models.Index(fields=['contract', 'due_date']),
            models.Index(fields=['is_paid', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.contract.contract_number} - Oylik {self.installment_number}"
    
    @property
    def is_overdue(self):
        """Muddati o'tganmi?"""
        if self.is_paid:
            return False
        return timezone.now().date() > self.due_date
    
    @property
    def days_overdue(self):
        """Qancha kun o'tgan"""
        if self.is_paid or not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days


class Payment(models.Model):
    """
    To'lovlar
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Naqd pul'),
        ('card', 'Bank kartasi'),
        ('transfer', 'Bank o\'tkazmasi'),
        ('other', 'Boshqa'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('completed', 'Yakunlangan'),
        ('cancelled', 'Bekor qilingan'),
        ('refunded', 'Qaytarilgan'),
    ]
    
    payment_number = models.CharField(max_length=50, unique=True)  # To'lov raqami
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='payments')
    payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(0)])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # To'lov ma'lumotlari
    paid_at = models.DateTimeField(null=True, blank=True)
    receipt_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='created_payments',
                                   limit_choices_to={'role__in': ['admin', 'manager', 'accountant']})
    
    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract', 'paid_at']),
            models.Index(fields=['status', 'paid_at']),
            models.Index(fields=['payment_number']),
        ]
    
    def __str__(self):
        return f"{self.payment_number} - {self.amount} so'm"
    
    def save(self, *args, **kwargs):
        # To'lov yakunlanganda
        if self.status == 'completed' and not self.paid_at:
            self.paid_at = timezone.now()
            
            # Contract paid_amount yangilash
            self.contract.paid_amount += self.amount
            self.contract.save()
            
            # PaymentPlan yangilash
            if self.payment_plan:
                self.payment_plan.is_paid = True
                self.payment_plan.paid_date = timezone.now().date()
                self.payment_plan.save()
        
        super().save(*args, **kwargs)


class PaymentHistory(models.Model):
    """
    To'lovlar tarixi (audit trail)
    """
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=50)  # created, updated, cancelled, refunded
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='payment_history_changes')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "To'lov tarixi"
        verbose_name_plural = "To'lovlar tarixi"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.payment.payment_number} - {self.action}"


class Debt(models.Model):
    """
    Qarzlar
    """
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='debts')
    amount = models.DecimalField(max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(0)])
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Qarz'
        verbose_name_plural = 'Qarzlar'
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['contract', 'due_date']),
            models.Index(fields=['is_paid', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.amount} so'm"
    
    @property
    def is_overdue(self):
        """Muddati o'tganmi?"""
        if self.is_paid:
            return False
        return timezone.now().date() > self.due_date
    
    @property
    def days_overdue(self):
        """Qancha kun o'tgan"""
        if self.is_paid or not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days


class PaymentReminder(models.Model):
    """
    To'lov eslatmalari
    """
    PRIORITY_CHOICES = [
        ('low', 'Past'),
        ('medium', 'O\'rtacha'),
        ('high', 'Yuqori'),
        ('urgent', 'Shoshilinch'),
    ]
    
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='payment_reminders')
    payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='reminders')
    debt = models.ForeignKey(Debt, on_delete=models.CASCADE, null=True, blank=True,
                            related_name='reminders')
    reminder_date = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "To'lov eslatmasi"
        verbose_name_plural = "To'lov eslatmalari"
        ordering = ['reminder_date', 'priority']
        indexes = [
            models.Index(fields=['contract', 'reminder_date']),
            models.Index(fields=['is_sent', 'reminder_date']),
        ]
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.reminder_date}"


class FinancialReport(models.Model):
    """
    Moliya hisobotlari
    """
    REPORT_TYPE_CHOICES = [
        ('daily', 'Kunlik'),
        ('weekly', 'Haftalik'),
        ('monthly', 'Oylik'),
        ('yearly', 'Yillik'),
    ]
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='financial_reports')
    
    # Statistikalar
    total_contracts = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_payments = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_debts = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_discounts = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Qo'shimcha ma'lumotlar
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='created_financial_reports',
                                  limit_choices_to={'role__in': ['admin', 'manager', 'accountant']})
    
    class Meta:
        verbose_name = 'Moliya hisoboti'
        verbose_name_plural = 'Moliya hisobotlari'
        ordering = ['-period_end', '-period_start']
        indexes = [
            models.Index(fields=['report_type', 'period_start', 'period_end']),
            models.Index(fields=['branch', 'period_start']),
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.period_start} to {self.period_end}"
