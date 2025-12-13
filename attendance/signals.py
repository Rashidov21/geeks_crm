"""
Django signals for attendance app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Attendance, AttendanceStatistics


@receiver(post_save, sender=Attendance)
def update_attendance_statistics(sender, instance, **kwargs):
    """
    Davomat o'zgarganda, statistikani avtomatik yangilash
    """
    if instance.lesson and instance.lesson.group:
        stats, created = AttendanceStatistics.objects.get_or_create(
            student=instance.student,
            group=instance.lesson.group
        )
        stats.calculate_statistics()

