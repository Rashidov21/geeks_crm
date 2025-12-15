from django.contrib import admin
from .models import (
    ContractTemplate, Contract, PaymentPlan, Payment, PaymentHistory,
    Debt, PaymentReminder, FinancialReport
)


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'is_active', 'created_at']
    list_filter = ['course', 'is_active', 'created_at']
    search_fields = ['name', 'content']
    ordering = ['name']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['contract_number', 'student', 'course', 'status', 'total_amount', 
                   'paid_amount', 'remaining_amount', 'start_date', 'created_at']
    list_filter = ['status', 'course', 'start_date', 'created_at']
    search_fields = ['contract_number', 'student__username', 'student__email']
    ordering = ['-created_at']
    readonly_fields = ['paid_amount', 'remaining_amount', 'payment_percentage', 'is_paid',
                      'created_at', 'updated_at']
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('contract_number', 'student', 'course', 'group', 'lead', 'status')
        }),
        ('Shartnoma ma\'lumotlari', {
            'fields': ('start_date', 'end_date', 'total_amount', 'discount_amount', 
                      'discount_percentage', 'paid_amount', 'remaining_amount', 
                      'payment_percentage', 'is_paid')
        }),
        ('Qo\'shimcha', {
            'fields': ('notes', 'signed_at', 'signed_by', 'created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ['contract', 'installment_number', 'amount', 'due_date', 'is_paid', 
                   'paid_date', 'is_overdue']
    list_filter = ['is_paid', 'due_date', 'contract__status']
    search_fields = ['contract__contract_number', 'contract__student__username']
    ordering = ['contract', 'installment_number']
    readonly_fields = ['is_overdue', 'days_overdue', 'created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'contract', 'amount', 'payment_method', 'status', 
                   'paid_at', 'created_at']
    list_filter = ['status', 'payment_method', 'paid_at', 'created_at']
    search_fields = ['payment_number', 'receipt_number', 'contract__contract_number']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('payment_number', 'contract', 'payment_plan', 'amount', 
                      'payment_method', 'status')
        }),
        ('To\'lov ma\'lumotlari', {
            'fields': ('paid_at', 'receipt_number', 'notes', 'created_by', 
                      'created_at', 'updated_at')
        }),
    )


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['payment', 'action', 'changed_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['payment__payment_number', 'notes']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ['contract', 'amount', 'due_date', 'is_paid', 'paid_at', 'is_overdue']
    list_filter = ['is_paid', 'due_date', 'created_at']
    search_fields = ['contract__contract_number', 'contract__student__username']
    ordering = ['due_date']
    readonly_fields = ['is_overdue', 'days_overdue', 'created_at', 'updated_at']


@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    list_display = ['contract', 'reminder_date', 'priority', 'is_sent', 'sent_at']
    list_filter = ['priority', 'is_sent', 'reminder_date']
    search_fields = ['contract__contract_number', 'notes']
    ordering = ['reminder_date', 'priority']
    readonly_fields = ['sent_at', 'created_at', 'updated_at']


@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'period_start', 'period_end', 'branch', 
                   'total_revenue', 'total_payments', 'created_at']
    list_filter = ['report_type', 'branch', 'period_start', 'created_at']
    search_fields = ['notes']
    ordering = ['-period_end', '-period_start']
    readonly_fields = ['created_at', 'updated_at']
