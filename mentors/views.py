from django.views.generic import ListView, DetailView, CreateView, UpdateView,TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import MentorKPI, MentorRanking, MonthlyReport, LessonQuality, ParentFeedback
from accounts.mixins import MentorRequiredMixin, AdminRequiredMixin, TailwindFormMixin


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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kpi = self.object
        mentor = kpi.mentor
        
        # Guruhlar
        from courses.models import Group
        groups = Group.objects.filter(mentor=mentor, is_active=True).select_related('course')
        context['groups'] = groups
        context['groups_count'] = groups.count()
        
        # O'quvchilar
        total_students = sum(g.students.filter(role='student', is_active=True).count() for g in groups)
        context['total_students'] = total_students
        
        # Darslar
        from courses.models import Lesson
        from datetime import datetime
        month_start = datetime(year=kpi.year, month=kpi.month, day=1).date()
        if kpi.month == 12:
            month_end = datetime(year=kpi.year + 1, month=1, day=1).date()
        else:
            month_end = datetime(year=kpi.year, month=kpi.month + 1, day=1).date()
        
        lessons = Lesson.objects.filter(
            group__mentor=mentor,
            date__gte=month_start,
            date__lt=month_end
        )
        context['lessons_count'] = lessons.count()
        
        # Uy vazifalari
        from homework.models import Homework
        homeworks = Homework.objects.filter(
            lesson__group__mentor=mentor,
            deadline__year=kpi.year,
            deadline__month=kpi.month
        )
        context['homeworks_count'] = homeworks.count()
        context['homeworks_graded'] = homeworks.filter(grade__isnull=False).count()
        
        # Oylik hisobotlar
        reports = MonthlyReport.objects.filter(
            mentor=mentor,
            year=kpi.year,
            month=kpi.month
        )
        context['reports_count'] = reports.count()
        
        # Permissions
        context['can_view_all'] = self.request.user.is_admin or self.request.user.is_manager
        context['is_own_kpi'] = self.request.user == mentor
        
        return context


class MentorRankingView(LoginRequiredMixin, TemplateView):
    """
    Mentorlar reytingi
    """
    template_name = 'mentors/mentor_ranking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from accounts.models import User
        from courses.models import Group
        from .models import MentorKPI
        
        mentors = User.objects.filter(role='mentor', is_active=True)
        
        mentor_data = []
        for mentor in mentors:
            groups = Group.objects.filter(mentor=mentor, is_active=True)
            total_students = sum(g.students.filter(role='student').count() for g in groups)
            
            # KPI hisoblash
            kpi = MentorKPI.objects.filter(mentor=mentor).order_by('-year', '-month').first()
            
            mentor_data.append({
                'user': mentor,
                'groups_count': groups.count(),
                'students_count': total_students,
                'kpi_score': kpi.total_kpi_score if kpi else 0
            })
        
        # KPI bo'yicha saralash
        mentor_data.sort(key=lambda x: x['kpi_score'], reverse=True)
        
        context['mentors'] = mentor_data
        context['can_create'] = self.request.user.is_admin or self.request.user.is_manager
        return context


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


class MonthlyReportCreateView(TailwindFormMixin, MentorRequiredMixin, CreateView):
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


class MonthlyReportUpdateView(TailwindFormMixin, MentorRequiredMixin, UpdateView):
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


class LessonQualityCreateView(TailwindFormMixin, LoginRequiredMixin, CreateView):
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


class ParentFeedbackCreateView(TailwindFormMixin, LoginRequiredMixin, CreateView):
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
