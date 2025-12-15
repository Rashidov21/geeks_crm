from django.contrib import admin
from .models import ParentDashboard, MonthlyParentReport


@admin.register(ParentDashboard)
class ParentDashboardAdmin(admin.ModelAdmin):
    list_display = ['parent', 'student', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['parent__username', 'student__username']
    ordering = ['-last_updated']
    readonly_fields = ['last_updated']


@admin.register(MonthlyParentReport)
class MonthlyParentReportAdmin(admin.ModelAdmin):
    list_display = ['parent', 'student', 'group', 'year', 'month', 'attendance_percentage',
                   'homework_completion_rate', 'average_exam_score', 'is_sent', 'created_at']
    list_filter = ['is_sent', 'group__course', 'year', 'month', 'created_at']
    search_fields = ['parent__username', 'student__username', 'group__name']
    ordering = ['-year', '-month', '-created_at']
    readonly_fields = [
        'attendance_percentage', 'present_count', 'late_count', 'absent_count', 'total_lessons',
        'total_homeworks', 'completed_homeworks', 'on_time_homeworks', 'late_homeworks',
        'homework_completion_rate', 'total_exams', 'passed_exams', 'average_exam_score',
        'best_exam_score', 'worst_exam_score', 'progress_percentage', 'previous_month_progress',
        'progress_change', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('parent', 'student', 'group', 'month', 'year')
        }),
        ('Davomat statistikasi', {
            'fields': ('attendance_percentage', 'present_count', 'late_count', 'absent_count', 'total_lessons')
        }),
        ('Uy vazifalari statistikasi', {
            'fields': ('total_homeworks', 'completed_homeworks', 'on_time_homeworks', 'late_homeworks', 'homework_completion_rate')
        }),
        ('Imtihon natijalari', {
            'fields': ('total_exams', 'passed_exams', 'average_exam_score', 'best_exam_score', 'worst_exam_score')
        }),
        ('Progress', {
            'fields': ('progress_percentage', 'previous_month_progress', 'progress_change')
        }),
        ('Tahlil', {
            'fields': ('strengths', 'weaknesses', 'mentor_report')
        }),
        ('Holat', {
            'fields': ('is_sent', 'created_at', 'updated_at')
        }),
    )
