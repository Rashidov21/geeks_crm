from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from courses.models import Lesson, Group


class Attendance(models.Model):
    """
    Davomat tizimi
    """
    STATUS_CHOICES = [
        ('present', 'Keldi'),
        ('late', 'Kech qoldi'),
        ('absent', 'Kelmadi'),
    ]
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances',
                               limit_choices_to={'role': 'student'})
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')
    notes = models.TextField(blank=True, null=True)  # Qo'shimcha izohlar
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Attendance')
        verbose_name_plural = _('Attendances')
        unique_together = ['lesson', 'student']
        ordering = ['-lesson__date', '-lesson__start_time']
    
    def __str__(self):
        return f"{self.student.username} - {self.lesson} - {self.get_status_display()}"


class AttendanceStatistics(models.Model):
    """
    O'quvchi davomat statistikasi (guruh bo'yicha)
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_stats',
                               limit_choices_to={'role': 'student'})
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='attendance_stats')
    total_lessons = models.IntegerField(default=0)
    present_count = models.IntegerField(default=0)
    late_count = models.IntegerField(default=0)
    absent_count = models.IntegerField(default=0)
    attendance_percentage = models.FloatField(default=0.0)  # 0-100%
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Attendance Statistics')
        verbose_name_plural = _('Attendance Statistics')
        unique_together = ['student', 'group']
        ordering = ['-attendance_percentage']
    
    def __str__(self):
        return f"{self.student.username} - {self.group.name} ({self.attendance_percentage}%)"
    
    def calculate_statistics(self):
        """Davomat statistikasini hisoblash"""
        attendances = Attendance.objects.filter(
            student=self.student,
            lesson__group=self.group
        )
        
        self.total_lessons = attendances.count()
        self.present_count = attendances.filter(status='present').count()
        self.late_count = attendances.filter(status='late').count()
        self.absent_count = attendances.filter(status='absent').count()
        
        if self.total_lessons > 0:
            # Keldi va kech qoldi hisobga olinadi
            attended = self.present_count + self.late_count
            self.attendance_percentage = (attended / self.total_lessons) * 100
        else:
            self.attendance_percentage = 0.0
        
        self.save()
        return self.attendance_percentage
