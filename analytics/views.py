from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta
from accounts.mixins import AdminRequiredMixin, RoleRequiredMixin
from accounts.models import User, Branch
from courses.models import Course, Group, Lesson, StudentProgress
from attendance.models import Attendance, AttendanceStatistics
from homework.models import Homework
from exams.models import Exam, ExamResult
from gamification.models import StudentPoints, GroupRanking, BranchRanking, OverallRanking
from crm.models import Lead, FollowUp
from mentors.models import MentorKPI
from finance.models import Contract, Payment, PaymentPlan, Debt, PaymentReminder


class StatisticsDashboardView(RoleRequiredMixin, TemplateView):
    """
    Umumiy statistika dashboard (Admin/Manager uchun)
    """
    template_name = 'analytics/admin_dashboard.html'
    allowed_roles = ['admin', 'manager']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Umumiy statistika
        context['total_students'] = User.objects.filter(role='student', is_active=True).count()
        context['total_mentors'] = User.objects.filter(role='mentor', is_active=True).count()
        context['total_courses'] = Course.objects.filter(is_active=True).count()
        context['total_groups'] = Group.objects.filter(is_active=True).count()
        context['total_branches'] = Branch.objects.filter(is_active=True).count()
        
        # 2. O'quvchilar statistikasi
        context['active_students'] = User.objects.filter(
            role='student',
            is_active=True,
            student_groups__is_active=True
        ).distinct().count()
        context['new_students_this_month'] = User.objects.filter(
            role='student',
            created_at__gte=this_month_start
        ).count()
        
        # 3. Kurslar statistikasi
        context['courses_with_students'] = Course.objects.filter(
            groups__students__isnull=False
        ).distinct().count()
        
        # 4. Davomat statistikasi
        this_month_attendances = Attendance.objects.filter(
            lesson__date__gte=this_month_start
        )
        context['total_lessons_this_month'] = Lesson.objects.filter(
            date__gte=this_month_start
        ).count()
        context['total_attendances_this_month'] = this_month_attendances.count()
        context['present_count'] = this_month_attendances.filter(status='present').count()
        context['late_count'] = this_month_attendances.filter(status='late').count()
        context['absent_count'] = this_month_attendances.filter(status='absent').count()
        context['attendance_percentage'] = (
            (context['present_count'] + context['late_count']) / context['total_attendances_this_month'] * 100
        ) if context['total_attendances_this_month'] else 0
        
        # 5. Uy vazifalari statistikasi
        context['total_homeworks'] = Homework.objects.count()
        context['submitted_homeworks'] = Homework.objects.filter(is_submitted=True).count()
        context['graded_homeworks'] = Homework.objects.filter(
            homework_grade__isnull=False
        ).count()
        context['homework_submission_rate'] = (
            context['submitted_homeworks'] / context['total_homeworks'] * 100
        ) if context['total_homeworks'] else 0
        
        # 6. Imtihonlar statistikasi
        context['total_exams'] = Exam.objects.filter(is_active=True).count()
        context['total_exam_results'] = ExamResult.objects.count()
        context['passed_exams'] = ExamResult.objects.filter(is_passed=True).count()
        context['exam_pass_rate'] = (
            context['passed_exams'] / context['total_exam_results'] * 100
        ) if context['total_exam_results'] else 0
        
        # 7. Filiallar statistikasi
        branches_stats = []
        branches = Branch.objects.filter(is_active=True)
        for branch in branches:
            students_count = User.objects.filter(
                role='student',
                student_profile__branch=branch,
                is_active=True
            ).count()
            groups_count = Group.objects.filter(
                course__branch=branch,
                is_active=True
            ).count()
            courses_count = Course.objects.filter(
                branch=branch,
                is_active=True
            ).count()
            branch_attendances = Attendance.objects.filter(
                lesson__group__course__branch=branch,
                lesson__date__gte=this_month_start
            )
            total_att = branch_attendances.count()
            present_att = branch_attendances.filter(status__in=['present', 'late']).count()
            avg_attendance = (present_att / total_att * 100) if total_att > 0 else 0
            
            branches_stats.append({
                'branch': branch,
                'students_count': students_count,
                'groups_count': groups_count,
                'courses_count': courses_count,
                'avg_attendance': avg_attendance,
            })
        context['branches_stats'] = branches_stats
        
        # 8. CRM statistikasi
        context['total_leads'] = Lead.objects.count()
        context['new_leads_this_month'] = Lead.objects.filter(
            created_at__gte=this_month_start
        ).count()
        context['enrolled_leads_this_month'] = Lead.objects.filter(
            status__code='enrolled',
            updated_at__gte=this_month_start
        ).count()
        context['pending_followups'] = FollowUp.objects.filter(
            is_completed=False,
            scheduled_at__lt=now
        ).count()
        
        # 9. Mentor KPI statistikasi
        context['mentors_with_kpi'] = MentorKPI.objects.values('mentor').distinct().count()
        context['avg_mentor_kpi'] = MentorKPI.objects.aggregate(avg=Avg('total_kpi_score'))['avg'] or 0
        
        # 10. Gamification statistikasi
        context['total_points_awarded'] = StudentPoints.objects.aggregate(
            total=Sum('total_points')
        )['total'] or 0
        context['top_students'] = OverallRanking.objects.select_related('student').order_by('rank')[:10]
        
        # 11. Finance statistikasi
        context['finance_total_contracts'] = Contract.objects.count()
        context['finance_active_contracts'] = Contract.objects.filter(status='active').count()
        context['finance_total_revenue'] = Contract.objects.aggregate(total=Sum('total_amount'))['total'] or 0
        context['finance_total_paid'] = Contract.objects.aggregate(total=Sum('paid_amount'))['total'] or 0
        context['finance_total_debts'] = Debt.objects.filter(is_paid=False).aggregate(total=Sum('amount'))['total'] or 0
        context['finance_pending_reminders'] = PaymentReminder.objects.filter(is_sent=False).count()
        context['finance_upcoming_payments'] = PaymentPlan.objects.filter(is_paid=False, due_date__gte=now.date()).count()
        context['finance_overdue_payments'] = PaymentPlan.objects.filter(is_paid=False, due_date__lt=now.date()).count()
        
        return context


class BranchStatisticsView(RoleRequiredMixin, TemplateView):
    """
    Filial bo'yicha batafsil statistika
    """
    template_name = 'analytics/branch_statistics.html'
    allowed_roles = ['admin', 'manager']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branch_id = self.kwargs.get('branch_id')
        branch = Branch.objects.get(pk=branch_id)
        
        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        context['branch'] = branch
        
        # O'quvchilar
        context['students'] = User.objects.filter(
            role='student',
            student_profile__branch=branch,
            is_active=True
        ).count()
        
        # Kurslar va guruhlar
        context['courses'] = Course.objects.filter(branch=branch, is_active=True).count()
        context['groups'] = Group.objects.filter(
            course__branch=branch,
            is_active=True
        ).count()
        
        # Davomat
        attendances = Attendance.objects.filter(
            lesson__group__course__branch=branch,
            lesson__date__gte=this_month_start
        )
        context['total_attendances'] = attendances.count()
        context['present_count'] = attendances.filter(status='present').count()
        context['late_count'] = attendances.filter(status='late').count()
        context['absent_count'] = attendances.filter(status='absent').count()
        
        # Reytinglar
        context['branch_rankings'] = BranchRanking.objects.filter(
            branch=branch
        ).select_related('student').order_by('rank')[:20]
        
        return context


class CourseStatisticsView(RoleRequiredMixin, TemplateView):
    """
    Kurs bo'yicha statistika
    """
    template_name = 'analytics/course_statistics.html'
    allowed_roles = ['admin', 'manager']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('course_id')
        course = Course.objects.get(pk=course_id)
        
        context['course'] = course
        
        # Guruhlar
        context['groups'] = Group.objects.filter(course=course, is_active=True)
        context['total_groups'] = context['groups'].count()
        
        # O'quvchilar
        students = User.objects.filter(
            student_groups__course=course,
            is_active=True
        ).distinct()
        context['students'] = students.count()
        
        # Progress
        progresses = StudentProgress.objects.filter(course=course)
        context['avg_progress'] = progresses.aggregate(avg=Avg('progress_percentage'))['avg'] or 0
        context['completed_students'] = progresses.filter(progress_percentage=100).count()
        
        # Guruhlar statistikasi
        groups_stats = []
        for group in context['groups']:
            students_count = group.students.filter(role='student').count()
            avg_progress = StudentProgress.objects.filter(
                student__in=group.students.all(),
                course=course
            ).aggregate(avg=Avg('progress_percentage'))['avg'] or 0
            
            groups_stats.append({
                'group': group,
                'students_count': students_count,
                'avg_progress': avg_progress,
            })
        
        context['groups_stats'] = groups_stats
        
        return context

