from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from courses.models import Course, Group


class Exam(models.Model):
    """
    Imtihonlar
    """
    EXAM_TYPE_CHOICES = [
        ('test', 'Test'),
        ('written', 'Yozma'),
        ('practical', 'Amaliy'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='exams', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES, default='test')
    date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)  # Davomiyligi (daqiqa)
    max_score = models.IntegerField(default=100)  # Maksimal ball
    passing_score = models.FloatField(default=50.0)  # O'tish balli (guruh o'rtacha ballidan yuqori)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Exam')
        verbose_name_plural = _('Exams')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.title} - {self.course.name}"


class Question(models.Model):
    """
    Imtihon savollari
    """
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=[
        ('single_choice', 'Yagona tanlov'),
        ('multiple_choice', 'Ko\'p tanlov'),
        ('text', 'Matn'),
    ], default='single_choice')
    points = models.IntegerField(default=1)  # Savol balli
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')
        ordering = ['exam', 'order']
    
    def __str__(self):
        return f"{self.exam.title} - {self.question_text[:50]}..."


class Answer(models.Model):
    """
    Savol javoblari (variantlar)
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = _('Answer')
        verbose_name_plural = _('Answers')
        ordering = ['question', 'order']
    
    def __str__(self):
        return f"{self.question.question_text[:30]}... - {self.answer_text[:30]}..."


class ExamResult(models.Model):
    """
    Imtihon natijalari
    """
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_results',
                               limit_choices_to={'role': 'student'})
    score = models.FloatField(default=0.0)  # Olingan ball
    percentage = models.FloatField(default=0.0)  # Foiz
    is_passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Exam Result')
        verbose_name_plural = _('Exam Results')
        unique_together = ['exam', 'student']
        ordering = ['-score', '-submitted_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.exam.title} - {self.score} ball"
    
    def calculate_score(self, student_answers):
        """
        Ballni hisoblash
        student_answers: {question_id: [answer_ids]}
        """
        total_points = 0
        earned_points = 0
        
        for question in self.exam.questions.all():
            total_points += question.points
            
            if question.id in student_answers:
                student_answer_ids = student_answers[question.id]
                correct_answers = question.answers.filter(is_correct=True).values_list('id', flat=True)
                
                if question.question_type == 'single_choice':
                    # Yagona tanlov: to'g'ri javob bo'lishi kerak
                    if len(student_answer_ids) == 1 and student_answer_ids[0] in correct_answers:
                        earned_points += question.points
                elif question.question_type == 'multiple_choice':
                    # Ko'p tanlov: barcha to'g'ri javoblar tanlangan bo'lishi kerak
                    if set(student_answer_ids) == set(correct_answers):
                        earned_points += question.points
        
        self.score = earned_points
        if total_points > 0:
            self.percentage = (earned_points / total_points) * 100
        else:
            self.percentage = 0.0
        
        # O'tish balli: guruh o'rtacha ballidan yuqori bo'lishi kerak
        group_avg = ExamResult.objects.filter(
            exam=self.exam,
            exam__group=self.exam.group
        ).exclude(id=self.id).aggregate(
            avg_score=models.Avg('score')
        )['avg_score'] or 0
        
        if self.percentage > group_avg:
            self.is_passed = True
        else:
            self.is_passed = False
        
        self.save()
        return self.score


class StudentAnswer(models.Model):
    """
    O'quvchi javoblari
    """
    exam_result = models.ForeignKey(ExamResult, on_delete=models.CASCADE, related_name='student_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    selected_answers = models.ManyToManyField(Answer, related_name='student_selections')
    text_answer = models.TextField(blank=True, null=True)  # Matn javob uchun
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Student Answer')
        verbose_name_plural = _('Student Answers')
        unique_together = ['exam_result', 'question']
    
    def __str__(self):
        return f"{self.exam_result.student.username} - {self.question.question_text[:30]}..."
