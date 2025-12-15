from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.models import User
from courses.models import Group, Course
from attendance.models import AttendanceStatistics
from homework.models import Homework
from exams.models import ExamResult
from mentors.models import MonthlyReport


class ParentDashboard(models.Model):
    """
    Ota-ona dashboard ma'lumotlari (cache uchun)
    """
    parent = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_dashboard',
                                 limit_choices_to={'role': 'parent'})
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parent_dashboards',
                               limit_choices_to={'role': 'student'})
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Parent Dashboard')
        verbose_name_plural = _('Parent Dashboards')
        unique_together = ['parent', 'student']
    
    def __str__(self):
        return f"{self.parent.username} - {self.student.username}"


class MonthlyParentReport(models.Model):
    """
    Ota-onalar uchun oylik avtomatik hisobot
    """
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_reports',
                               limit_choices_to={'role': 'parent'})
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parent_monthly_reports',
                               limit_choices_to={'role': 'student'})
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='parent_monthly_reports')
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    
    # Davomat statistikasi
    attendance_percentage = models.FloatField(default=0.0)
    present_count = models.IntegerField(default=0)
    late_count = models.IntegerField(default=0)
    absent_count = models.IntegerField(default=0)
    total_lessons = models.IntegerField(default=0)
    
    # Uy vazifalari statistikasi
    total_homeworks = models.IntegerField(default=0)
    completed_homeworks = models.IntegerField(default=0)
    on_time_homeworks = models.IntegerField(default=0)
    late_homeworks = models.IntegerField(default=0)
    homework_completion_rate = models.FloatField(default=0.0)
    
    # Imtihon natijalari
    total_exams = models.IntegerField(default=0)
    passed_exams = models.IntegerField(default=0)
    average_exam_score = models.FloatField(default=0.0)
    best_exam_score = models.FloatField(default=0.0)
    worst_exam_score = models.FloatField(default=0.0)
    
    # Kuchli tomonlar
    strengths = models.TextField(blank=True, null=True)
    
    # Kuchsiz tomonlar
    weaknesses = models.TextField(blank=True, null=True)
    
    # Mentor oylik harakteristikasi
    mentor_report = models.ForeignKey(MonthlyReport, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='parent_reports')
    
    # Progress
    progress_percentage = models.FloatField(default=0.0)
    previous_month_progress = models.FloatField(default=0.0)
    progress_change = models.CharField(max_length=20, choices=[
        ('improved', 'Yaxshilandi'),
        ('stable', 'Barqaror'),
        ('declined', 'Pasaydi'),
    ], blank=True, null=True)
    
    is_sent = models.BooleanField(default=False)  # Telegram orqali yuborilganmi
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Monthly Parent Report')
        verbose_name_plural = _('Monthly Parent Reports')
        unique_together = ['parent', 'student', 'group', 'month', 'year']
        ordering = ['-year', '-month', '-created_at']
        indexes = [
            models.Index(fields=['parent', 'year', 'month']),
            models.Index(fields=['student', 'year', 'month']),
            models.Index(fields=['group', 'year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.parent.username} - {self.student.username} - {self.year}-{self.month:02d}"
    
    def generate_report(self):
        """
        Hisobotni avtomatik generatsiya qilish
        """
        from datetime import datetime
        from django.db.models import Avg, Count, Q
        
        # 1. Davomat statistikasi
        attendance_stats = AttendanceStatistics.objects.filter(
            student=self.student,
            group=self.group
        ).first()
        
        if attendance_stats:
            self.attendance_percentage = attendance_stats.attendance_percentage
            self.present_count = attendance_stats.present_count
            self.late_count = attendance_stats.late_count
            self.absent_count = attendance_stats.absent_count
            self.total_lessons = attendance_stats.total_lessons
        
        # 2. Uy vazifalari statistikasi
        homeworks = Homework.objects.filter(
            student=self.student,
            lesson__group=self.group,
            lesson__date__year=self.year,
            lesson__date__month=self.month
        )
        
        self.total_homeworks = homeworks.count()
        self.completed_homeworks = homeworks.filter(is_submitted=True).count()
        self.on_time_homeworks = homeworks.filter(is_submitted=True, is_late=False).count()
        self.late_homeworks = homeworks.filter(is_submitted=True, is_late=True).count()
        
        if self.total_homeworks > 0:
            self.homework_completion_rate = (self.completed_homeworks / self.total_homeworks) * 100
        
        # 3. Imtihon natijalari
        exam_results = ExamResult.objects.filter(
            student=self.student,
            exam__group=self.group,
            submitted_at__year=self.year,
            submitted_at__month=self.month
        )
        
        self.total_exams = exam_results.count()
        self.passed_exams = exam_results.filter(is_passed=True).count()
        
        if self.total_exams > 0:
            avg_score = exam_results.aggregate(avg=Avg('percentage'))['avg'] or 0
            self.average_exam_score = avg_score
            
            best = exam_results.order_by('-percentage').first()
            worst = exam_results.order_by('percentage').first()
            
            if best:
                self.best_exam_score = best.percentage
            if worst:
                self.worst_exam_score = worst.percentage
        
        # 4. Progress
        from courses.models import StudentProgress
        progress = StudentProgress.objects.filter(
            student=self.student,
            course=self.group.course
        ).first()
        
        if progress:
            self.progress_percentage = progress.progress_percentage
        
        # O'tgan oy progress
        if self.month > 1:
            prev_month = self.month - 1
            prev_year = self.year
        else:
            prev_month = 12
            prev_year = self.year - 1
        
        prev_report = MonthlyParentReport.objects.filter(
            student=self.student,
            group=self.group,
            month=prev_month,
            year=prev_year
        ).first()
        
        if prev_report:
            self.previous_month_progress = prev_report.progress_percentage
            
            if self.progress_percentage > prev_report.progress_percentage + 5:
                self.progress_change = 'improved'
            elif self.progress_percentage < prev_report.progress_percentage - 5:
                self.progress_change = 'declined'
            else:
                self.progress_change = 'stable'
        
        # 5. Kuchli va kuchsiz tomonlar
        strengths = []
        weaknesses = []
        
        # Kuchli tomonlar
        if self.attendance_percentage >= 95:
            strengths.append("A'lo davomat")
        if self.homework_completion_rate >= 90:
            strengths.append("Uy vazifalarini to'liq bajarish")
        if self.average_exam_score >= 80:
            strengths.append("Yaxshi imtihon natijalari")
        if self.progress_percentage >= 80:
            strengths.append("Yuqori progress")
        
        # Kuchsiz tomonlar
        if self.attendance_percentage < 70:
            weaknesses.append("Past davomat")
        if self.homework_completion_rate < 60:
            weaknesses.append("Uy vazifalarini kam bajarish")
        if self.average_exam_score < 60:
            weaknesses.append("Past imtihon natijalari")
        if self.progress_percentage < 50:
            weaknesses.append("Past progress")
        
        self.strengths = ", ".join(strengths) if strengths else "Kuchli tomonlar aniqlanmadi"
        self.weaknesses = ", ".join(weaknesses) if weaknesses else "Kuchsiz tomonlar yo'q"
        
        # 6. Mentor oylik hisoboti
        self.mentor_report = MonthlyReport.objects.filter(
            mentor=self.group.mentor,
            student=self.student,
            group=self.group,
            month=self.month,
            year=self.year
        ).first()
        
        self.save()
        return self
