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
        context['total_exams'] = self.get_queryset().count()
        context['upcoming_exams'] = self.get_queryset().filter(date__gte=timezone.now().date()).count()
        
        if self.request.user.is_mentor:
            context['groups'] = Group.objects.filter(mentor=self.request.user, is_active=True)
        elif self.request.user.is_admin or self.request.user.is_manager:
            context['groups'] = Group.objects.filter(is_active=True)
            context['courses'] = Course.objects.filter(is_active=True)
        
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


class ExamResultsView(RoleRequiredMixin, TemplateView):
    """Imtihon natijalari (mentor/admin uchun)"""
    template_name = 'exams/exam_results.html'
    allowed_roles = ['admin', 'manager', 'mentor']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = get_object_or_404(Exam, pk=self.kwargs['pk'])
        
        results = ExamResult.objects.filter(exam=exam).select_related('student').order_by('-score')
        
        context['exam'] = exam
        context['results'] = results
        context['avg_score'] = results.aggregate(avg=Avg('score'))['avg'] or 0
        context['passed_count'] = results.filter(is_passed=True).count()
        context['total_count'] = results.count()
        
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
