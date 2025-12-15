from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import MentorKPI, MentorRanking, MonthlyReport, LessonQuality, ParentFeedback
from accounts.mixins import MentorRequiredMixin, AdminRequiredMixin


class MentorKPIView(LoginRequiredMixin, DetailView):
    """
    Mentor KPI ko'rish
    """
    model = MentorKPI
    template_name = 'mentors/kpi_detail.html'
    context_object_name = 'kpi'
    
    def get_object(self):
        mentor = self.request.user if self.request.user.is_mentor else self.kwargs.get('mentor_id')
        month = self.kwargs.get('month', timezone.now().month)
        year = self.kwargs.get('year', timezone.now().year)
        
        kpi, created = MentorKPI.objects.get_or_create(
            mentor=mentor,
            month=month,
            year=year
        )
        
        if created:
            from .tasks import calculate_mentor_kpi
            calculate_mentor_kpi.delay(mentor.id, month, year)
        
        return kpi


class MentorRankingView(LoginRequiredMixin, ListView):
    """
    Mentorlar reytingi
    """
    model = MentorRanking
    template_name = 'mentors/mentor_ranking.html'
    context_object_name = 'rankings'
    
    def get_queryset(self):
        month = self.kwargs.get('month', timezone.now().month)
        year = self.kwargs.get('year', timezone.now().year)
        
        return MentorRanking.objects.filter(
            month=month,
            year=year
        ).select_related('mentor').order_by('rank')


class MonthlyReportListView(MentorRequiredMixin, ListView):
    """
    Oylik hisobotlar ro'yxati
    """
    model = MonthlyReport
    template_name = 'mentors/monthly_report_list.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        queryset = MonthlyReport.objects.filter(mentor=self.request.user)
        
        month = self.request.GET.get('month')
        year = self.request.GET.get('year')
        
        if month:
            queryset = queryset.filter(month=int(month))
        if year:
            queryset = queryset.filter(year=int(year))
        
        return queryset.select_related('student', 'group').order_by('-year', '-month')


class MonthlyReportCreateView(MentorRequiredMixin, CreateView):
    """
    Oylik hisobot yaratish
    """
    model = MonthlyReport
    template_name = 'mentors/monthly_report_form.html'
    fields = ['student', 'group', 'month', 'year', 'character', 'attendance', 
              'mastery', 'progress_change', 'additional_notes']
    success_url = reverse_lazy('mentors:monthly_report_list')
    
    def form_valid(self, form):
        form.instance.mentor = self.request.user
        form.instance.is_completed = True
        messages.success(self.request, 'Oylik hisobot muvaffaqiyatli yaratildi.')
        return super().form_valid(form)


class MonthlyReportUpdateView(MentorRequiredMixin, UpdateView):
    """
    Oylik hisobotni tahrirlash
    """
    model = MonthlyReport
    template_name = 'mentors/monthly_report_form.html'
    fields = ['character', 'attendance', 'mastery', 'progress_change', 'additional_notes']
    success_url = reverse_lazy('mentors:monthly_report_list')
    
    def get_queryset(self):
        return MonthlyReport.objects.filter(mentor=self.request.user)
    
    def form_valid(self, form):
        form.instance.is_completed = True
        messages.success(self.request, 'Oylik hisobot muvaffaqiyatli yangilandi.')
        return super().form_valid(form)


class LessonQualityCreateView(LoginRequiredMixin, CreateView):
    """
    Dars sifati baholash (o'quvchi tomonidan)
    """
    model = LessonQuality
    template_name = 'mentors/lesson_quality_form.html'
    fields = ['rating', 'comment']
    success_url = reverse_lazy('courses:lesson_list')
    
    def form_valid(self, form):
        from courses.models import Lesson
        lesson = Lesson.objects.get(pk=self.kwargs['lesson_id'])
        form.instance.lesson = lesson
        form.instance.student = self.request.user
        messages.success(self.request, 'Dars sifati baholandi.')
        return super().form_valid(form)


class ParentFeedbackCreateView(LoginRequiredMixin, CreateView):
    """
    Ota-ona feedback yaratish
    """
    model = ParentFeedback
    template_name = 'mentors/parent_feedback_form.html'
    fields = ['mentor', 'student', 'feedback_type', 'comment']
    success_url = reverse_lazy('parents:dashboard')
    
    def form_valid(self, form):
        form.instance.parent = self.request.user
        messages.success(self.request, 'Feedback muvaffaqiyatli yuborildi.')
        return super().form_valid(form)
