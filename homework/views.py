from django.views.generic import ListView, CreateView, DetailView, UpdateView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Homework, HomeworkGrade
from accounts.mixins import MentorRequiredMixin, RoleRequiredMixin, TailwindFormMixin
from courses.models import Group, Lesson


class HomeworkListView(LoginRequiredMixin, ListView):
    model = Homework
    template_name = 'homework/homework_list.html'
    context_object_name = 'homeworks'
    
    def get_queryset(self):
        queryset = Homework.objects.select_related('student', 'lesson', 'lesson__group', 'grade')
        
        # Rol bo'yicha filter
        if self.request.user.is_student:
            queryset = queryset.filter(student=self.request.user)
        elif self.request.user.is_mentor:
            queryset = queryset.filter(lesson__group__mentor=self.request.user)
        
        # Qo'shimcha filterlar
        status = self.request.GET.get('status')
        if status == 'submitted':
            queryset = queryset.filter(is_submitted=True)
        elif status == 'pending':
            queryset = queryset.filter(is_submitted=False, deadline__gte=timezone.now())
        elif status == 'overdue':
            queryset = queryset.filter(is_submitted=False, deadline__lt=timezone.now())
        elif status == 'graded':
            queryset = queryset.filter(grade__isnull=False)
        
        group_id = self.request.GET.get('group')
        if group_id:
            queryset = queryset.filter(lesson__group_id=group_id)
        
        return queryset.order_by('-deadline', '-submitted_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        homeworks = Homework.objects.all()
        
        if self.request.user.is_student:
            homeworks = homeworks.filter(student=self.request.user)
        elif self.request.user.is_mentor:
            homeworks = homeworks.filter(lesson__group__mentor=self.request.user)
        
        context['total_homeworks'] = homeworks.count()
        context['submitted_count'] = homeworks.filter(is_submitted=True).count()
        context['pending_count'] = homeworks.filter(is_submitted=False, deadline__gte=timezone.now()).count()
        context['overdue_count'] = homeworks.filter(is_submitted=False, deadline__lt=timezone.now()).count()
        context['graded_count'] = homeworks.filter(grade__isnull=False).count()
        
        # Guruhlar (mentor/admin uchun)
        if self.request.user.is_mentor:
            context['groups'] = Group.objects.filter(mentor=self.request.user, is_active=True)
        elif self.request.user.is_admin or self.request.user.is_manager:
            context['groups'] = Group.objects.filter(is_active=True)
        
        # Permissions
        user = self.request.user
        context['can_create'] = user.is_admin or user.is_manager or user.is_mentor
        context['can_edit'] = user.is_admin or user.is_manager or user.is_mentor
        context['can_delete'] = user.is_admin or user.is_manager
        
        return context


class HomeworkCreateView(TailwindFormMixin, LoginRequiredMixin, CreateView):
    model = Homework
    template_name = 'homework/homework_form.html'
    fields = ['lesson', 'title', 'description', 'file', 'link', 'code', 'deadline']
    success_url = reverse_lazy('homework:homework_list')
    
    def form_valid(self, form):
        form.instance.student = self.request.user
        return super().form_valid(form)


class HomeworkAssignView(MentorRequiredMixin, TemplateView):
    """Mentor: Vazifa berish"""
    template_name = 'homework/homework_assign.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = Group.objects.filter(mentor=self.request.user, is_active=True)
        return context
    
    def post(self, request):
        group_id = request.POST.get('group')
        title = request.POST.get('title')
        description = request.POST.get('description')
        deadline = request.POST.get('deadline')
        
        group = get_object_or_404(Group, pk=group_id)
        
        # Har bir talaba uchun homework yaratish
        for student in group.students.all():
            Homework.objects.create(
                student=student,
                title=title,
                description=description,
                deadline=deadline
            )
        
        messages.success(request, f'{group.students.count()} ta talabaga vazifa berildi.')
        return redirect('homework:homework_list')


class HomeworkSubmitView(LoginRequiredMixin, View):
    """Student: Vazifa topshirish"""
    
    def post(self, request, pk):
        homework = get_object_or_404(Homework, pk=pk, student=request.user)
        
        homework.file = request.FILES.get('file') or homework.file
        homework.link = request.POST.get('link') or homework.link
        homework.code = request.POST.get('code') or homework.code
        homework.is_submitted = True
        homework.submitted_at = timezone.now()
        homework.save()
        
        messages.success(request, 'Vazifa muvaffaqiyatli topshirildi.')
        return redirect('homework:homework_detail', pk=pk)


class HomeworkBulkGradeView(MentorRequiredMixin, TemplateView):
    """Mentor: Bulk baholash"""
    template_name = 'homework/homework_bulk_grade.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.request.GET.get('group')
        
        homeworks = Homework.objects.filter(
            lesson__group__mentor=self.request.user,
            is_submitted=True,
            grade__isnull=True
        ).select_related('student', 'lesson__group')
        
        if group_id:
            homeworks = homeworks.filter(lesson__group_id=group_id)
        
        context['homeworks'] = homeworks
        context['groups'] = Group.objects.filter(mentor=self.request.user, is_active=True)
        return context
    
    def post(self, request):
        homework_ids = request.POST.getlist('homework_ids')
        grades = request.POST.getlist('grades')
        comments = request.POST.getlist('comments')
        
        for i, hw_id in enumerate(homework_ids):
            if grades[i]:
                homework = Homework.objects.get(pk=hw_id)
                HomeworkGrade.objects.update_or_create(
                    homework=homework,
                    defaults={
                        'grade': int(grades[i]),
                        'comment': comments[i] if i < len(comments) else '',
                        'mentor': request.user
                    }
                )
        
        messages.success(request, f'{len(homework_ids)} ta vazifa baholandi.')
        return redirect('homework:homework_list')


class HomeworkDetailView(LoginRequiredMixin, DetailView):
    model = Homework
    template_name = 'homework/homework_detail.html'
    context_object_name = 'homework'
    
    def get_queryset(self):
        return Homework.objects.select_related('student', 'lesson', 'grade__mentor')


class HomeworkGradeView(TailwindFormMixin, MentorRequiredMixin, UpdateView):
    model = HomeworkGrade
    template_name = 'homework/homework_grade_form.html'
    fields = ['grade', 'comment']
    
    def get_object(self):
        homework = Homework.objects.get(pk=self.kwargs['pk'])
        grade, created = HomeworkGrade.objects.get_or_create(homework=homework)
        if created:
            grade.mentor = self.request.user
            grade.save()
        return grade
    
    def get_success_url(self):
        return reverse_lazy('homework:homework_detail', kwargs={'pk': self.kwargs['pk']})
