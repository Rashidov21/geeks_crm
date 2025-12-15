from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from .models import Course, Module, Topic, Group, GroupTransfer, Lesson, StudentProgress
from accounts.mixins import RoleRequiredMixin


class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    
    def get_queryset(self):
        return Course.objects.filter(is_active=True).select_related('branch')


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    
    def get_queryset(self):
        return Course.objects.prefetch_related('modules__topics', 'modules__topics__materials')


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
    
    def get_queryset(self):
        return Group.objects.filter(is_active=True).select_related('course', 'mentor', 'room')


class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group
    template_name = 'courses/group_detail.html'
    context_object_name = 'group'
    
    def get_queryset(self):
        return Group.objects.prefetch_related('students', 'lessons').select_related('course', 'mentor', 'room')


class LessonListView(LoginRequiredMixin, ListView):
    model = Lesson
    template_name = 'courses/lesson_list.html'
    context_object_name = 'lessons'
    
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
        return Lesson.objects.select_related('group', 'topic', 'mentor')


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


class GroupTransferCreateView(RoleRequiredMixin, CreateView):
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
