from django.contrib import admin
from .models import (
    PointTransaction, StudentPoints, Badge, StudentBadge,
    GroupRanking, BranchRanking, OverallRanking, MonthlyRanking
)


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ['student', 'points', 'point_type', 'description', 'created_at']
    list_filter = ['point_type', 'created_at']
    search_fields = ['student__username', 'student__email', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(StudentPoints)
class StudentPointsAdmin(admin.ModelAdmin):
    list_display = ['student', 'group', 'total_points', 'updated_at']
    list_filter = ['group__course', 'updated_at']
    search_fields = ['student__username', 'student__email', 'group__name']
    ordering = ['-total_points']
    readonly_fields = ['total_points', 'updated_at']


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'badge_type', 'icon', 'points_required', 'is_active', 'created_at']
    list_filter = ['badge_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['points_required']


@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ['student', 'badge', 'group', 'earned_at']
    list_filter = ['badge', 'group__course', 'earned_at']
    search_fields = ['student__username', 'student__email', 'badge__name']
    ordering = ['-earned_at']


@admin.register(GroupRanking)
class GroupRankingAdmin(admin.ModelAdmin):
    list_display = ['group', 'student', 'rank', 'total_points', 'updated_at']
    list_filter = ['group__course', 'updated_at']
    search_fields = ['student__username', 'group__name']
    ordering = ['group', 'rank']
    readonly_fields = ['rank', 'total_points', 'updated_at']


@admin.register(BranchRanking)
class BranchRankingAdmin(admin.ModelAdmin):
    list_display = ['branch', 'student', 'rank', 'total_points', 'updated_at']
    list_filter = ['branch', 'updated_at']
    search_fields = ['student__username', 'branch__name']
    ordering = ['branch', 'rank']
    readonly_fields = ['rank', 'total_points', 'updated_at']


@admin.register(OverallRanking)
class OverallRankingAdmin(admin.ModelAdmin):
    list_display = ['student', 'rank', 'total_points', 'updated_at']
    search_fields = ['student__username', 'student__email']
    ordering = ['rank']
    readonly_fields = ['rank', 'total_points', 'updated_at']


@admin.register(MonthlyRanking)
class MonthlyRankingAdmin(admin.ModelAdmin):
    list_display = ['student', 'ranking_type', 'year', 'month', 'rank', 'total_points', 'created_at']
    list_filter = ['ranking_type', 'year', 'month', 'created_at']
    search_fields = ['student__username', 'student__email']
    ordering = ['year', 'month', 'ranking_type', 'rank']
    readonly_fields = ['created_at']
