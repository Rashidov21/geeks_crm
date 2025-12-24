from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse_lazy
import json
from .models import Course, Module, Topic, TopicMaterial, Group, GroupTransfer, Lesson, StudentProgress, Room
from accounts.models import User, Branch
from accounts.mixins import RoleRequiredMixin, TailwindFormMixin


class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Course.objects.select_related('branch')
        
        # Filterlar
        branch = self.request.GET.get('branch')
        if branch:
            queryset = queryset.filter(branch_id=branch)
        
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        else:
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['branches'] = Branch.objects.all()
        context['total_courses'] = Course.objects.count()
        context['active_courses'] = Course.objects.filter(is_active=True).count()
        
        # Stats for cards
        context['stats'] = [
            {'label': 'Jami kurslar', 'value': context['total_courses'], 'icon': 'fas fa-book', 'color': 'text-indigo-600'},
            {'label': 'Faol kurslar', 'value': context['active_courses'], 'icon': 'fas fa-check-circle', 'color': 'text-green-600'},
        ]
        
        # Permissions
        user = self.request.user
        context['can_create'] = user.is_superuser or (hasattr(user, 'is_admin') and user.is_admin) or (hasattr(user, 'is_manager') and user.is_manager)
        context['can_edit'] = context['can_create']
        context['can_delete'] = context['can_create']
        return context


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    
    def get_queryset(self):
        return Course.objects.prefetch_related('modules__topics', 'modules__topics__materials')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = Group.objects.filter(course=self.object, is_active=True)
        context['can_edit'] = self.request.user.is_admin or self.request.user.is_manager
        return context


class CourseCreateView(RoleRequiredMixin, CreateView):
    model = Course
    template_name = 'courses/course_form.html'
    fields = ['name', 'description', 'branch', 'duration_weeks', 'price']
    allowed_roles = ['admin', 'manager']
    
    def get_success_url(self):
        return reverse_lazy('courses:course_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Kurs muvaffaqiyatli yaratildi.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['branches'] = Branch.objects.all()
        return context


class CourseUpdateView(RoleRequiredMixin, UpdateView):
    model = Course
    template_name = 'courses/course_form.html'
    fields = ['name', 'description', 'branch', 'duration_weeks', 'price', 'is_active']
    allowed_roles = ['admin', 'manager']
    
    def get_success_url(self):
        return reverse_lazy('courses:course_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Kurs muvaffaqiyatli yangilandi.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['branches'] = Branch.objects.all()
        context['is_edit'] = True
        return context


class CourseDeleteView(RoleRequiredMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('courses:course_list')
    allowed_roles = ['admin', 'manager']
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Kurs o\'chirildi.')
        return super().delete(request, *args, **kwargs)


# ==================== MODULE VIEWS ====================

class ModuleCreateView(RoleRequiredMixin, View):
    allowed_roles = ['admin', 'manager']
    
    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        order = Module.objects.filter(course=course).count() + 1
        
        module = Module.objects.create(
            course=course,
            name=name,
            description=description,
            order=order
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'module_id': module.id, 'name': module.name})
        
        messages.success(request, 'Modul qo\'shildi.')
        return redirect('courses:course_detail', pk=course_id)


class ModuleUpdateView(RoleRequiredMixin, View):
    allowed_roles = ['admin', 'manager']
    
    def post(self, request, pk):
        module = get_object_or_404(Module, pk=pk)
        module.name = request.POST.get('name', module.name)
        module.description = request.POST.get('description', module.description)
        module.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Modul yangilandi.')
        return redirect('courses:course_detail', pk=module.course.pk)


class ModuleDeleteView(RoleRequiredMixin, View):
    allowed_roles = ['admin', 'manager']
    
    def post(self, request, pk):
        module = get_object_or_404(Module, pk=pk)
        course_id = module.course.pk
        module.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Modul o\'chirildi.')
        return redirect('courses:course_detail', pk=course_id)


# ==================== TOPIC VIEWS ====================

class TopicCreateView(RoleRequiredMixin, View):
    allowed_roles = ['admin', 'manager']
    
    def post(self, request, module_id):
        module = get_object_or_404(Module, pk=module_id)
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        duration = request.POST.get('duration_minutes', 90)
        order = Topic.objects.filter(module=module).count() + 1
        
        topic = Topic.objects.create(
            module=module,
            name=name,
            description=description,
            duration_minutes=duration,
            order=order
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'topic_id': topic.id, 'name': topic.name})
        
        messages.success(request, 'Mavzu qo\'shildi.')
        return redirect('courses:course_detail', pk=module.course.pk)


class TopicUpdateView(RoleRequiredMixin, View):
    allowed_roles = ['admin', 'manager']
    
    def post(self, request, pk):
        topic = get_object_or_404(Topic, pk=pk)
        topic.name = request.POST.get('name', topic.name)
        topic.description = request.POST.get('description', topic.description)
        topic.duration_minutes = request.POST.get('duration_minutes', topic.duration_minutes)
        topic.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Mavzu yangilandi.')
        return redirect('courses:course_detail', pk=topic.module.course.pk)


class TopicDeleteView(RoleRequiredMixin, View):
    allowed_roles = ['admin', 'manager']
    
    def post(self, request, pk):
        topic = get_object_or_404(Topic, pk=pk)
        course_id = topic.module.course.pk
        topic.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Mavzu o\'chirildi.')
        return redirect('courses:course_detail', pk=course_id)


class ModuleDetailView(LoginRequiredMixin, DetailView):
    model = Module
    template_name = 'courses/module_detail.html'
    context_object_name = 'module'
    
    def get_queryset(self):
        return Module.objects.prefetch_related('topics', 'topics__materials')


class TopicDetailView(LoginRequiredMixin, DetailView):
    model = Topic
    template_name = 'courses/topic_detail.html'
    context_object_name = 'topic'
    
    def get_queryset(self):
        return Topic.objects.prefetch_related('materials')


class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = 'courses/group_list.html'
    context_object_name = 'groups'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Group.objects.select_related('course', 'mentor', 'room')
        
        # Filterlar
        course = self.request.GET.get('course')
        if course:
            queryset = queryset.filter(course_id=course)
        
        mentor = self.request.GET.get('mentor')
        if mentor:
            queryset = queryset.filter(mentor_id=mentor)
        
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        else:
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.filter(is_active=True)
        context['mentors'] = User.objects.filter(role='mentor', is_active=True)
        context['total_groups'] = Group.objects.count()
        context['active_groups'] = Group.objects.filter(is_active=True).count()
        return context


class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group
    template_name = 'courses/group_detail.html'
    context_object_name = 'group'
    
    def get_queryset(self):
        return Group.objects.prefetch_related('students', 'lessons').select_related('course', 'mentor', 'room')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = self.request.user.is_admin or self.request.user.is_manager
        context['available_students'] = User.objects.filter(role='student', is_active=True).exclude(
            pk__in=self.object.students.values_list('pk', flat=True)
        )
        return context


class GroupCreateView(RoleRequiredMixin, CreateView):
    model = Group
    template_name = 'courses/group_form.html'
    fields = ['name', 'course', 'mentor', 'room', 'schedule_type', 'start_time', 'end_time', 'capacity']
    allowed_roles = ['admin', 'manager']
    
    def get_success_url(self):
        return reverse_lazy('courses:group_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Guruh muvaffaqiyatli yaratildi.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.filter(is_active=True)
        context['mentors'] = User.objects.filter(role='mentor', is_active=True)
        context['rooms'] = Room.objects.filter(is_active=True)
        return context


class GroupUpdateView(RoleRequiredMixin, UpdateView):
    model = Group
    template_name = 'courses/group_form.html'
    fields = ['name', 'course', 'mentor', 'room', 'schedule_type', 'start_time', 'end_time', 'capacity', 'is_active']
    allowed_roles = ['admin', 'manager']
    
    def get_success_url(self):
        return reverse_lazy('courses:group_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Guruh muvaffaqiyatli yangilandi.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.filter(is_active=True)
        context['mentors'] = User.objects.filter(role='mentor', is_active=True)
        context['rooms'] = Room.objects.filter(is_active=True)
        context['is_edit'] = True
        return context


class GroupDeleteView(RoleRequiredMixin, DeleteView):
    model = Group
    template_name = 'courses/group_confirm_delete.html'
    success_url = reverse_lazy('courses:group_list')
    allowed_roles = ['admin', 'manager']
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Guruh o\'chirildi.')
        return super().delete(request, *args, **kwargs)


class GroupStudentsView(RoleRequiredMixin, View):
    allowed_roles = ['admin', 'manager']
    
    def post(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        action = request.POST.get('action')
        student_id = request.POST.get('student_id')
        
        if action == 'add' and student_id:
            student = get_object_or_404(User, pk=student_id, role='student')
            group.students.add(student)
            messages.success(request, f'{student.get_full_name()} guruhga qo\'shildi.')
        elif action == 'remove' and student_id:
            student = get_object_or_404(User, pk=student_id, role='student')
            group.students.remove(student)
            messages.success(request, f'{student.get_full_name()} guruhdan chiqarildi.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('courses:group_detail', pk=pk)


class LessonListView(LoginRequiredMixin, ListView):
    model = Lesson
    template_name = 'courses/lesson_list.html'
    context_object_name = 'lessons'
    paginate_by = 30
    
    def get_queryset(self):
        queryset = Lesson.objects.select_related('group', 'topic', 'mentor')
        if self.request.user.is_student:
            queryset = queryset.filter(group__students=self.request.user)
        elif self.request.user.is_mentor:
            queryset = queryset.filter(mentor=self.request.user)
        return queryset.order_by('-date', '-start_time')


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = 'courses/lesson_detail.html'
    context_object_name = 'lesson'
    
    def get_queryset(self):
        return Lesson.objects.select_related('group', 'group__mentor', 'topic')


class StudentProgressView(LoginRequiredMixin, DetailView):
    model = StudentProgress
    template_name = 'courses/progress.html'
    context_object_name = 'progress'
    
    def get_object(self):
        progress, created = StudentProgress.objects.get_or_create(
            student=self.request.user,
            course_id=self.kwargs.get('course_id')
        )
        if created or not progress.progress_percentage:
            progress.calculate_progress()
        return progress


class GroupTransferCreateView(TailwindFormMixin, RoleRequiredMixin, CreateView):
    """
    O'quvchini bir guruhdan boshqasiga ko'chirish
    """
    model = GroupTransfer
    template_name = 'courses/group_transfer_form.html'
    fields = ['student', 'from_group', 'to_group', 'reason', 'notes']
    allowed_roles = ['admin', 'manager']
    
    def form_valid(self, form):
        form.instance.transferred_by = self.request.user
        messages.success(self.request, f"O'quvchi {form.instance.from_group.name} dan {form.instance.to_group.name} ga muvaffaqiyatli ko'chirildi.")
        return super().form_valid(form)


class GroupTransferListView(RoleRequiredMixin, ListView):
    """
    Guruh ko'chirishlar tarixi
    """
    model = GroupTransfer
    template_name = 'courses/group_transfer_list.html'
    context_object_name = 'transfers'
    allowed_roles = ['admin', 'manager']
    
    def get_queryset(self):
        queryset = GroupTransfer.objects.select_related('student', 'from_group', 'to_group', 'transferred_by')
        
        # Filtrlash
        student_id = self.request.GET.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset.order_by('-transferred_at')
