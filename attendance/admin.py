from django.contrib import admin
from .models import Attendance, AttendanceStatistics


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'status', 'created_at']
    list_filter = ['status', 'lesson__group__course', 'lesson__date', 'created_at']
    search_fields = ['student__username', 'student__email', 'lesson__group__name']
    ordering = ['-lesson__date', '-lesson__start_time']
    date_hierarchy = 'lesson__date'


@admin.register(AttendanceStatistics)
class AttendanceStatisticsAdmin(admin.ModelAdmin):
    list_display = ['student', 'group', 'total_lessons', 'present_count', 'late_count', 
                   'absent_count', 'attendance_percentage', 'updated_at']
    list_filter = ['group__course', 'updated_at']
    search_fields = ['student__username', 'student__email', 'group__name']
    ordering = ['-attendance_percentage']
    readonly_fields = ['total_lessons', 'present_count', 'late_count', 'absent_count', 
                      'attendance_percentage', 'updated_at']
