from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Attendance, AttendanceStatistics
from courses.models import Lesson
from accounts.mixins import MentorRequiredMixin, TailwindFormMixin


class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendances'
    
    def get_queryset(self):
        queryset = Attendance.objects.select_related('student', 'lesson', 'lesson__group')
        if self.request.user.is_student:
            queryset = queryset.filter(student=self.request.user)
        elif self.request.user.is_mentor:
            queryset = queryset.filter(lesson__mentor=self.request.user)
        return queryset.order_by('-lesson__date', '-lesson__start_time')


class AttendanceCreateView(TailwindFormMixin, MentorRequiredMixin, CreateView):
    model = Attendance
    template_name = 'attendance/attendance_form.html'
    fields = ['student', 'status', 'notes']
    
    def get_lesson(self):
        return Lesson.objects.get(pk=self.kwargs['lesson_id'])
    
    def form_valid(self, form):
        form.instance.lesson = self.get_lesson()
        return super().form_valid(form)


class AttendanceStatisticsView(LoginRequiredMixin, ListView):
    model = AttendanceStatistics
    template_name = 'attendance/statistics.html'
    context_object_name = 'statistics'
    
    def get_queryset(self):
        queryset = AttendanceStatistics.objects.select_related('student', 'group')
        if self.request.user.is_student:
            queryset = queryset.filter(student=self.request.user)
        return queryset.order_by('-attendance_percentage')
