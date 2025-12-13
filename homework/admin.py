from django.contrib import admin
from .models import Homework, HomeworkGrade


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'title', 'is_submitted', 'is_late', 'deadline', 'submitted_at']
    list_filter = ['is_submitted', 'is_late', 'lesson__group__course', 'deadline', 'created_at']
    search_fields = ['student__username', 'student__email', 'title', 'description']
    ordering = ['-deadline', '-submitted_at']
    date_hierarchy = 'deadline'
    readonly_fields = ['is_late', 'created_at', 'updated_at']


@admin.register(HomeworkGrade)
class HomeworkGradeAdmin(admin.ModelAdmin):
    list_display = ['homework', 'mentor', 'grade', 'graded_at']
    list_filter = ['mentor', 'graded_at']
    search_fields = ['homework__student__username', 'homework__title', 'comment']
    ordering = ['-graded_at']
