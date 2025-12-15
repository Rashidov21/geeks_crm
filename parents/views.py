from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
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
        
        context['students'] = students
        
        # Har bir farzand uchun statistikalar
        student_stats = []
        for student in students:
            # Davomat
            from attendance.models import AttendanceStatistics
            attendance_stats = AttendanceStatistics.objects.filter(student=student).first()
            
            # Uy vazifalari
            total_homeworks = Homework.objects.filter(student=student).count()
            completed_homeworks = Homework.objects.filter(student=student, is_submitted=True).count()
            
            # Imtihonlar
            total_exams = ExamResult.objects.filter(student=student).count()
            passed_exams = ExamResult.objects.filter(student=student, is_passed=True).count()
            
            # Progress
            from courses.models import StudentProgress
            progress = StudentProgress.objects.filter(student=student).first()
            
            student_stats.append({
                'student': student,
                'attendance_percentage': attendance_stats.attendance_percentage if attendance_stats else 0,
                'homework_completion': (completed_homeworks / total_homeworks * 100) if total_homeworks > 0 else 0,
                'exam_pass_rate': (passed_exams / total_exams * 100) if total_exams > 0 else 0,
                'progress_percentage': progress.progress_percentage if progress else 0,
            })
        
        context['student_stats'] = student_stats
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
        return User.objects.filter(
            role='student',
            parents=self.request.user
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object
        
        # Darslar tarixi
        groups = Group.objects.filter(students=student)
        lessons = Lesson.objects.filter(group__in=groups).select_related('group', 'topic', 'mentor').order_by('-date', '-start_time')[:20]
        context['lessons'] = lessons
        
        # Uy vazifalari
        homeworks = Homework.objects.filter(student=student).select_related('lesson', 'grade__mentor').order_by('-deadline')[:20]
        context['homeworks'] = homeworks
        
        # Testlar va imtihonlar
        exam_results = ExamResult.objects.filter(student=student).select_related('exam').order_by('-submitted_at')[:20]
        context['exam_results'] = exam_results
        
        # Davomat
        attendances = Attendance.objects.filter(student=student).select_related('lesson', 'lesson__group').order_by('-lesson__date')[:30]
        context['attendances'] = attendances
        
        # Mentor sharhlari (oylik hisobotlar)
        monthly_reports = MonthlyReport.objects.filter(student=student).select_related('mentor', 'group').order_by('-year', '-month')[:12]
        context['monthly_reports'] = monthly_reports
        
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
