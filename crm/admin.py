from django.contrib import admin
from .models import (
    LeadStatus, Lead, LeadHistory, FollowUp, TrialLesson,
    SalesProfile, WorkSchedule, Leave, SalesKPI, Message
)


@admin.register(LeadStatus)
class LeadStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'order', 'color', 'is_active']
    list_filter = ['is_active']
    ordering = ['order']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'status', 'sales', 'course', 'branch', 'trial_date', 'created_at']
    list_filter = ['status', 'source', 'course', 'branch', 'sales', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone', 'email', 'telegram_username']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'assigned_at']
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('first_name', 'last_name', 'phone', 'email', 'telegram_username')
        }),
        ('Lead ma\'lumotlari', {
            'fields': ('status', 'source', 'course', 'branch', 'notes', 'expected_start_date')
        }),
        ('Sotuvchi', {
            'fields': ('sales', 'assigned_at')
        }),
        ('Sinov darsi', {
            'fields': ('trial_group', 'trial_room', 'trial_date', 'trial_time', 'trial_result')
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at', 'created_by')
        }),
    )


@admin.register(LeadHistory)
class LeadHistoryAdmin(admin.ModelAdmin):
    list_display = ['lead', 'old_status', 'new_status', 'changed_by', 'created_at']
    list_filter = ['old_status', 'new_status', 'created_at']
    search_fields = ['lead__first_name', 'lead__last_name', 'lead__phone']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ['lead', 'sales', 'title', 'scheduled_at', 'is_completed', 'is_overdue', 'priority']
    list_filter = ['is_completed', 'is_overdue', 'priority', 'sales', 'scheduled_at']
    search_fields = ['lead__first_name', 'lead__last_name', 'title', 'description']
    ordering = ['scheduled_at']
    readonly_fields = ['is_overdue', 'created_at', 'updated_at']


@admin.register(TrialLesson)
class TrialLessonAdmin(admin.ModelAdmin):
    list_display = ['lead', 'group', 'room', 'date', 'start_time', 'result', 'created_at']
    list_filter = ['result', 'group__course', 'date', 'created_at']
    search_fields = ['lead__first_name', 'lead__last_name', 'group__name']
    ordering = ['-date', '-start_time']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SalesProfile)
class SalesProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'branch', 'is_active', 'max_leads_per_day', 'created_at']
    list_filter = ['branch', 'is_active', 'created_at']
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
