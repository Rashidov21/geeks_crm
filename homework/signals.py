from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Homework, HomeworkGrade
from gamification.models import PointTransaction


@receiver(post_save, sender=Homework)
def award_homework_points(sender, instance, created, **kwargs):
    """
    Vazifa topshirilganda avtomatik ball berish
    """
    # Faqat topshirilgan va hali ball berilmagan vazifalar uchun
    if instance.is_submitted and not instance.point_transactions.exists():
        points = 10 if not instance.is_late else 3
        point_type = 'homework_on_time' if not instance.is_late else 'homework_late'
        
        PointTransaction.objects.create(
            student=instance.student,
            points=points,
            point_type=point_type,
            homework=instance,
            description=f"Vazifa: {instance.title or 'Vazifa'}"
        )
        
        # StudentPoints'ni yangilash
        if hasattr(instance.lesson, 'group') and instance.lesson.group:
            from gamification.models import StudentPoints
            student_points, _ = StudentPoints.objects.get_or_create(
                student=instance.student,
                group=instance.lesson.group
            )
            student_points.calculate_total_points()
        
        # Telegram notification
        from telegram_bot.tasks import send_homework_submitted_notification
        send_homework_submitted_notification.delay(instance.pk)


@receiver(pre_save, sender=Homework)
def validate_homework_file(sender, instance, **kwargs):
    """
    File upload validatsiyasi
    """
    if instance.file and hasattr(instance.file, 'size'):
        max_size = 10 * 1024 * 1024  # 10MB
        if instance.file.size > max_size:
            from django.core.exceptions import ValidationError
            raise ValidationError("Fayl hajmi 10MB dan oshmasligi kerak")


@receiver(post_save, sender=Homework)
def notify_homework_assigned(sender, instance, created, **kwargs):
    """
    Vazifa berilganda notification yuborish
    """
    if created:
        from telegram_bot.tasks import send_homework_assigned_notification
        send_homework_assigned_notification.delay(instance.pk)


@receiver(post_save, sender=HomeworkGrade)
def notify_homework_graded(sender, instance, created, **kwargs):
    """
    Vazifa baholanganida notification yuborish
    """
    from telegram_bot.tasks import send_homework_graded_notification
    send_homework_graded_notification.delay(instance.homework.pk)

