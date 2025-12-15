from django.contrib import admin
from .models import Course, Module, Topic, TopicMaterial, Room, Group, GroupTransfer, Lesson, StudentProgress


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch', 'duration_weeks', 'price', 'is_active', 'created_at']
    list_filter = ['branch', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


class TopicMaterialInline(admin.TabularInline):
    model = TopicMaterial
    extra = 1


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'order', 'created_at']
    list_filter = ['course', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['course', 'order']


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'module', 'order', 'created_at']
    list_filter = ['module__course', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['module', 'order']
    inlines = [TopicMaterialInline]


@admin.register(TopicMaterial)
class TopicMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'topic', 'material_type', 'order', 'created_at']
    list_filter = ['material_type', 'created_at']
    search_fields = ['title', 'content']
    ordering = ['topic', 'order']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch', 'capacity', 'is_active', 'created_at']
    list_filter = ['branch', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['branch', 'name']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'mentor', 'room', 'schedule_type', 'start_time', 'capacity', 'is_active']
    list_filter = ['course', 'mentor', 'schedule_type', 'is_active', 'created_at']
    search_fields = ['name']
    ordering = ['course', 'name']
    filter_horizontal = ['students']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['group', 'topic', 'date', 'start_time', 'created_at']
    list_filter = ['group__course', 'date', 'created_at']
    search_fields = ['title', 'description', 'group__name']
    ordering = ['-date', '-start_time']
    date_hierarchy = 'date'


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'progress_percentage', 'updated_at']
    list_filter = ['course', 'updated_at']
    search_fields = ['student__username', 'student__email', 'course__name']
    ordering = ['-updated_at']
    readonly_fields = ['progress_percentage']


@admin.register(GroupTransfer)
class GroupTransferAdmin(admin.ModelAdmin):
    list_display = ['student', 'from_group', 'to_group', 'transferred_by', 'transferred_at']
    list_filter = ['from_group__course', 'to_group__course', 'transferred_at']
    search_fields = ['student__username', 'student__email', 'reason', 'notes']
    ordering = ['-transferred_at']
    readonly_fields = ['transferred_at']
    fieldsets = (
        ('O\'quvchi va guruhlar', {
            'fields': ('student', 'from_group', 'to_group')
        }),
        ('Ma\'lumotlar', {
            'fields': ('reason', 'notes', 'transferred_by', 'transferred_at')
        }),
    )
