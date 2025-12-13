"""
Celery tasks for Telegram bot
"""
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from courses.models import Lesson
from homework.models import Homework
from attendance.models import Attendance
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_lesson_reminder():
    """
    Dars boshlanishidan 2 soat oldin eslatma yuborish
    """
    try:
        from telegram import Bot
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        two_hours_later = timezone.now() + timedelta(hours=2)
        
        # Bugungi darslar (2 soatdan keyin boshlanadigan)
        lessons = Lesson.objects.filter(
            date=timezone.now().date(),
            start_time__lte=two_hours_later.time(),
            start_time__gte=timezone.now().time()
        ).select_related('group', 'mentor')
        
        for lesson in lessons:
            # O'quvchilarga xabar
            for student in lesson.group.students.filter(role='student', telegram_id__isnull=False):
                try:
                    message = f"📚 Dars eslatmasi\n\n"
                    message += f"Guruh: {lesson.group.name}\n"
                    message += f"Vaqt: {lesson.start_time.strftime('%H:%M')}\n"
                    if lesson.topic:
                        message += f"Mavzu: {lesson.topic.name}\n"
                    bot.send_message(chat_id=student.telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending message to {student.telegram_id}: {e}")
            
            # Mentorlarga xabar
            if lesson.mentor and lesson.mentor.telegram_id:
                try:
                    message = f"👨‍🏫 Sizning darsingiz 2 soatdan keyin boshlanadi\n\n"
                    message += f"Guruh: {lesson.group.name}\n"
                    message += f"Vaqt: {lesson.start_time.strftime('%H:%M')}\n"
                    bot.send_message(chat_id=lesson.mentor.telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending message to mentor {lesson.mentor.telegram_id}: {e}")
    
    except Exception as e:
        logger.error(f"Error in send_lesson_reminder: {e}")


@shared_task
def send_homework_deadline_reminder():
    """
    Uy vazifasi deadline yaqinlashganda eslatma
    """
    try:
        from telegram import Bot
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        tomorrow = timezone.now() + timedelta(days=1)
        
        # Ertaga deadline bo'lgan vazifalar
        homeworks = Homework.objects.filter(
            deadline__lte=tomorrow,
            deadline__gte=timezone.now(),
            is_submitted=False
        ).select_related('student', 'lesson')
        
        for homework in homeworks:
            if homework.student.telegram_id:
                try:
                    message = f"📝 Uy vazifasi eslatmasi\n\n"
                    message += f"Vazifa: {homework.title or 'Nomsiz'}\n"
                    message += f"Deadline: {homework.deadline.strftime('%Y-%m-%d %H:%M')}\n"
                    message += f"Qolgan vaqt: {homework.deadline - timezone.now()}"
                    bot.send_message(chat_id=homework.student.telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending homework reminder: {e}")
    
    except Exception as e:
        logger.error(f"Error in send_homework_deadline_reminder: {e}")


@shared_task
def send_attendance_notification_to_parents():
    """
    Ota-onalarga bugungi davomat haqida xabar
    """
    try:
        from telegram import Bot
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        today = timezone.now().date()
        
        # Bugungi davomatlar
        attendances = Attendance.objects.filter(
            lesson__date=today
        ).select_related('student', 'lesson', 'lesson__group')
        
        for attendance in attendances:
            # Ota-onalarni topish
            parents = User.objects.filter(
                role='parent',
                parent_profile__students=attendance.student,
                telegram_id__isnull=False
            )
            
            status_text = {
                'present': '✅ Keldi',
                'late': '⏰ Kech qoldi',
                'absent': '❌ Kelmadi'
            }
            
            for parent in parents:
                try:
                    message = f"👨‍👩‍👦 Farzandingizning davomati\n\n"
                    message += f"Ism: {attendance.student.get_full_name() or attendance.student.username}\n"
                    message += f"Guruh: {attendance.lesson.group.name}\n"
                    message += f"Holat: {status_text.get(attendance.status, attendance.get_status_display())}\n"
                    message += f"Sana: {attendance.lesson.date}"
                    bot.send_message(chat_id=parent.telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending attendance notification: {e}")
    
    except Exception as e:
        logger.error(f"Error in send_attendance_notification_to_parents: {e}")


@shared_task
def send_lesson_completion_notification(lesson_id):
    """
    Dars tugaganda o'quvchilar va ota-onalarga xabar
    """
    try:
        from telegram import Bot
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        lesson = Lesson.objects.select_related('group', 'topic').get(pk=lesson_id)
        
        # O'quvchilarga xabar
        for student in lesson.group.students.filter(role='student', telegram_id__isnull=False):
            try:
                message = f"✅ Dars yakunlandi\n\n"
                message += f"Guruh: {lesson.group.name}\n"
                if lesson.topic:
                    message += f"Mavzu: {lesson.topic.name}\n"
                if lesson.homework_description:
                    message += f"\n📝 Uy vazifasi:\n{lesson.homework_description}"
                bot.send_message(chat_id=student.telegram_id, text=message)
            except Exception as e:
                logger.error(f"Error sending lesson completion: {e}")
        
        # Ota-onalarga xabar
        for student in lesson.group.students.filter(role='student'):
            parents = User.objects.filter(
                role='parent',
                parent_profile__students=student,
                telegram_id__isnull=False
            )
            for parent in parents:
                try:
                    message = f"✅ Farzandingizning darsi yakunlandi\n\n"
                    message += f"Ism: {student.get_full_name() or student.username}\n"
                    message += f"Guruh: {lesson.group.name}\n"
                    if lesson.topic:
                        message += f"Mavzu: {lesson.topic.name}\n"
                    bot.send_message(chat_id=parent.telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending lesson completion to parent: {e}")
    
    except Exception as e:
        logger.error(f"Error in send_lesson_completion_notification: {e}")

