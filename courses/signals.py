"""
Django signals for courses app
"""
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import StudentProgress, Topic, Lesson
from attendance.models import Attendance


@receiver(m2m_changed, sender=StudentProgress.completed_topics.through)
def update_progress_on_topic_completion(sender, instance, action, **kwargs):
    """
    Progressni avtomatik yangilash, mavzu bajarilganda
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.calculate_progress()


@receiver(post_save, sender=Lesson)
def create_attendance_records(sender, instance, created, **kwargs):
    """
    Dars yaratilganda, barcha o'quvchilar uchun davomat yozuvlarini yaratish
    """
    if created and instance.group:
        from accounts.models import User
        students = instance.group.students.filter(role='student')
        for student in students:
            Attendance.objects.get_or_create(
                lesson=instance,
                student=student,
                defaults={'status': 'absent'}
            )


@receiver(post_save, sender=Lesson)
def send_lesson_completion_notification_signal(sender, instance, created, **kwargs):
    """
    Dars yangilanganda (tugaganda) xabar yuborish
    """
    if not created and instance.end_time:  # Dars tugagan bo'lsa
        from telegram_bot.tasks import send_lesson_completion_notification
        # Celery taskni chaqirish
        send_lesson_completion_notification.delay(instance.id)

