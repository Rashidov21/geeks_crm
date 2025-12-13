from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.models import User
from courses.models import Lesson, Group


class Homework(models.Model):
    """
    Uy vazifalari
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='homeworks')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='homeworks',
                               limit_choices_to={'role': 'student'})
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)  # Student tomonidan yozilgan
    file = models.FileField(upload_to='homeworks/', blank=True, null=True)
    link = models.URLField(blank=True, null=True)  # GitHub, CodePen va hokazo
    code = models.TextField(blank=True, null=True)  # Kod matn shaklida
    submitted_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField()
    is_submitted = models.BooleanField(default=False)
    is_late = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Homework')
        verbose_name_plural = _('Homeworks')
        ordering = ['-deadline', '-submitted_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.lesson} - {self.title or 'No title'}"
    
    def save(self, *args, **kwargs):
        if self.submitted_at and self.deadline:
            if self.submitted_at > self.deadline:
                self.is_late = True
            else:
                self.is_late = False
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Deadline o'tib ketganmi?"""
        if not self.is_submitted:
            return timezone.now() > self.deadline
        return False


class HomeworkGrade(models.Model):
    """
    Uy vazifasi bahosi
    """
    homework = models.OneToOneField(Homework, on_delete=models.CASCADE, related_name='grade')
    mentor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='graded_homeworks', limit_choices_to={'role': 'mentor'})
    grade = models.IntegerField(default=0)  # 0-100 ball
    comment = models.TextField(blank=True, null=True)
    graded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Homework Grade')
        verbose_name_plural = _('Homework Grades')
        ordering = ['-graded_at']
    
    def __str__(self):
        return f"{self.homework} - {self.grade} ball"
    
    def get_grade_display(self):
        """Bahoni harf ko'rinishida"""
        if self.grade >= 90:
            return 'A'
        elif self.grade >= 80:
            return 'B'
        elif self.grade >= 70:
            return 'C'
        elif self.grade >= 60:
            return 'D'
        else:
            return 'F'
