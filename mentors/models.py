from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.models import User
from courses.models import Group, Lesson
from homework.models import Homework
from attendance.models import Attendance


class LessonQuality(models.Model):
    """
    Dars sifati (o'quvchilar bahosi 1-5)
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quality_ratings')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_ratings',
                               limit_choices_to={'role': 'student'})
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 ball
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Lesson Quality')
        verbose_name_plural = _('Lesson Qualities')
        unique_together = ['lesson', 'student']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lesson', 'rating']),
            models.Index(fields=['student', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.lesson} - {self.student.username} - {self.rating} ball"


class ParentFeedback(models.Model):
    """
    Ota-onalar feedbacklari
    """
    FEEDBACK_TYPE_CHOICES = [
        ('positive', 'Ijobiy'),
        ('negative', 'Salbiy'),
        ('neutral', 'Neytral'),
        ('suggestion', 'Taklif'),
    ]
    
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_feedbacks',
                              limit_choices_to={'role': 'mentor'})
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedbacks',
                              limit_choices_to={'role': 'parent'})
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_feedbacks',
                               limit_choices_to={'role': 'student'})
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES, default='neutral')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Parent Feedback')
        verbose_name_plural = _('Parent Feedbacks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mentor', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.parent.username} - {self.mentor.username} - {self.get_feedback_type_display()}"


class MonthlyReport(models.Model):
    """
    Mentor oylik hisobotlari
    """
    CHARACTER_CHOICES = [
        ('excellent', 'A\'lo'),
        ('good', 'Yaxshi'),
        ('satisfactory', 'Qoniqarli'),
        ('needs_improvement', 'Yaxshilash kerak'),
    ]
    
    ATTENDANCE_CHOICES = [
        ('excellent', 'A\'lo (95-100%)'),
        ('good', 'Yaxshi (85-94%)'),
        ('satisfactory', 'Qoniqarli (70-84%)'),
        ('poor', 'Qoniqarsiz (<70%)'),
    ]
    
    MASTERY_CHOICES = [
        ('excellent', 'A\'lo'),
        ('good', 'Yaxshi'),
        ('satisfactory', 'Qoniqarli'),
        ('needs_improvement', 'Yaxshilash kerak'),
    ]
    
    PROGRESS_CHOICES = [
        ('improved', 'Yaxshilandi'),
        ('stable', 'Barqaror'),
        ('declined', 'Pasaydi'),
    ]
    
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentor_monthly_reports',
                              limit_choices_to={'role': 'mentor'})
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_monthly_reports',
                               limit_choices_to={'role': 'student'})
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='monthly_reports')
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    
    # Oylik hisobot maydonlari
    character = models.CharField(max_length=20, choices=CHARACTER_CHOICES, blank=True, null=True)
    attendance = models.CharField(max_length=20, choices=ATTENDANCE_CHOICES, blank=True, null=True)
    mastery = models.CharField(max_length=20, choices=MASTERY_CHOICES, blank=True, null=True)
    progress_change = models.CharField(max_length=20, choices=PROGRESS_CHOICES, blank=True, null=True)
    additional_notes = models.TextField(blank=True, null=True)  # Qo'shimcha izohlar
    
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Monthly Report')
        verbose_name_plural = _('Monthly Reports')
        unique_together = ['mentor', 'student', 'group', 'month', 'year']
        ordering = ['-year', '-month', '-created_at']
        indexes = [
            models.Index(fields=['mentor', 'year', 'month']),
            models.Index(fields=['student', 'year', 'month']),
            models.Index(fields=['group', 'year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.mentor.username} - {self.student.username} - {self.year}-{self.month:02d}"


class MentorKPI(models.Model):
    """
    Mentor KPI (har oy uchun)
    """
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kpis',
                              limit_choices_to={'role': 'mentor'})
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    
    # KPI mezonlari
    lesson_quality_score = models.FloatField(default=0.0)  # Dars sifati (1-5 o'rtacha)
    attendance_entry_score = models.FloatField(default=0.0)  # Davomatni vaqtida kiritish (0-100%)
    homework_grading_score = models.FloatField(default=0.0)  # Uy vazifalarini o'z vaqtida baholash (0-100%)
    student_progress_score = models.FloatField(default=0.0)  # O'quvchilarning rivojlanish dinamikasi
    group_rating_score = models.FloatField(default=0.0)  # Guruh reytingidagi o'rtacha ball
    parent_feedback_score = models.FloatField(default=0.0)  # Ota-onalar feedbacklari
    monthly_report_score = models.FloatField(default=0.0)  # Oylik hisobotlarni to'ldirish (0-100%)
    
    # Umumiy KPI balli (0-100)
    total_kpi_score = models.FloatField(default=0.0)
    
    # Statistika
    total_lessons = models.IntegerField(default=0)
    total_students = models.IntegerField(default=0)
    completed_reports = models.IntegerField(default=0)
    total_reports = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Mentor KPI')
        verbose_name_plural = _('Mentor KPIs')
        unique_together = ['mentor', 'month', 'year']
        ordering = ['-year', '-month', '-total_kpi_score']
        indexes = [
            models.Index(fields=['mentor', 'year', 'month']),
            models.Index(fields=['total_kpi_score', 'year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.mentor.username} - {self.year}-{self.month:02d} - {self.total_kpi_score:.1f} ball"
    
    def calculate_kpi(self):
        """
        KPI ballini hisoblash
        """
        # 1. Dars sifati (20% vazn)
        if self.total_lessons > 0:
            self.lesson_quality_score = min(5.0, self.lesson_quality_score / self.total_lessons) * 20
        else:
            self.lesson_quality_score = 0
        
        # 2. Davomatni vaqtida kiritish (15% vazn)
        self.attendance_entry_score = self.attendance_entry_score * 0.15
        
        # 3. Uy vazifalarini o'z vaqtida baholash (15% vazn)
        self.homework_grading_score = self.homework_grading_score * 0.15
        
        # 4. O'quvchilarning rivojlanish dinamikasi (15% vazn)
        self.student_progress_score = self.student_progress_score * 0.15
        
        # 5. Guruh reytingidagi o'rtacha ball (15% vazn)
        self.group_rating_score = self.group_rating_score * 0.15
        
        # 6. Ota-onalar feedbacklari (10% vazn)
        self.parent_feedback_score = self.parent_feedback_score * 0.10
        
        # 7. Oylik hisobotlarni to'ldirish (10% vazn)
        if self.total_reports > 0:
            self.monthly_report_score = (self.completed_reports / self.total_reports) * 100 * 0.10
        else:
            self.monthly_report_score = 0
        
        # Umumiy KPI balli
        self.total_kpi_score = (
            self.lesson_quality_score +
            self.attendance_entry_score +
            self.homework_grading_score +
            self.student_progress_score +
            self.group_rating_score +
            self.parent_feedback_score +
            self.monthly_report_score
        )
        
        self.save()
        return self.total_kpi_score


class MentorRanking(models.Model):
    """
    Mentorlar reytingi
    """
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentor_rankings',
                              limit_choices_to={'role': 'mentor'})
    month = models.IntegerField()
    year = models.IntegerField()
    rank = models.IntegerField()
    total_kpi_score = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Mentor Ranking')
        verbose_name_plural = _('Mentor Rankings')
        unique_together = ['mentor', 'month', 'year']
        ordering = ['-year', '-month', 'rank']
        indexes = [
            models.Index(fields=['year', 'month', 'rank']),
            models.Index(fields=['mentor', 'year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.mentor.username} - {self.year}-{self.month:02d} - {self.rank} o'rin"
