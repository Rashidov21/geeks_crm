from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Exam, ExamResult, Question, StudentAnswer


class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'
    
    def get_queryset(self):
        queryset = Exam.objects.filter(is_active=True).select_related('course', 'group')
        if self.request.user.is_student:
            queryset = queryset.filter(group__students=self.request.user)
        return queryset.order_by('-date')


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
