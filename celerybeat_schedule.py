"""
Celery Beat schedule configuration
Bu fayl celery beat ishga tushirish uchun misol
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Har 5 daqiqada dars eslatmalarini yuborish
    'send-lesson-reminders': {
        'task': 'telegram_bot.tasks.send_lesson_reminder',
        'schedule': crontab(minute='*/5'),  # Har 5 daqiqada
    },
    # Har kuni ertalab uy vazifasi eslatmalarini yuborish
    'send-homework-deadline-reminders': {
        'task': 'telegram_bot.tasks.send_homework_deadline_reminder',
        'schedule': crontab(hour=9, minute=0),  # Har kuni soat 9:00
    },
    # Har kuni kechqurun davomat xabarlarini yuborish
    'send-attendance-notifications': {
        'task': 'telegram_bot.tasks.send_attendance_notification_to_parents',
        'schedule': crontab(hour=20, minute=0),  # Har kuni soat 20:00
    },
}

