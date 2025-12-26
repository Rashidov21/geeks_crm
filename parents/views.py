from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Sum
from accounts.mixins import RoleRequiredMixin
from .models import MonthlyParentReport, ParentDashboard
from accounts.models import User
from courses.models import Lesson, Group
from homework.models import Homework
from exams.models import ExamResult
from attendance.models import Attendance
from mentors.models import MonthlyReport


class ParentDashboardView(LoginRequiredMixin, TemplateView):
    """
    Ota-ona dashboard
    """
    template_name = 'parents/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent = self.request.user
        
        # Ota-onaning farzandlari
        try:
            students = parent.parent_profile.students.all()
        except:
            students = User.objects.none()
        
        # Har bir farzand uchun statistikalar va student obyektiga qo'shish
        student_stats = []
        for student in students:
            # Davomat
            from attendance.models import AttendanceStatistics
            attendance_stats = AttendanceStatistics.objects.filter(student=student).first()
            attendance_percentage = attendance_stats.attendance_percentage if attendance_stats else 0
            
            # Uy vazifalari
            total_homeworks = Homework.objects.filter(student=student).count()
            completed_homeworks = Homework.objects.filter(student=student, is_submitted=True).count()
            homework_completion = (completed_homeworks / total_homeworks * 100) if total_homeworks > 0 else 0
            
            # Imtihonlar
            total_exams = ExamResult.objects.filter(student=student).count()
            passed_exams = ExamResult.objects.filter(student=student, is_passed=True).count()
            exam_pass_rate = (passed_exams / total_exams * 100) if total_exams > 0 else 0
            
            # Progress
            from courses.models import StudentProgress
            progress = StudentProgress.objects.filter(student=student).first()
            progress_percentage = progress.progress_percentage if progress else 0
            
            # Student obyektiga statistika ma'lumotlarini qo'shish (template uchun)
            student.attendance_percentage = attendance_percentage
            student.progress_percentage = progress_percentage
            student.homework_completion = homework_completion
            student.exam_pass_rate = exam_pass_rate
            
            student_stats.append({
                'student': student,
                'attendance_percentage': attendance_percentage,
                'homework_completion': homework_completion,
                'exam_pass_rate': exam_pass_rate,
                'progress_percentage': progress_percentage,
            })
        
        context['students'] = students
        context['student_stats'] = student_stats
        
        # Oylik hisobotlar soni
        context['monthly_reports_count'] = MonthlyReport.objects.filter(
            student__in=students
        ).count()
        
        return context


class StudentDetailView(LoginRequiredMixin, DetailView):
    """
    Farzandning batafsil ma'lumotlari
    """
    model = User
    template_name = 'parents/student_detail.html'
    context_object_name = 'student'
    
    def get_queryset(self):
        # Faqat ota-onaning farzandlari
        # Check if user has parent_profile and get students from there
        if hasattr(self.request.user, 'parent_profile'):
            parent_profile = self.request.user.parent_profile
            return parent_profile.students.all()
        else:
            # If no parent_profile, return empty queryset
            return User.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object
        
        # Guruhlar
        groups = Group.objects.filter(students=student, is_active=True).select_related('course', 'mentor')
        context['groups'] = groups
        context['group'] = groups.first() if groups.exists() else None
        
        # Darslar tarixi (oxirgi 10 tasi)
        lessons = Lesson.objects.filter(group__in=groups).select_related('group', 'topic', 'group__mentor').order_by('-date', '-start_time')[:10]
        context['lessons'] = lessons
        context['lessons_count'] = Lesson.objects.filter(group__in=groups).count()
        
        # Uy vazifalari (oxirgi 10 tasi)
        homeworks = Homework.objects.filter(student=student).select_related('lesson', 'grade__mentor').order_by('-deadline')[:10]
        context['homeworks'] = homeworks
        context['homeworks_count'] = Homework.objects.filter(student=student).count()
        context['homeworks_submitted'] = Homework.objects.filter(student=student, is_submitted=True).count()
        context['homeworks_pending'] = Homework.objects.filter(student=student, is_submitted=False, deadline__gte=timezone.now()).count()
        context['homeworks_overdue'] = Homework.objects.filter(student=student, is_submitted=False, deadline__lt=timezone.now()).count()
        
        # Testlar va imtihonlar (oxirgi 10 tasi)
        exam_results = ExamResult.objects.filter(student=student).select_related('exam').order_by('-submitted_at')[:10]
        context['exam_results'] = exam_results
        context['exam_results_count'] = ExamResult.objects.filter(student=student).count()
        
        # Davomat statistikasi
        attendances = Attendance.objects.filter(student=student).select_related('lesson', 'lesson__group')
        context['attendances_count'] = attendances.count()
        context['present_count'] = attendances.filter(status='present').count()
        context['late_count'] = attendances.filter(status='late').count()
        context['absent_count'] = attendances.filter(status='absent').count()
        
        # Davomat foizi
        total_attendance = context['attendances_count']
        if total_attendance > 0:
            context['attendance_percentage'] = ((context['present_count'] + context['late_count']) / total_attendance) * 100
        else:
            context['attendance_percentage'] = 0
        
        # Progress foizi (kurs bo'yicha)
        from courses.models import StudentProgress
        progress = StudentProgress.objects.filter(student=student).first()
        context['progress_percentage'] = progress.progress_percentage if progress else 0
        
        # Mentor sharhlari (oylik hisobotlar) - oxirgi 6 tasi
        monthly_reports = MonthlyReport.objects.filter(student=student).select_related('mentor', 'group').order_by('-year', '-month')[:6]
        context['monthly_reports'] = monthly_reports
        context['monthly_reports_count'] = MonthlyReport.objects.filter(student=student).count()
        
        # Ball va badge'lar
        from gamification.models import StudentPoints, StudentBadge
        total_points = StudentPoints.objects.filter(student=student).aggregate(total=Sum('total_points'))['total'] or 0
        context['total_points'] = total_points
        context['badges_count'] = StudentBadge.objects.filter(student=student).count()
        
        return context


class LessonHistoryView(LoginRequiredMixin, ListView):
    """
    Darslar tarixi
    """
    model = Lesson
    template_name = 'parents/lesson_history.html'
    context_object_name = 'lessons'
    
    def get_queryset(self):
        student_id = self.kwargs.get('student_id')
        student = User.objects.get(pk=student_id, role='student')
        
        # Ota-onaning farzandi ekanligini tekshirish
        try:
            if student not in self.request.user.parent_profile.students.all():
                return Lesson.objects.none()
        except:
            return Lesson.objects.none()
        
        groups = Group.objects.filter(students=student)
        return Lesson.objects.filter(group__in=groups).select_related('group', 'topic', 'mentor').order_by('-date', '-start_time')


class HomeworkStatusView(LoginRequiredMixin, ListView):
    """
    Uy vazifalari holati
    """
    model = Homework
    template_name = 'parents/homework_status.html'
    context_object_name = 'homeworks'
    
    def get_queryset(self):
        student_id = self.kwargs.get('student_id')
        student = User.objects.get(pk=student_id, role='student')
        
        # Ota-onaning farzandi ekanligini tekshirish
        try:
            if student not in self.request.user.parent_profile.students.all():
                return Homework.objects.none()
        except:
            return Homework.objects.none()
        
        return Homework.objects.filter(student=student).select_related('lesson', 'grade__mentor').order_by('-deadline')


class ExamResultsView(LoginRequiredMixin, ListView):
    """
    Test va imtihon natijalari
    """
    model = ExamResult
    template_name = 'parents/exam_results.html'
    context_object_name = 'exam_results'
    
    def get_queryset(self):
        student_id = self.kwargs.get('student_id')
        student = User.objects.get(pk=student_id, role='student')
        
        # Ota-onaning farzandi ekanligini tekshirish
        try:
            if student not in self.request.user.parent_profile.students.all():
                return ExamResult.objects.none()
        except:
            return ExamResult.objects.none()
        
        return ExamResult.objects.filter(student=student).select_related('exam').order_by('-submitted_at')


class AttendanceListView(LoginRequiredMixin, ListView):
    """
    Keldi/kelmadi ro'yxati
    """
    model = Attendance
    template_name = 'parents/attendance_list.html'
    context_object_name = 'attendances'
    
    def get_queryset(self):
        student_id = self.kwargs.get('student_id')
        student = User.objects.get(pk=student_id, role='student')
        
        # Ota-onaning farzandi ekanligini tekshirish
        try:
            if student not in self.request.user.parent_profile.students.all():
                return Attendance.objects.none()
        except:
            return Attendance.objects.none()
        
        return Attendance.objects.filter(student=student).select_related('lesson', 'lesson__group').order_by('-lesson__date')


class MonthlyReportView(LoginRequiredMixin, DetailView):
    """
    Oylik hisobot ko'rish
    """
    model = MonthlyParentReport
    template_name = 'parents/monthly_report.html'
    context_object_name = 'report'
    
    def get_queryset(self):
        # Faqat ota-onaning o'z hisobotlari
        return MonthlyParentReport.objects.filter(parent=self.request.user)


class MonthlyReportListView(LoginRequiredMixin, ListView):
    """
    Oylik hisobotlar ro'yxati
    """
    model = MonthlyParentReport
    template_name = 'parents/monthly_report_list.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        queryset = MonthlyParentReport.objects.filter(parent=self.request.user)
        
        student_id = self.request.GET.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset.select_related('student', 'group', 'mentor_report__mentor').order_by('-year', '-month')
