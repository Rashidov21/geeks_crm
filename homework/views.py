from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Homework, HomeworkGrade
from accounts.mixins import MentorRequiredMixin


class HomeworkListView(LoginRequiredMixin, ListView):
    model = Homework
    template_name = 'homework/homework_list.html'
    context_object_name = 'homeworks'
    
    def get_queryset(self):
        queryset = Homework.objects.select_related('student', 'lesson', 'lesson__group')
        if self.request.user.is_student:
            queryset = queryset.filter(student=self.request.user)
        elif self.request.user.is_mentor:
            queryset = queryset.filter(lesson__mentor=self.request.user)
        return queryset.order_by('-deadline', '-submitted_at')


class HomeworkCreateView(LoginRequiredMixin, CreateView):
    model = Homework
    template_name = 'homework/homework_form.html'
    fields = ['lesson', 'title', 'description', 'file', 'link', 'code', 'deadline']
    success_url = reverse_lazy('homework:homework_list')
    
    def form_valid(self, form):
        form.instance.student = self.request.user
        return super().form_valid(form)


class HomeworkDetailView(LoginRequiredMixin, DetailView):
    model = Homework
    template_name = 'homework/homework_detail.html'
    context_object_name = 'homework'
    
    def get_queryset(self):
        return Homework.objects.select_related('student', 'lesson', 'grade__mentor')


class HomeworkGradeView(MentorRequiredMixin, UpdateView):
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
