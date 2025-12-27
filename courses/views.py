from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.db.models import Count
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
        
        # Studentlar uchun faqat o'zi o'qiyotgan kurslar
        if self.request.user.is_student:
            student_groups = Group.objects.filter(students=self.request.user, is_active=True)
            course_ids = student_groups.values_list('course_id', flat=True).distinct()
            queryset = queryset.filter(id__in=course_ids)
        # Mentorlar uchun faqat o'z guruhlaridagi kurslar
        elif self.request.user.is_mentor:
            mentor_groups = Group.objects.filter(mentor=self.request.user, is_active=True)
            course_ids = mentor_groups.values_list('course_id', flat=True).distinct()
            queryset = queryset.filter(id__in=course_ids)
        
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
        queryset = Course.objects.prefetch_related('modules__topics', 'modules__topics__materials')
        
        # Studentlar uchun faqat o'zi o'qiyotgan kurslar
        if self.request.user.is_student:
            student_courses = Group.objects.filter(
                students=self.request.user,
                is_active=True
            ).values_list('course_id', flat=True).distinct()
            queryset = queryset.filter(id__in=student_courses)
        # Mentorlar uchun faqat o'z guruhlaridagi kurslar
        elif self.request.user.is_mentor:
            mentor_courses = Group.objects.filter(
                mentor=self.request.user,
                is_active=True
            ).values_list('course_id', flat=True).distinct()
            queryset = queryset.filter(id__in=mentor_courses)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Studentlar uchun faqat o'zi o'qiyotgan guruhlar
        if self.request.user.is_student:
            groups = Group.objects.filter(course=self.object, students=self.request.user, is_active=True)
        else:
            groups = Group.objects.filter(course=self.object, is_active=True)
        
        context['groups'] = groups
        
        # Kurs bo'yicha barcha darslar (barcha guruhlardan)
        context['lessons'] = Lesson.objects.filter(
            group__course=self.object,
            group__in=groups
        ).select_related('group', 'topic').order_by('-date', '-start_time')[:20]  # Oxirgi 20 ta dars
        
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
    allowed_roles = ['admin', 'manager', 'mentor']
    
    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        
        # Mentorlar uchun tekshiruv - faqat o'z guruhlaridagi kurslar
        if request.user.is_mentor:
            from django.core.exceptions import PermissionDenied
            mentor_courses = Group.objects.filter(
                mentor=request.user,
                is_active=True
            ).values_list('course_id', flat=True).distinct()
            if course.id not in mentor_courses:
                raise PermissionDenied("Siz bu kurs uchun modul qo'sha olmaysiz")
        
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
    allowed_roles = ['admin', 'manager', 'mentor']
    
    def post(self, request, pk):
        module = get_object_or_404(Module, pk=pk)
        
        # Mentorlar uchun tekshiruv - faqat o'z guruhlaridagi kurslar
        if request.user.is_mentor:
            from django.core.exceptions import PermissionDenied
            mentor_courses = Group.objects.filter(
                mentor=request.user,
                is_active=True
            ).values_list('course_id', flat=True).distinct()
            if module.course.id not in mentor_courses:
                raise PermissionDenied("Siz bu kurs uchun modul tahrirlay olmaysiz")
        
        module.name = request.POST.get('name', module.name)
        module.description = request.POST.get('description', module.description)
        module.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Modul yangilandi.')
        return redirect('courses:course_detail', pk=module.course.pk)


class ModuleDeleteView(RoleRequiredMixin, View):
    allowed_roles = ['admin', 'manager', 'mentor']
    
    def post(self, request, pk):
        module = get_object_or_404(Module, pk=pk)
        
        # Mentorlar uchun tekshiruv - faqat o'z guruhlaridagi kurslar
        if request.user.is_mentor:
            from django.core.exceptions import PermissionDenied
            mentor_courses = Group.objects.filter(
                mentor=request.user,
                is_active=True
            ).values_list('course_id', flat=True).distinct()
            if module.course.id not in mentor_courses:
                raise PermissionDenied("Siz bu kurs uchun modul o'chira olmaysiz")
        
        course_id = module.course.pk
        module.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Modul o\'chirildi.')
        return redirect('courses:course_detail', pk=course_id)


# ==================== TOPIC VIEWS ====================

class TopicCreateView(RoleRequiredMixin, View):
    allowed_roles = ['admin', 'manager', 'mentor']
    
    def post(self, request, module_id):
        module = get_object_or_404(Module, pk=module_id)
        
        # Mentorlar uchun tekshiruv - faqat o'z guruhlaridagi kurslar
        if request.user.is_mentor:
            from django.core.exceptions import PermissionDenied
            mentor_courses = Group.objects.filter(
                mentor=request.user,
                is_active=True
            ).values_list('course_id', flat=True).distinct()
            if module.course.id not in mentor_courses:
                raise PermissionDenied("Siz bu kurs uchun mavzu qo'sha olmaysiz")
        
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
    allowed_roles = ['admin', 'manager', 'mentor']
    
    def post(self, request, pk):
        topic = get_object_or_404(Topic, pk=pk)
        
        # Mentorlar uchun tekshiruv - faqat o'z guruhlaridagi kurslar
        if request.user.is_mentor:
            from django.core.exceptions import PermissionDenied
            mentor_courses = Group.objects.filter(
                mentor=request.user,
                is_active=True
            ).values_list('course_id', flat=True).distinct()
            if topic.module.course.id not in mentor_courses:
                raise PermissionDenied("Siz bu kurs uchun mavzu tahrirlay olmaysiz")
        
        topic.name = request.POST.get('name', topic.name)
        topic.description = request.POST.get('description', topic.description)
        topic.duration_minutes = request.POST.get('duration_minutes', topic.duration_minutes)
        topic.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Mavzu yangilandi.')
        return redirect('courses:course_detail', pk=topic.module.course.pk)


class TopicDeleteView(RoleRequiredMixin, View):
    allowed_roles = ['admin', 'manager', 'mentor']
    
    def post(self, request, pk):
        topic = get_object_or_404(Topic, pk=pk)
        
        # Mentorlar uchun tekshiruv - faqat o'z guruhlaridagi kurslar
        if request.user.is_mentor:
            from django.core.exceptions import PermissionDenied
            mentor_courses = Group.objects.filter(
                mentor=request.user,
                is_active=True
            ).values_list('course_id', flat=True).distinct()
            if topic.module.course.id not in mentor_courses:
                raise PermissionDenied("Siz bu kurs uchun mavzu o'chira olmaysiz")
        
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get lessons related to this topic for mentor's groups
        if self.request.user.is_mentor:
            mentor_groups = Group.objects.filter(mentor=self.request.user, is_active=True)
            context['lessons'] = Lesson.objects.filter(
                topic=self.object,
                group__in=mentor_groups
            ).select_related('group').order_by('-date', '-start_time')[:20]
            context['can_edit_lessons'] = True
        elif self.request.user.is_admin or self.request.user.is_manager:
            context['lessons'] = Lesson.objects.filter(
                topic=self.object
            ).select_related('group').order_by('-date', '-start_time')[:20]
            context['can_edit_lessons'] = True
        else:
            context['lessons'] = []
            context['can_edit_lessons'] = False
        
        return context


class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = 'courses/group_list.html'
    context_object_name = 'groups'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Group.objects.select_related('course', 'mentor', 'room')
        
        # Studentlar uchun faqat o'zi o'qiyotgan guruhlar
        if self.request.user.is_student:
            queryset = queryset.filter(students=self.request.user)
        # Mentorlar uchun faqat o'z guruhlari
        elif self.request.user.is_mentor:
            queryset = queryset.filter(mentor=self.request.user)
        
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
        queryset = Group.objects.select_related('course', 'mentor', 'room').prefetch_related('students', 'lessons')
        
        # Studentlar uchun faqat o'zi o'qiyotgan guruhlar
        if self.request.user.is_student:
            queryset = queryset.filter(students=self.request.user)
        # Mentorlar uchun faqat o'z guruhlari
        elif self.request.user.is_mentor:
            queryset = queryset.filter(mentor=self.request.user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Admin, Manager va o'z guruhlarini boshqaruvchi mentorlar uchun tahrirlash ruxsati
        user = self.request.user
        # Mentorlar guruhni tahrirlay olmaydi, faqat o'quvchi qo'sha oladi
        context['can_edit'] = (
            user.is_admin or 
            user.is_manager
        )
        # Mentorlar o'z guruhlariga o'quvchi qo'sha oladi
        context['can_add_students'] = (
            user.is_admin or 
            user.is_manager or 
            (user.is_mentor and self.object.mentor == user)
        )
        context['available_students'] = User.objects.filter(role='student', is_active=True).exclude(
            pk__in=self.object.students.values_list('pk', flat=True)
        )
        
        # Student data with points and ratings for tabs
        from gamification.models import StudentPoints, GroupRanking
        student_data = []
        for student in self.object.students.all().order_by('first_name', 'last_name'):
            # Get or create student points and calculate
            student_points, created = StudentPoints.objects.get_or_create(
                student=student,
                group=self.object
            )
            if created or not student_points.total_points:
                student_points.calculate_total_points()
            
            # Get ranking
            ranking = GroupRanking.objects.filter(
                group=self.object,
                student=student
            ).first()
            
            student_data.append({
                'student': student,
                'total_points': student_points.total_points,
                'rank': ranking.rank if ranking else None,
            })
        
        # Sort by points descending for ranking tab
        student_data_sorted = sorted(student_data, key=lambda x: x['total_points'], reverse=True)
        for idx, data in enumerate(student_data_sorted, 1):
            if data['rank'] is None:
                data['rank'] = idx
        
        context['student_data'] = student_data
        context['student_data_sorted'] = student_data_sorted
        
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


class GroupAddStudentView(LoginRequiredMixin, TemplateView):
    """
    Guruhga o'quvchi qo'shish sahifasi
    Admin, Manager va o'z guruhlarini boshqaruvchi mentorlar uchun
    """
    template_name = 'courses/group_add_student.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Ruxsatni tekshirish
        pk = kwargs.get('pk')
        group = get_object_or_404(Group, pk=pk)
        
        user = request.user
        if not (user.is_admin or user.is_manager or (user.is_mentor and group.mentor == user)):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Sizga bu guruhga o'quvchi qo'shish ruxsati yo'q")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = get_object_or_404(Group, pk=self.kwargs['pk'])
        context['group'] = group
        
        # 1. Aktiv studentlar (guruhda bo'lmagan)
        context['available_students'] = User.objects.filter(
            role='student', 
            is_active=True
        ).exclude(
            pk__in=group.students.values_list('pk', flat=True)
        ).order_by('first_name', 'last_name')
        
        # 2. Guruhi yo'q studentlar (hech qanday guruhda bo'lmagan)
        context['students_without_group'] = User.objects.filter(
            role='student',
            is_active=True
        ).exclude(
            pk__in=group.students.values_list('pk', flat=True)
        ).annotate(
            group_count=Count('student_groups')
        ).filter(
            group_count=0
        ).order_by('first_name', 'last_name')
        
        # 3. Lidlar (sinov darsiga yozilgan yoki qabul qilingan, hali studentga aylantirilmagan)
        from crm.models import Lead, LeadStatus
        
        trial_statuses = LeadStatus.objects.filter(
            code__in=['trial_registered', 'trial_attended', 'enrolled']
        )
        
        context['available_leads'] = Lead.objects.filter(
            status__in=trial_statuses,
            converted_student__isnull=True  # Hali studentga aylantirilmagan
        ).exclude(
            phone__in=group.students.values_list('phone', flat=True)
        ).select_related('status', 'interested_course').order_by('-created_at')[:50]
        
        return context
    
    def post(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        student_id = request.POST.get('student_id')
        
        if student_id:
            student = get_object_or_404(User, pk=student_id, role='student')
            if student not in group.students.all():
                group.students.add(student)
                messages.success(request, f'{student.get_full_name()} guruhga qo\'shildi.')
                return redirect('courses:group_detail', pk=pk)
            else:
                messages.warning(request, f'{student.get_full_name()} allaqachon guruhda.')
        else:
            messages.error(request, 'Iltimos, o\'quvchini tanlang.')
        
        return redirect('courses:group_add_student', pk=pk)


class ConvertLeadToStudentView(LoginRequiredMixin, View):
    """
    Leadni Studentga aylantirish va guruhga qo'shish
    """
    def dispatch(self, request, *args, **kwargs):
        # Ruxsatni tekshirish
        pk = kwargs.get('pk')
        group = get_object_or_404(Group, pk=pk)
        
        user = request.user
        if not (user.is_admin or user.is_manager or (user.is_mentor and group.mentor == user)):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Sizga bu guruhga o'quvchi qo'shish ruxsati yo'q")
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        lead_id = request.POST.get('lead_id')
        
        if lead_id:
            from crm.models import Lead
            from crm.signals import convert_lead_to_student
            
            lead = get_object_or_404(Lead, pk=lead_id)
            student = convert_lead_to_student(lead, group)
            
            if student:
                messages.success(request, f'{lead.name} studentga aylantirildi va {group.name} guruhiga qo\'shildi.')
                return redirect('courses:group_detail', pk=pk)
        
        messages.error(request, 'Xato: Lid topilmadi.')
        return redirect('courses:group_add_student', pk=pk)


class GroupStudentsView(LoginRequiredMixin, View):
    """
    Guruhdan o'quvchi chiqarish (AJAX uchun)
    Admin, Manager va o'z guruhlarini boshqaruvchi mentorlar uchun
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Ruxsatni tekshirish
        pk = kwargs.get('pk')
        group = get_object_or_404(Group, pk=pk)
        
        user = request.user
        if not (user.is_admin or user.is_manager or (user.is_mentor and group.mentor == user)):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Sizga bu guruhdan o'quvchi chiqarish ruxsati yo'q")
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        action = request.POST.get('action')
        student_id = request.POST.get('student_id')
        
        if action == 'remove' and student_id:
            student = get_object_or_404(User, pk=student_id, role='student')
            group.students.remove(student)
            messages.success(request, f'{student.get_full_name()} guruhdan chiqarildi.')
        else:
            messages.error(request, 'Xato: O\'quvchi tanlanmagan yoki noto\'g\'ri amal.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('courses:group_detail', pk=pk)


class LessonListView(LoginRequiredMixin, ListView):
    model = Lesson
    template_name = 'courses/lesson_list.html'
    context_object_name = 'lessons'
    paginate_by = 30
    
    def get_queryset(self):
        queryset = Lesson.objects.select_related('group', 'group__mentor', 'topic')
        if self.request.user.is_student:
            queryset = queryset.filter(group__students=self.request.user)
        elif self.request.user.is_mentor:
            queryset = queryset.filter(group__mentor=self.request.user)
        
        # Group filter
        group_id = self.request.GET.get('group')
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        
        return queryset.order_by('-date', '-start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available groups for filter
        if self.request.user.is_student:
            groups = Group.objects.filter(students=self.request.user, is_active=True)
        elif self.request.user.is_mentor:
            groups = Group.objects.filter(mentor=self.request.user, is_active=True)
        else:
            groups = Group.objects.filter(is_active=True)
        
        context['groups'] = groups.order_by('course__name', 'name')
        context['selected_group'] = self.request.GET.get('group')
        
        return context


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = 'courses/lesson_detail.html'
    context_object_name = 'lesson'
    
    def get_queryset(self):
        return Lesson.objects.select_related('group', 'group__mentor', 'topic').prefetch_related('topic__materials')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get previous and next lessons in the same group
        lesson_obj = context.get('lesson') or self.object
        group_lessons = list(Lesson.objects.filter(group=lesson_obj.group).select_related('topic', 'group').order_by('date', 'start_time'))
        try:
            current_index = next(i for i, lesson in enumerate(group_lessons) if lesson.id == lesson_obj.id)
            if current_index > 0:
                context['prev_lesson'] = group_lessons[current_index - 1]
            if current_index < len(group_lessons) - 1:
                context['next_lesson'] = group_lessons[current_index + 1]
        except StopIteration:
            pass
        return context


class LessonUpdateView(LoginRequiredMixin, View):
    """Lesson tahrirlash - mentor va admin uchun"""
    
    def dispatch(self, request, *args, **kwargs):
        lesson = get_object_or_404(Lesson, pk=kwargs.get('pk'))
        
        # Permission check
        if request.user.is_mentor:
            if lesson.group.mentor != request.user:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("Siz bu darsni tahrirlay olmaysiz")
        elif not (request.user.is_admin or request.user.is_manager):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Sizga bu funksiya uchun ruxsat yo'q")
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, pk):
        from .forms import LessonForm
        lesson = get_object_or_404(Lesson, pk=pk)
        
        # Use form for validation and CKEditor support
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Dars muvaffaqiyatli yangilandi'})
            else:
                messages.success(request, 'Dars muvaffaqiyatli yangilandi')
                return redirect('courses:lesson_detail', pk=lesson.pk)
        else:
            # Form validation failed
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Form validatsiyadan o\'tmadi', 'errors': form.errors})
            else:
                messages.error(request, 'Form validatsiyadan o\'tmadi')
                return redirect('courses:topic_detail', pk=lesson.topic.pk if lesson.topic else 0)


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
    paginate_by = 25
    
    def get_queryset(self):
        queryset = GroupTransfer.objects.select_related('student', 'from_group', 'to_group', 'transferred_by')
        
        # Filtrlash
        student_id = self.request.GET.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset.order_by('-transferred_at')
