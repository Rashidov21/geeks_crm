from django.contrib import admin
from .models import (
    LessonQuality, ParentFeedback, MonthlyReport,
    MentorKPI, MentorRanking
)


@admin.register(LessonQuality)
class LessonQualityAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'student', 'rating', 'created_at']
    list_filter = ['rating', 'lesson__group__course', 'created_at']
    search_fields = ['student__username', 'lesson__group__name', 'comment']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(ParentFeedback)
class ParentFeedbackAdmin(admin.ModelAdmin):
    list_display = ['mentor', 'parent', 'student', 'feedback_type', 'created_at']
    list_filter = ['feedback_type', 'mentor', 'created_at']
    search_fields = ['mentor__username', 'parent__username', 'student__username', 'comment']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = ['mentor', 'student', 'group', 'year', 'month', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'group__course', 'year', 'month', 'created_at']
    search_fields = ['mentor__username', 'student__username', 'group__name']
    ordering = ['-year', '-month', '-created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('mentor', 'student', 'group', 'month', 'year')
        }),
        ('Hisobot maydonlari', {
            'fields': ('character', 'attendance', 'mastery', 'progress_change', 'additional_notes')
        }),
        ('Holat', {
            'fields': ('is_completed', 'created_at', 'updated_at')
        }),
    )


@admin.register(MentorKPI)
class MentorKPIAdmin(admin.ModelAdmin):
    list_display = ['mentor', 'year', 'month', 'total_kpi_score', 'total_lessons', 'total_students', 'updated_at']
    list_filter = ['year', 'month', 'updated_at']
    search_fields = ['mentor__username', 'mentor__email']
    ordering = ['-year', '-month', '-total_kpi_score']
    readonly_fields = [
        'lesson_quality_score', 'attendance_entry_score', 'homework_grading_score',
        'student_progress_score', 'group_rating_score', 'parent_feedback_score',
        'monthly_report_score', 'total_kpi_score', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('mentor', 'month', 'year')
        }),
        ('KPI mezonlari', {
            'fields': (
                'lesson_quality_score', 'attendance_entry_score', 'homework_grading_score',
                'student_progress_score', 'group_rating_score', 'parent_feedback_score',
                'monthly_report_score'
            )
        }),
        ('Umumiy natija', {
            'fields': ('total_kpi_score',)
        }),
        ('Statistika', {
            'fields': ('total_lessons', 'total_students', 'completed_reports', 'total_reports')
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(MentorRanking)
class MentorRankingAdmin(admin.ModelAdmin):
    list_display = ['mentor', 'year', 'month', 'rank', 'total_kpi_score', 'updated_at']
    list_filter = ['year', 'month', 'updated_at']
    search_fields = ['mentor__username', 'mentor__email']
    ordering = ['-year', '-month', 'rank']
    readonly_fields = ['rank', 'total_kpi_score', 'updated_at']
