"""
Role-based dashboard views
"""
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta

from .models import User
from courses.models import Group, Lesson, StudentProgress
from attendance.models import Attendance
from homework.models import Homework
from exams.models import Exam, ExamResult
from gamification.models import StudentPoints, StudentBadge, GroupRanking
from parents.models import MonthlyParentReport


class DashboardView(TemplateView):
    """
    Role-based dashboard redirector
    """
    def get(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        user = request.user
        
        # Redirect based on role
        if user.role in ['admin', 'manager']:
            return redirect('analytics:dashboard')
        elif user.role == 'student':
            return redirect('accounts:student_dashboard')
        elif user.role == 'mentor':
            return redirect('accounts:mentor_dashboard')
        elif user.role == 'parent':
            return redirect('parents:dashboard')
        elif user.role == 'accountant':
            return redirect('finance:dashboard')
        elif user.role in ['sales', 'sales_manager']:
            return redirect('crm:lead_list')
        else:
            # Default fallback
            return redirect('accounts:profile')


class StudentDashboardView(LoginRequiredMixin, TemplateView):
    """
    Student dashboard
    """
    template_name = 'accounts/student_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'student':
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user
        now = timezone.now()
        this_week_start = now - timedelta(days=now.weekday())
        
        # My Groups
        context['my_groups'] = student.student_groups.filter(is_active=True)
        
        # My Progress
        progress_list = StudentProgress.objects.filter(
            student=student
        ).select_related('course')
        context['my_progress'] = progress_list
        context['avg_progress'] = progress_list.aggregate(avg=Avg('progress_percentage'))['avg'] or 0
        
        # Recent Lessons (this week)
        context['recent_lessons'] = Lesson.objects.filter(
            group__in=context['my_groups'],
            date__gte=this_week_start.date()
        ).order_by('-date', '-start_time')[:5]
        
        # My Attendance Stats (this month)
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        my_attendances = Attendance.objects.filter(
            student=student,
            lesson__date__gte=this_month_start.date()
        )
        total_att = my_attendances.count()
        present_att = my_attendances.filter(status__in=['present', 'late']).count()
        context['my_attendance_count'] = total_att
        context['my_attendance_percentage'] = (present_att / total_att * 100) if total_att > 0 else 0
        context['my_present_count'] = my_attendances.filter(status='present').count()
        context['my_late_count'] = my_attendances.filter(status='late').count()
        context['my_absent_count'] = my_attendances.filter(status='absent').count()
        
        # Pending Homework
        context['pending_homeworks'] = Homework.objects.filter(
            student=student,
            is_submitted=False,
            deadline__gte=now.date()
        ).order_by('deadline')[:5]
        
        context['overdue_homeworks'] = Homework.objects.filter(
            student=student,
            is_submitted=False,
            deadline__lt=now.date()
        ).count()
        
        # Upcoming Exams
        context['upcoming_exams'] = Exam.objects.filter(
            group__in=context['my_groups'],
            date__gte=now.date(),
            is_active=True
        ).order_by('date')[:5]
        
        # My Points and Ranking
        try:
            student_points = StudentPoints.objects.get(student=student)
            context['my_points'] = student_points.total_points
            context['my_level'] = student_points.level
        except StudentPoints.DoesNotExist:
            context['my_points'] = 0
            context['my_level'] = 1
        
        # My Badges
        context['my_badges'] = StudentBadge.objects.filter(
            student=student
        ).select_related('badge').order_by('-earned_at')[:6]
        
        # My Group Rankings
        context['my_rankings'] = GroupRanking.objects.filter(
            student=student
        ).select_related('group').order_by('rank')
        
        return context


class MentorDashboardView(LoginRequiredMixin, TemplateView):
    """
    Mentor dashboard
    """
    template_name = 'accounts/mentor_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'mentor':
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mentor = self.request.user
        now = timezone.now()
        today = now.date()
        this_week_start = now - timedelta(days=now.weekday())
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # My Groups
        context['my_groups'] = Group.objects.filter(
            mentor=mentor,
            is_active=True
        ).annotate(
            students_count=Count('students', filter=Q(students__role='student'))
        )
        
        # Total Students
        total_students = 0
        for group in context['my_groups']:
            total_students += group.students_count
        context['total_students'] = total_students
        
        # Today's Lessons
        context['todays_lessons'] = Lesson.objects.filter(
            group__mentor=mentor,
            date=today
        ).select_related('group', 'room').order_by('start_time')
        
        # This Week's Lessons
        context['this_week_lessons'] = Lesson.objects.filter(
            group__mentor=mentor,
            date__gte=this_week_start.date(),
            date__lt=today + timedelta(days=7)
        ).select_related('group', 'room').order_by('date', 'start_time')[:10]
        
        # Homework to Grade
        context['homeworks_to_grade'] = Homework.objects.filter(
            lesson__group__mentor=mentor,
            is_submitted=True,
            grade__isnull=True
        ).select_related('student', 'lesson').order_by('submitted_at')[:10]
        
        context['homeworks_to_grade_count'] = Homework.objects.filter(
            lesson__group__mentor=mentor,
            is_submitted=True,
            grade__isnull=True
        ).count()
        
        # Attendance Stats (this month)
        attendances = Attendance.objects.filter(
            lesson__group__mentor=mentor,
            lesson__date__gte=this_month_start.date()
        )
        total_att = attendances.count()
        present_att = attendances.filter(status__in=['present', 'late']).count()
        context['attendance_count'] = total_att
        context['attendance_percentage'] = (present_att / total_att * 100) if total_att > 0 else 0
        
        # My KPI
        from mentors.models import MentorKPI
        try:
            latest_kpi = MentorKPI.objects.filter(mentor=mentor).order_by('-month', '-year').first()
            if latest_kpi:
                context['my_kpi'] = latest_kpi.total_kpi_score
                context['my_kpi_month'] = f"{latest_kpi.year}-{latest_kpi.month:02d}"
            else:
                context['my_kpi'] = None
        except:
            context['my_kpi'] = None
        
        # Recent Exams
        context['recent_exams'] = Exam.objects.filter(
            group__mentor=mentor,
            is_active=True
        ).order_by('-date')[:5]
        
        return context

