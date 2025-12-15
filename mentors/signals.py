"""
Django signals for mentors app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MonthlyReport
from telegram_bot.tasks import send_monthly_report_to_parent


@receiver(post_save, sender=MonthlyReport)
def send_monthly_report_notification(sender, instance, created, **kwargs):
    """
    Oylik hisobot to'ldirilganda ota-onalarga xabar yuborish
    """
    if instance.is_completed:
        # Celery task orqali xabar yuborish
        send_monthly_report_to_parent.delay(instance.id)

