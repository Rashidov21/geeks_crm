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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Stats for cards
        attendances = self.get_queryset()
        context['present_count'] = attendances.filter(status='present').count()
        context['late_count'] = attendances.filter(status='late').count()
        context['absent_count'] = attendances.filter(status='absent').count()
        total = attendances.count()
        if total > 0:
            context['attendance_percentage'] = ((context['present_count'] + context['late_count']) / total) * 100
        else:
            context['attendance_percentage'] = 0
        return context


class AttendanceCreateView(TailwindFormMixin, MentorRequiredMixin, CreateView):
    model = Attendance
    template_name = 'attendance/attendance_form.html'
    fields = ['lesson', 'student', 'status', 'notes']
    
    def get_success_url(self):
        from django.urls import reverse
        return reverse('attendance:attendance_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter lessons by mentor if specific lesson_id not provided
        if 'lesson_id' in self.kwargs:
            form.fields['lesson'].initial = self.kwargs['lesson_id']
            form.fields['lesson'].widget = form.fields['lesson'].hidden_widget()
        else:
            # Show only mentor's lessons
            form.fields['lesson'].queryset = Lesson.objects.filter(
                group__mentor=self.request.user
            ).order_by('-date')
        return form
    
    def form_valid(self, form):
        if 'lesson_id' in self.kwargs:
            form.instance.lesson = Lesson.objects.get(pk=self.kwargs['lesson_id'])
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
