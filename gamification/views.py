from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F
from .models import (
    StudentPoints, StudentBadge, GroupRanking, BranchRanking,
    OverallRanking, MonthlyRanking, PointTransaction
)
from accounts.mixins import RoleRequiredMixin


class StudentPointsView(LoginRequiredMixin, DetailView):
    """
    O'quvchi ballari (guruh bo'yicha)
    """
    model = StudentPoints
    template_name = 'gamification/student_points.html'
    context_object_name = 'student_points'
    
    def get_object(self):
        student = self.request.user if self.request.user.is_student else self.kwargs.get('student_id')
        group_id = self.kwargs.get('group_id')
        from courses.models import Group
        group = Group.objects.get(pk=group_id)
        
        student_points, created = StudentPoints.objects.get_or_create(
            student=student,
            group=group
        )
        if created:
            student_points.calculate_total_points()
        return student_points


class StudentBadgesView(LoginRequiredMixin, ListView):
    """
    O'quvchi badge'lari
    """
    model = StudentBadge
    template_name = 'gamification/student_badges.html'
    context_object_name = 'badges'
    
    def get_queryset(self):
        student = self.request.user if self.request.user.is_student else self.kwargs.get('student_id')
        return StudentBadge.objects.filter(student=student).select_related('badge', 'group')


class GroupRankingView(LoginRequiredMixin, ListView):
    """
    Guruh bo'yicha reyting
    """
    model = GroupRanking
    template_name = 'gamification/group_ranking.html'
    context_object_name = 'rankings'
    
    def get_queryset(self):
        from courses.models import Group
        group = Group.objects.get(pk=self.kwargs['group_id'])
        return GroupRanking.objects.filter(group=group).select_related('student').order_by('rank')


class BranchRankingView(LoginRequiredMixin, ListView):
    """
    Filial bo'yicha reyting
    """
    model = BranchRanking
    template_name = 'gamification/branch_ranking.html'
    context_object_name = 'rankings'
    
    def get_queryset(self):
        from accounts.models import Branch
        branch = Branch.objects.get(pk=self.kwargs['branch_id'])
        return BranchRanking.objects.filter(branch=branch).select_related('student').order_by('rank')


class OverallRankingView(LoginRequiredMixin, ListView):
    """
    Markaz bo'yicha umumiy reyting
    """
    model = OverallRanking
    template_name = 'gamification/overall_ranking.html'
    context_object_name = 'rankings'
    
    def get_queryset(self):
        return OverallRanking.objects.select_related('student').order_by('rank')[:100]  # Top 100


class MonthlyRankingView(LoginRequiredMixin, ListView):
    """
    Oylik reyting (Top-10, Top-25, Top-50, Top-100)
    """
    model = MonthlyRanking
    template_name = 'gamification/monthly_ranking.html'
    context_object_name = 'rankings'
    
    def get_queryset(self):
        ranking_type = self.kwargs.get('ranking_type', 'top_10')
        month = self.kwargs.get('month', timezone.now().month)
        year = self.kwargs.get('year', timezone.now().year)
        
        limit = {
            'top_10': 10,
            'top_25': 25,
            'top_50': 50,
            'top_100': 100,
        }.get(ranking_type, 10)
        
        return MonthlyRanking.objects.filter(
            ranking_type=ranking_type,
            month=month,
            year=year
        ).select_related('student').order_by('rank')[:limit]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ranking_type'] = self.kwargs.get('ranking_type', 'top_10')
        context['month'] = self.kwargs.get('month', timezone.now().month)
        context['year'] = self.kwargs.get('year', timezone.now().year)
        return context


class PointHistoryView(LoginRequiredMixin, ListView):
    """
    O'quvchi ball tarixi
    """
    model = PointTransaction
    template_name = 'gamification/point_history.html'
    context_object_name = 'transactions'
    
    def get_queryset(self):
        student = self.request.user if self.request.user.is_student else self.kwargs.get('student_id')
        return PointTransaction.objects.filter(student=student).select_related(
            'attendance', 'homework', 'exam_result'
        ).order_by('-created_at')
