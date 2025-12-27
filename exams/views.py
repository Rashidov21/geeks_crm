from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse_lazy
from django.db.models import Avg, Count
from .models import Exam, ExamResult, Question, StudentAnswer, Answer
from accounts.mixins import RoleRequiredMixin, MentorRequiredMixin, TailwindFormMixin
from courses.models import Course, Group


class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Exam.objects.select_related('course', 'group')
        
        if self.request.user.is_student:
            queryset = queryset.filter(group__students=self.request.user, is_active=True)
        elif self.request.user.is_mentor:
            queryset = queryset.filter(group__mentor=self.request.user)
        
        # Filterlar
        course_id = self.request.GET.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        group_id = self.request.GET.get('group')
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        
        return queryset.order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        total_exams = queryset.count()
        upcoming_exams = queryset.filter(date__gte=timezone.now().date()).count()
        completed_exams = queryset.filter(date__lt=timezone.now().date()).count()
        
        # For students, add exam results
        if self.request.user.is_student:
            from .models import ExamResult
            exam_results = {}
            for exam in queryset:
                result = ExamResult.objects.filter(
                    exam=exam,
                    student=self.request.user
                ).first()
                exam_results[exam.id] = result
            context['exam_results'] = exam_results
            
            # Calculate stats
            passed_exams = sum(1 for r in exam_results.values() if r and r.is_passed)
            context['passed_exams'] = passed_exams
        
        # Stats for cards
        context['stats'] = [
            {'label': 'Jami imtihonlar', 'value': total_exams, 'icon': 'fas fa-file-alt', 'color': 'text-rose-600'},
            {'label': 'Kutilayotgan', 'value': upcoming_exams, 'icon': 'fas fa-calendar', 'color': 'text-blue-600'},
            {'label': 'O\'tgan', 'value': completed_exams, 'icon': 'fas fa-check-circle', 'color': 'text-green-600'},
        ]
        
        if self.request.user.is_student:
            context['stats'].append({'label': 'O\'tdi', 'value': context.get('passed_exams', 0), 'icon': 'fas fa-trophy', 'color': 'text-yellow-600'})
        
        if self.request.user.is_mentor:
            context['groups'] = Group.objects.filter(mentor=self.request.user, is_active=True)
        elif self.request.user.is_admin or self.request.user.is_manager:
            context['groups'] = Group.objects.filter(is_active=True)
            context['courses'] = Course.objects.filter(is_active=True)
        elif self.request.user.is_student:
            context['groups'] = Group.objects.filter(students=self.request.user, is_active=True)
        
        # Permissions
        user = self.request.user
        context['can_create'] = user.is_superuser or (hasattr(user, 'is_admin') and user.is_admin) or (hasattr(user, 'is_manager') and user.is_manager) or (hasattr(user, 'is_mentor') and user.is_mentor)
        context['can_edit'] = context['can_create']
        context['can_delete'] = user.is_superuser or (hasattr(user, 'is_admin') and user.is_admin) or (hasattr(user, 'is_manager') and user.is_manager)
        
        return context


class ExamDetailView(LoginRequiredMixin, DetailView):
    model = Exam
    template_name = 'exams/exam_detail.html'
    context_object_name = 'exam'
    
    def get_queryset(self):
        return Exam.objects.prefetch_related('questions__answers').select_related('course', 'group')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_student:
            context['result'] = ExamResult.objects.filter(
                exam=self.object,
                student=self.request.user
            ).first()
        
        # Permissions
        user = self.request.user
        context['can_edit'] = (user.is_superuser or 
                               user.is_admin or 
                               user.is_manager or
                               (user.is_mentor and 
                                self.object.group and 
                                self.object.group.mentor == user))
        return context


class ExamTakeView(LoginRequiredMixin, CreateView):
    template_name = 'exams/exam_take.html'
    
    def get(self, request, *args, **kwargs):
        exam = get_object_or_404(Exam, pk=kwargs['pk'], is_active=True)
        
        # Check if already taken
        result = ExamResult.objects.filter(exam=exam, student=request.user).first()
        if result and result.submitted_at:
            messages.warning(request, 'Siz bu imtihonni allaqachon topshirdingiz.')
            return redirect('exams:exam_result', pk=result.pk)
        
        # Create or get result
        if not result:
            result = ExamResult.objects.create(exam=exam, student=request.user)
        
        context = {
            'exam': exam,
            'result': result,
            'questions': exam.questions.all().prefetch_related('answers'),
        }
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        exam = get_object_or_404(Exam, pk=kwargs['pk'])
        result = ExamResult.objects.get(exam=exam, student=request.user)
        
        # Process answers
        student_answers = {}
        for key, value in request.POST.items():
            if key.startswith('question_'):
                question_id = int(key.split('_')[1])
                if question_id not in student_answers:
                    student_answers[question_id] = []
                if isinstance(value, list):
                    student_answers[question_id].extend([int(v) for v in value])
                else:
                    student_answers[question_id].append(int(value))
        
        # Save student answers
        for question_id, answer_ids in student_answers.items():
            question = Question.objects.get(pk=question_id)
            student_answer, created = StudentAnswer.objects.get_or_create(
                exam_result=result,
                question=question
            )
            student_answer.selected_answers.set(answer_ids)
        
        # Calculate score
        result.calculate_score(student_answers)
        result.submitted_at = timezone.now()
        result.save()
        
        messages.success(request, 'Imtihon muvaffaqiyatli topshirildi!')
        return redirect('exams:exam_result', pk=result.pk)


class ExamResultView(LoginRequiredMixin, DetailView):
    model = ExamResult
    template_name = 'exams/exam_result.html'
    context_object_name = 'result'
    
    def get_queryset(self):
        return ExamResult.objects.prefetch_related(
            'student_answers__question',
            'student_answers__selected_answers'
        ).select_related('exam', 'student')


class ExamCreateView(RoleRequiredMixin, CreateView):
    """Imtihon yaratish"""
    model = Exam
    template_name = 'exams/exam_form.html'
    fields = ['title', 'course', 'group', 'date', 'duration_minutes', 'passing_score', 'description']
    allowed_roles = ['admin', 'manager', 'mentor']
    
    def get_success_url(self):
        return reverse_lazy('exams:exam_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Imtihon muvaffaqiyatli yaratildi.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_mentor:
            context['groups'] = Group.objects.filter(mentor=self.request.user, is_active=True)
        else:
            context['groups'] = Group.objects.filter(is_active=True)
        context['courses'] = Course.objects.filter(is_active=True)
        return context


class ExamUpdateView(RoleRequiredMixin, UpdateView):
    """Imtihonni tahrirlash"""
    model = Exam
    template_name = 'exams/exam_form.html'
    fields = ['title', 'course', 'group', 'date', 'duration_minutes', 'passing_score', 'description', 'is_active']
    allowed_roles = ['admin', 'manager', 'mentor']
    
    def get_success_url(self):
        return reverse_lazy('exams:exam_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Imtihon muvaffaqiyatli yangilandi.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_mentor:
            context['groups'] = Group.objects.filter(mentor=self.request.user, is_active=True)
        else:
            context['groups'] = Group.objects.filter(is_active=True)
        context['courses'] = Course.objects.filter(is_active=True)
        context['is_edit'] = True
        return context


class ExamDeleteView(RoleRequiredMixin, DeleteView):
    """Imtihonni o'chirish"""
    model = Exam
    template_name = 'exams/exam_confirm_delete.html'
    success_url = reverse_lazy('exams:exam_list')
    allowed_roles = ['admin', 'manager']
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Imtihon o\'chirildi.')
        return super().delete(request, *args, **kwargs)


class ExamResultsView(LoginRequiredMixin, TemplateView):
    """Imtihon natijalari (student/mentor/admin uchun)"""
    template_name = 'exams/exam_results.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user has permission to view results"""
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        # Allow admin, manager, mentor, and students
        if not (request.user.is_admin or request.user.is_manager or 
                request.user.is_mentor or request.user.is_student):
            messages.error(request, 'Sizda bu sahifaga kirish huquqi yo\'q.')
            return redirect('exams:exam_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = get_object_or_404(Exam, pk=self.kwargs['pk'])
        
        # Get results - filter by group if student
        if self.request.user.is_student:
            # Students see only their group's results
            if exam.group and self.request.user in exam.group.students.all():
                results = ExamResult.objects.filter(
                    exam=exam,
                    student__in=exam.group.students.all()
                ).select_related('student').order_by('-score')
            else:
                # If not in group, show only their own result
                results = ExamResult.objects.filter(
                    exam=exam,
                    student=self.request.user
                ).select_related('student').order_by('-score')
        else:
            # Admin/Manager/Mentor see all results
            results = ExamResult.objects.filter(exam=exam).select_related('student').order_by('-score')
        
        # Calculate student's position
        student_rank = None
        student_result = None
        if self.request.user.is_student:
            try:
                student_result = results.get(student=self.request.user)
                # Calculate rank (1-based)
                better_results = results.filter(score__gt=student_result.score).count()
                student_rank = better_results + 1
            except ExamResult.DoesNotExist:
                pass
        
        # Motivational messages
        motivational_message = None
        if student_result and self.request.user.is_student:
            percentage = student_result.percentage or 0
            if percentage >= 90:
                motivational_message = "🎉 Ajoyib! Siz eng yaxshi natijalardan birini ko'rsatdingiz! Davom eting!"
            elif percentage >= 80:
                motivational_message = "👍 Yaxshi ish qildingiz! Biroz ko'proq harakat qilsangiz, eng yaxshilardan bo'lasiz!"
            elif percentage >= 70:
                motivational_message = "💪 Yaxshi! Harakat qilayapsiz. Keyingi marta yanada yaxshi natija olishga harakat qiling!"
            elif percentage >= 60:
                motivational_message = "📚 O'tdingiz! Lekin yanada yaxshi natija uchun ko'proq o'qish kerak. Qo'yib bering!"
            elif student_result.is_passed:
                motivational_message = "✅ O'tdingiz! Lekin yaxshilash uchun ko'proq harakat qilish kerak."
            else:
                motivational_message = "📖 Kechirasiz, o'ta olmadingiz. Lekin qo'yib bermang! Ko'proq o'qib, keyingi marta yaxshiroq natija ko'rsating!"
        
        context['exam'] = exam
        context['results'] = results
        context['avg_score'] = results.aggregate(avg=Avg('score'))['avg'] or 0
        context['passed_count'] = results.filter(is_passed=True).count()
        context['total_count'] = results.count()
        context['student_rank'] = student_rank
        context['student_result'] = student_result
        context['motivational_message'] = motivational_message
        context['is_student_view'] = self.request.user.is_student
        
        return context


class ExamResultEntryView(RoleRequiredMixin, TemplateView):
    """Natijalarni manual kiritish"""
    template_name = 'exams/exam_result_entry.html'
    allowed_roles = ['admin', 'manager', 'mentor']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = get_object_or_404(Exam, pk=self.kwargs['pk'])
        
        # Guruh talabalari
        students = exam.group.students.all() if exam.group else []
        
        # Mavjud natijalar
        existing_results = {r.student_id: r for r in ExamResult.objects.filter(exam=exam)}
        
        student_data = []
        for student in students:
            student_data.append({
                'student': student,
                'result': existing_results.get(student.id)
            })
        
        context['exam'] = exam
        context['student_data'] = student_data
        return context
    
    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        
        student_ids = request.POST.getlist('student_ids')
        scores = request.POST.getlist('scores')
        
        for i, student_id in enumerate(student_ids):
            if scores[i]:
                score = int(scores[i])
                result, created = ExamResult.objects.update_or_create(
                    exam=exam,
                    student_id=student_id,
                    defaults={
                        'score': score,
                        'is_passed': score >= exam.passing_score,
                        'submitted_at': timezone.now()
                    }
                )
        
        messages.success(request, 'Natijalar saqlandi.')
        return redirect('exams:exam_results', pk=pk)
