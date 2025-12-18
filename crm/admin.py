from django.contrib import admin
from .models import (
    LeadStatus, Lead, LeadHistory, FollowUp, TrialLesson,
    SalesProfile, WorkSchedule, Leave, SalesKPI, DailyKPI,
    SalesMessage, SalesMessageRead, Offer, Reactivation, Message
)


@admin.register(LeadStatus)
class LeadStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'order', 'color', 'is_active']
    list_filter = ['is_active']
    ordering = ['order']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'status', 'assigned_sales', 'interested_course', 'branch', 'trial_date', 'created_at']
    list_filter = ['status', 'source', 'interested_course', 'branch', 'assigned_sales', 'created_at']
    search_fields = ['name', 'phone', 'secondary_phone']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'assigned_at', 'lost_at', 'enrolled_at']
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'phone', 'secondary_phone')
        }),
        ('Lead ma\'lumotlari', {
            'fields': ('status', 'source', 'interested_course', 'branch', 'notes')
        }),
        ('Sotuvchi', {
            'fields': ('assigned_sales', 'assigned_at')
        }),
        ('Sinov darsi', {
            'fields': ('trial_group', 'trial_room', 'trial_date', 'trial_time', 'trial_result')
        }),
        ('Yozilish', {
            'fields': ('enrolled_at', 'enrolled_group', 'lost_at')
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at', 'created_by')
        }),
    )


@admin.register(LeadHistory)
class LeadHistoryAdmin(admin.ModelAdmin):
    list_display = ['lead', 'old_status', 'new_status', 'changed_by', 'created_at']
    list_filter = ['old_status', 'new_status', 'created_at']
    search_fields = ['lead__name', 'lead__phone']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ['lead', 'sales', 'due_date', 'completed', 'is_overdue', 'followup_sequence']
    list_filter = ['completed', 'is_overdue', 'sales', 'due_date']
    search_fields = ['lead__name', 'notes']
    ordering = ['due_date']
    readonly_fields = ['is_overdue', 'created_at', 'updated_at']


@admin.register(TrialLesson)
class TrialLessonAdmin(admin.ModelAdmin):
    list_display = ['lead', 'group', 'room', 'date', 'time', 'result', 'created_at']
    list_filter = ['result', 'group__course', 'date', 'created_at']
    search_fields = ['lead__name', 'group__name']
    ordering = ['-date', '-time']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SalesProfile)
class SalesProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'branch', 'is_active_sales', 'is_on_leave', 'is_absent', 'max_leads_per_day', 'created_at']
    list_filter = ['branch', 'is_active_sales', 'is_on_leave', 'is_absent', 'created_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['-created_at']


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ['sales', 'weekday', 'start_time', 'end_time', 'is_active']
    list_filter = ['weekday', 'is_active', 'sales']
    ordering = ['sales', 'weekday']


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ['sales', 'start_date', 'end_date', 'status', 'approved_by', 'created_at']
    list_filter = ['status', 'start_date', 'created_at']
    search_fields = ['sales__username', 'reason']
    ordering = ['-created_at']
    readonly_fields = ['approved_at', 'created_at', 'updated_at']


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'offer_type', 'priority', 'valid_from', 'valid_until', 'is_active', 'created_at']
    list_filter = ['offer_type', 'priority', 'is_active', 'channel', 'audience']
    search_fields = ['title', 'description']
    ordering = ['-created_at']


@admin.register(Reactivation)
class ReactivationAdmin(admin.ModelAdmin):
    list_display = ['lead', 'reactivation_type', 'days_since_lost', 'result', 'sent_at']
    list_filter = ['reactivation_type', 'result', 'sent_at']
    search_fields = ['lead__name', 'lead__phone']
    ordering = ['-sent_at']


@admin.register(SalesMessage)
class SalesMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'subject', 'priority', 'telegram_sent', 'created_at']
    list_filter = ['priority', 'telegram_sent', 'created_at']
    search_fields = ['subject', 'message', 'sender__username']
    ordering = ['-created_at']


@admin.register(SalesMessageRead)
class SalesMessageReadAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'read_at']
    list_filter = ['read_at']
    ordering = ['-read_at']


@admin.register(DailyKPI)
class DailyKPIAdmin(admin.ModelAdmin):
    list_display = ['sales', 'date', 'daily_contacts', 'daily_followups', 'followup_completion_rate', 'conversion_rate']
    list_filter = ['date', 'sales']
    ordering = ['-date']


@admin.register(SalesKPI)
class SalesKPIAdmin(admin.ModelAdmin):
    list_display = ['sales', 'year', 'month', 'total_kpi_score', 'total_contacts', 'conversion_rate', 'updated_at']
    list_filter = ['year', 'month', 'updated_at']
    search_fields = ['sales__username', 'sales__email']
    ordering = ['-year', '-month', '-total_kpi_score']
    readonly_fields = ['total_kpi_score', 'created_at', 'updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'title', 'priority', 'is_read', 'created_at']
    list_filter = ['priority', 'is_read', 'created_at']
    search_fields = ['title', 'content', 'sender__username', 'recipient__username']
    ordering = ['-created_at']
    readonly_fields = ['read_at', 'created_at']
