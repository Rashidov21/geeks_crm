from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, TemplateView, View
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
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Homework.objects.select_related('student', 'lesson', 'lesson__group', 'grade', 'grade__mentor')
        
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
        
        # Search query
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(student__first_name__icontains=search) |
                Q(student__last_name__icontains=search)
            )
        
        return queryset.order_by('-deadline', '-submitted_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use paginated queryset for stats
        paginator = context.get('paginator')
        if paginator:
            # Stats for all items (not just current page)
            all_homeworks = self.get_queryset()
            total_homeworks = all_homeworks.count()
            submitted_count = all_homeworks.filter(is_submitted=True).count()
            pending_count = all_homeworks.filter(is_submitted=False, deadline__gte=timezone.now()).count()
            overdue_count = all_homeworks.filter(is_submitted=False, deadline__lt=timezone.now()).count()
        else:
            # Fallback if pagination not used
            homeworks = self.get_queryset()
            total_homeworks = homeworks.count()
            submitted_count = homeworks.filter(is_submitted=True).count()
            pending_count = homeworks.filter(is_submitted=False, deadline__gte=timezone.now()).count()
            overdue_count = homeworks.filter(is_submitted=False, deadline__lt=timezone.now()).count()
        
        # Stats for cards
        context['stats'] = [
            {'label': 'Jami vazifalar', 'value': total_homeworks, 'icon': 'fas fa-tasks', 'color': 'text-orange-600'},
            {'label': 'Topshirilgan', 'value': submitted_count, 'icon': 'fas fa-check', 'color': 'text-green-600'},
            {'label': 'Kutilmoqda', 'value': pending_count, 'icon': 'fas fa-clock', 'color': 'text-yellow-600'},
            {'label': 'Kechikkan', 'value': overdue_count, 'icon': 'fas fa-exclamation-triangle', 'color': 'text-red-600'},
        ]
        
        # Guruhlar (mentor/admin uchun)
        if self.request.user.is_mentor:
            context['groups'] = Group.objects.filter(mentor=self.request.user, is_active=True)
        elif self.request.user.is_admin or self.request.user.is_manager:
            context['groups'] = Group.objects.filter(is_active=True)
        elif self.request.user.is_student:
            # Studentlar uchun o'z guruhlari
            context['groups'] = Group.objects.filter(students=self.request.user, is_active=True)
        
        # Permissions
        user = self.request.user
        context['can_create'] = user.is_superuser or (hasattr(user, 'is_admin') and user.is_admin) or (hasattr(user, 'is_manager') and user.is_manager) or (hasattr(user, 'is_mentor') and user.is_mentor)
        context['can_assign'] = user.is_mentor or user.is_admin or user.is_manager  # Mentor uchun assign button
        context['can_edit'] = context['can_create']
        context['can_delete'] = user.is_superuser or (hasattr(user, 'is_admin') and user.is_admin) or (hasattr(user, 'is_manager') and user.is_manager)
        
        # Now for template deadline comparison
        context['now'] = timezone.now()
        
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
        groups = Group.objects.filter(mentor=self.request.user, is_active=True).select_related('course')
        context['groups'] = groups
        
        # Har bir guruh uchun oxirgi darslar
        group_lessons = {}
        for group in groups:
            latest_lesson = Lesson.objects.filter(group=group).order_by('-date', '-start_time').first()
            group_lessons[group.id] = latest_lesson
        context['group_lessons'] = group_lessons
        
        return context
    
    def post(self, request):
        group_id = request.POST.get('group')
        lesson_id = request.POST.get('lesson')
        title = request.POST.get('title')
        description = request.POST.get('description')
        deadline_str = request.POST.get('deadline')
        
        if not deadline_str:
            messages.error(request, 'Muddati belgilash majburiy.')
            return redirect('homework:homework_assign')
        
        from datetime import datetime
        deadline = datetime.fromisoformat(deadline_str.replace('T', ' '))
        
        group = get_object_or_404(Group, pk=group_id, mentor=self.request.user)
        lesson = None
        
        if lesson_id:
            lesson = get_object_or_404(Lesson, pk=lesson_id, group=group)
        
        # Agar lesson belgilanmagan bo'lsa, guruhning oxirgi darsini ishlatish
        if not lesson:
            lesson = Lesson.objects.filter(group=group).order_by('-date', '-start_time').first()
            if not lesson:
                messages.error(request, 'Guruhda dars topilmadi. Avval dars yarating.')
                return redirect('homework:homework_assign')
        
        # Har bir talaba uchun homework yaratish
        created_count = 0
        for student in group.students.all():
            homework, created = Homework.objects.get_or_create(
                student=student,
                lesson=lesson,
                title=title,
                defaults={
                    'description': description,
                    'deadline': deadline
                }
            )
            if created:
                created_count += 1
        
        messages.success(request, f'{created_count} ta talabaga vazifa berildi.')
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
        queryset = Homework.objects.select_related('student', 'lesson', 'grade__mentor')
        
        # Rol bo'yicha filter
        if self.request.user.is_student:
            queryset = queryset.filter(student=self.request.user)
        elif self.request.user.is_mentor:
            queryset = queryset.filter(lesson__group__mentor=self.request.user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = (self.request.user.is_admin or 
                               self.request.user.is_manager or 
                               (self.request.user.is_mentor and 
                                hasattr(self.object.lesson, 'group') and 
                                self.object.lesson.group.mentor == self.request.user))
        context['today'] = timezone.now().date()
        return context


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


class HomeworkUpdateView(TailwindFormMixin, RoleRequiredMixin, UpdateView):
    """Homework tahrirlash"""
    model = Homework
    template_name = 'homework/homework_form.html'
    fields = ['lesson', 'title', 'description', 'file', 'link', 'code', 'deadline']
    allowed_roles = ['admin', 'manager', 'mentor']
    
    def get_queryset(self):
        queryset = Homework.objects.all()
        if self.request.user.is_mentor:
            queryset = queryset.filter(lesson__group__mentor=self.request.user)
        return queryset
    
    def get_success_url(self):
        return reverse_lazy('homework:homework_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Vazifa muvaffaqiyatli yangilandi.')
        return super().form_valid(form)


class HomeworkDeleteView(RoleRequiredMixin, DeleteView):
    """Homework o'chirish"""
    model = Homework
    template_name = 'homework/homework_confirm_delete.html'
    success_url = reverse_lazy('homework:homework_list')
    allowed_roles = ['admin', 'manager']
    
    def get_queryset(self):
        queryset = Homework.objects.all()
        if self.request.user.is_mentor:
            queryset = queryset.filter(lesson__group__mentor=self.request.user)
        return queryset
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Vazifa o\'chirildi.')
        return super().delete(request, *args, **kwargs)
