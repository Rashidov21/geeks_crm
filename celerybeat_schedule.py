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
    
    # ==================== CRM TASKS ====================
    
    # Har 5 daqiqada overdue follow-up'larni tekshirish
    'check-overdue-followups': {
        'task': 'crm.tasks.check_overdue_followups',
        'schedule': crontab(minute='*/5'),  # Har 5 daqiqada
    },
    
    # Har 5 daqiqada follow-up eslatmalarini yuborish
    'send-followup-reminders': {
        'task': 'crm.tasks.send_followup_reminders',
        'schedule': crontab(minute='*/5'),  # Har 5 daqiqada
    },
    
    # Har soatda sinov darsi eslatmalarini tekshirish
    'send-trial-reminders': {
        'task': 'crm.tasks.send_trial_reminders',
        'schedule': crontab(minute=0),  # Har soatda
    },
    
    # Har kuni kechqurun KPI hisoblash
    'calculate-daily-kpi': {
        'task': 'crm.tasks.calculate_daily_kpi',
        'schedule': crontab(hour=23, minute=0),  # Har kuni soat 23:00
    },
    
    # Har kuni ertalab reactivatsiya tekshirish
    'check-reactivation': {
        'task': 'crm.tasks.check_reactivation',
        'schedule': crontab(hour=9, minute=0),  # Har kuni soat 9:00
    },
    
    # Har kuni kechqurun ruxsatlar tugashini tekshirish
    'check-leave-expiry': {
        'task': 'crm.tasks.check_leave_expiry',
        'schedule': crontab(hour=22, minute=0),  # Har kuni soat 22:00
    },
    
    # Har 5 daqiqada Google Sheets'dan import qilish
    'import-leads-from-google-sheets': {
        'task': 'crm.tasks.import_leads_from_google_sheets',
        'schedule': crontab(minute='*/5'),  # Har 5 daqiqada
    },
}

