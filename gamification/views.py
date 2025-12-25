from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F, Avg, Count
from django.utils import timezone
from .models import (
    StudentPoints, StudentBadge, GroupRanking, BranchRanking,
    OverallRanking, MonthlyRanking, PointTransaction
)
from accounts.mixins import RoleRequiredMixin, AdminRequiredMixin
from accounts.models import User
from courses.models import Group


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
    paginate_by = 20
    
    def get_queryset(self):
        student_id = self.kwargs.get('student_id')
        
        # Get student object safely
        if self.request.user.is_student:
            student = self.request.user
        elif student_id:
            try:
                student = User.objects.get(pk=student_id)
            except User.DoesNotExist:
                student = self.request.user
        else:
            student = self.request.user
        
        queryset = StudentBadge.objects.filter(student=student).select_related('badge', 'group').order_by('-earned_at')
        
        # Filter by group
        group_id = self.request.GET.get('group')
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        
        # Filter by badge type
        badge_type = self.request.GET.get('badge_type')
        if badge_type:
            queryset = queryset.filter(badge__badge_type=badge_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from courses.models import Group
        from .models import Badge
        from django.http import Http404
        
        student = self.request.user if self.request.user.is_student else self.kwargs.get('student_id')
        
        # Get student object safely
        if isinstance(student, User):
            student_obj = student
        elif student:
            try:
                student_obj = User.objects.get(pk=student)
            except User.DoesNotExist:
                # If student_id is invalid, default to current user
                student_obj = self.request.user
        else:
            # If no student_id provided, use current user
            student_obj = self.request.user
        
        context['groups'] = Group.objects.filter(students=student_obj, is_active=True)
        context['badge_types'] = Badge.BADGE_TYPE_CHOICES
        context['total_badges'] = self.get_queryset().count()
        context['student'] = student_obj
        return context


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
    paginate_by = 30
    
    def get_queryset(self):
        student = self.request.user if self.request.user.is_student else self.kwargs.get('student_id')
        return PointTransaction.objects.filter(student=student).select_related(
            'attendance', 'homework', 'exam_result'
        ).order_by('-created_at')


class StudentRankingView(LoginRequiredMixin, TemplateView):
    """Talabalar umumiy reytingi"""
    template_name = 'gamification/student_ranking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filterlar
        group_id = self.request.GET.get('group')
        course_id = self.request.GET.get('course')
        
        # Talabalar ro'yxati
        students = User.objects.filter(role='student', is_active=True)
        
        if group_id:
            students = students.filter(student_groups__id=group_id)
        
        # Ball bo'yicha saralash
        student_data = []
        for student in students:
            total_points = StudentPoints.objects.filter(student=student).aggregate(
                total=Sum('total_points')
            )['total'] or 0
            student_data.append({
                'student': student,
                'total_points': total_points
            })
        
        # Saralash
        student_data.sort(key=lambda x: x['total_points'], reverse=True)
        
        # Rank qo'shish
        for i, data in enumerate(student_data):
            data['rank'] = i + 1
        
        context['student_data'] = student_data[:100]  # Top 100
        context['groups'] = Group.objects.filter(is_active=True)
        
        return context


class GroupsRankingView(LoginRequiredMixin, TemplateView):
    """Guruhlar reytingi"""
    template_name = 'gamification/groups_ranking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        groups = Group.objects.filter(is_active=True).select_related('course', 'mentor')
        
        group_data = []
        for group in groups:
            avg_points = StudentPoints.objects.filter(group=group).aggregate(
                avg=Avg('total_points')
            )['avg'] or 0
            
            group_data.append({
                'group': group,
                'avg_points': avg_points,
                'student_count': group.students.count()
            })
        
        # Saralash
        group_data.sort(key=lambda x: x['avg_points'], reverse=True)
        
        # Rank
        for i, data in enumerate(group_data):
            data['rank'] = i + 1
        
        context['group_data'] = group_data
        
        return context


class MentorRankingView(AdminRequiredMixin, TemplateView):
    """Mentorlar reytingi (faqat admin)"""
    template_name = 'gamification/mentor_ranking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        mentors = User.objects.filter(role='mentor', is_active=True)
        
        mentor_data = []
        for mentor in mentors:
            groups = Group.objects.filter(mentor=mentor, is_active=True)
            total_students = sum(g.students.count() for g in groups)
            
            # KPI hisoblash
            from mentors.models import MentorKPI
            kpi = MentorKPI.objects.filter(mentor=mentor).first()
            
            mentor_data.append({
                'mentor': mentor,
                'groups_count': groups.count(),
                'students_count': total_students,
                'kpi_score': kpi.total_kpi_score if kpi else 0  # Use total_kpi_score instead of overall_score
            })
        
        # KPI bo'yicha saralash
        mentor_data.sort(key=lambda x: x['kpi_score'], reverse=True)
        
        # Rank
        for i, data in enumerate(mentor_data):
            data['rank'] = i + 1
        
        context['mentor_data'] = mentor_data
        
        return context
