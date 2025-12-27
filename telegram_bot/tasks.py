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
def send_homework_assigned_notification(homework_id):
    """
    Vazifa berilganda o'quvchiga va ota-onaga xabar
    """
    try:
        from telegram import Bot
        from homework.models import Homework
        from accounts.models import StudentProfile
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        homework = Homework.objects.select_related('student', 'lesson', 'lesson__group').get(pk=homework_id)
        student = homework.student
        
        # O'quvchiga xabar
        if student.telegram_id:
            try:
                message = f"📝 Yangi vazifa\n\n"
                message += f"Vazifa: {homework.title or 'Vazifa'}\n"
                if homework.lesson and homework.lesson.group:
                    message += f"Guruh: {homework.lesson.group.name}\n"
                if homework.assignment_description:
                    message += f"\nTavsif:\n{homework.assignment_description[:200]}...\n"
                message += f"Muddati: {homework.deadline.strftime('%d.%m.%Y %H:%M')}"
                bot.send_message(chat_id=student.telegram_id, text=message)
            except Exception as e:
                logger.error(f"Error sending homework notification to student: {e}")
        
        # Ota-onaga xabar
        try:
            student_profile = StudentProfile.objects.get(user=student)
            parent_telegram_id = student_profile.parent_telegram_id
            
            if parent_telegram_id:
                try:
                    message = f"📝 Farzandingizga yangi vazifa berildi\n\n"
                    message += f"Farzand: {student.get_full_name() or student.username}\n"
                    message += f"Vazifa: {homework.title or 'Vazifa'}\n"
                    if homework.lesson and homework.lesson.group:
                        message += f"Guruh: {homework.lesson.group.name}\n"
                    message += f"Muddati: {homework.deadline.strftime('%d.%m.%Y %H:%M')}"
                    bot.send_message(chat_id=parent_telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending homework notification to parent: {e}")
        except StudentProfile.DoesNotExist:
            pass
    
    except Exception as e:
        logger.error(f"Error in send_homework_assigned_notification: {e}")


@shared_task
def send_homework_submitted_notification(homework_id):
    """
    Vazifa topshirilganda mentor va ota-onaga xabar
    """
    try:
        from telegram import Bot
        from homework.models import Homework
        from accounts.models import StudentProfile
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        homework = Homework.objects.select_related('student', 'lesson', 'lesson__group', 'lesson__group__mentor').get(pk=homework_id)
        student = homework.student
        
        # Mentorga xabar
        if homework.lesson and homework.lesson.group and homework.lesson.group.mentor:
            mentor = homework.lesson.group.mentor
            if mentor.telegram_id:
                try:
                    message = f"✅ Vazifa topshirildi\n\n"
                    message += f"O'quvchi: {student.get_full_name() or student.username}\n"
                    message += f"Vazifa: {homework.title or 'Vazifa'}\n"
                    if homework.lesson.group:
                        message += f"Guruh: {homework.lesson.group.name}\n"
                    message += f"Topshirilgan: {homework.submitted_at.strftime('%d.%m.%Y %H:%M')}"
                    if homework.is_late:
                        message += f"\n⚠️ Kech topshirildi"
                    bot.send_message(chat_id=mentor.telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending homework submitted notification to mentor: {e}")
        
        # Ota-onaga xabar
        try:
            student_profile = StudentProfile.objects.get(user=student)
            parent_telegram_id = student_profile.parent_telegram_id
            
            if parent_telegram_id:
                try:
                    message = f"✅ Farzandingiz vazifani topshirdi\n\n"
                    message += f"Farzand: {student.get_full_name() or student.username}\n"
                    message += f"Vazifa: {homework.title or 'Vazifa'}\n"
                    if homework.is_late:
                        message += f"⚠️ Kech topshirildi"
                    else:
                        message += f"✅ Vaqtida topshirildi"
                    bot.send_message(chat_id=parent_telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending homework submitted notification to parent: {e}")
        except StudentProfile.DoesNotExist:
            pass
    
    except Exception as e:
        logger.error(f"Error in send_homework_submitted_notification: {e}")


@shared_task
def send_homework_graded_notification(homework_id):
    """
    Vazifa baholanganida o'quvchiga va ota-onaga xabar
    """
    try:
        from telegram import Bot
        from homework.models import Homework
        from accounts.models import StudentProfile
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        homework = Homework.objects.select_related('student', 'grade', 'lesson', 'lesson__group').get(pk=homework_id)
        student = homework.student
        
        if not homework.grade:
            return
        
        # O'quvchiga xabar
        if student.telegram_id:
            try:
                message = f"⭐ Vazifa baholandi\n\n"
                message += f"Vazifa: {homework.title or 'Vazifa'}\n"
                message += f"Baho: {homework.grade.grade}/100\n"
                if homework.grade.comment:
                    message += f"\nIzoh:\n{homework.grade.comment[:200]}"
                bot.send_message(chat_id=student.telegram_id, text=message)
            except Exception as e:
                logger.error(f"Error sending homework graded notification to student: {e}")
        
        # Ota-onaga xabar
        try:
            student_profile = StudentProfile.objects.get(user=student)
            parent_telegram_id = student_profile.parent_telegram_id
            
            if parent_telegram_id:
                try:
                    message = f"⭐ Farzandingizning vazifasi baholandi\n\n"
                    message += f"Farzand: {student.get_full_name() or student.username}\n"
                    message += f"Vazifa: {homework.title or 'Vazifa'}\n"
                    message += f"Baho: {homework.grade.grade}/100"
                    bot.send_message(chat_id=parent_telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending homework graded notification to parent: {e}")
        except StudentProfile.DoesNotExist:
            pass
    
    except Exception as e:
        logger.error(f"Error in send_homework_graded_notification: {e}")


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
            # Ota-ona ma'lumotlarini StudentProfile dan olish
            from accounts.models import StudentProfile
            try:
                student_profile = StudentProfile.objects.get(user=attendance.student)
                parent_telegram_id = student_profile.parent_telegram_id
                
                if not parent_telegram_id:
                    continue
                
                status_text = {
                    'present': '✅ Keldi',
                    'late': '⏰ Kech qoldi',
                    'absent': '❌ Kelmadi'
                }
                
                try:
                    message = f"👨‍👩‍👦 Farzandingizning davomati\n\n"
                    message += f"Ism: {attendance.student.get_full_name() or attendance.student.username}\n"
                    message += f"Guruh: {attendance.lesson.group.name}\n"
                    message += f"Holat: {status_text.get(attendance.status, attendance.get_status_display())}\n"
                    message += f"Sana: {attendance.lesson.date}"
                    bot.send_message(chat_id=parent_telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending attendance notification: {e}")
            except StudentProfile.DoesNotExist:
                continue
    
    except Exception as e:
        logger.error(f"Error in send_attendance_notification_to_parents: {e}")


@shared_task
def send_monthly_report_to_parent(report_id):
    """
    Oylik hisobotni ota-onalarga yuborish
    """
    try:
        from telegram import Bot
        from mentors.models import MonthlyReport
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        report = MonthlyReport.objects.select_related('mentor', 'student', 'group').get(pk=report_id)
        
        # Ota-ona ma'lumotlarini StudentProfile dan olish
        from accounts.models import StudentProfile
        try:
            student_profile = StudentProfile.objects.get(user=report.student)
            parent_telegram_id = student_profile.parent_telegram_id
            
            if not parent_telegram_id:
                logger.warning(f"Student {report.student.username} has no parent telegram_id")
                return
            
            character_text = {
                'excellent': 'A\'lo',
                'good': 'Yaxshi',
                'satisfactory': 'Qoniqarli',
                'needs_improvement': 'Yaxshilash kerak',
            }
            
            attendance_text = {
                'excellent': 'A\'lo (95-100%)',
                'good': 'Yaxshi (85-94%)',
                'satisfactory': 'Qoniqarli (70-84%)',
                'poor': 'Qoniqarsiz (<70%)',
            }
            
            mastery_text = {
                'excellent': 'A\'lo',
                'good': 'Yaxshi',
                'satisfactory': 'Qoniqarli',
                'needs_improvement': 'Yaxshilash kerak',
            }
            
            progress_text = {
                'improved': 'Yaxshilandi',
                'stable': 'Barqaror',
                'declined': 'Pasaydi',
            }
            
            try:
                message = f"📊 Oylik hisobot\n\n"
                message += f"Farzand: {report.student.get_full_name() or report.student.username}\n"
                message += f"Guruh: {report.group.name}\n"
                message += f"Oy: {report.year}-{report.month:02d}\n"
                message += f"Mentor: {report.mentor.get_full_name() or report.mentor.username}\n\n"
                
                if report.character:
                    message += f"Xulq: {character_text.get(report.character, report.character)}\n"
                if report.attendance:
                    message += f"Davomat: {attendance_text.get(report.attendance, report.attendance)}\n"
                if report.mastery:
                    message += f"O'zlashtirish: {mastery_text.get(report.mastery, report.mastery)}\n"
                if report.progress_change:
                    message += f"O'zgarish: {progress_text.get(report.progress_change, report.progress_change)}\n"
                
                if report.additional_notes:
                    message += f"\nQo'shimcha izoh:\n{report.additional_notes}"
                
                bot.send_message(chat_id=parent_telegram_id, text=message)
            except Exception as e:
                logger.error(f"Error sending monthly report to parent: {e}")
        except StudentProfile.DoesNotExist:
            logger.warning(f"StudentProfile not found for student {report.student.username}")
    
    except Exception as e:
        logger.error(f"Error in send_monthly_report_to_parent: {e}")


@shared_task
def send_parent_comment_notification(telegram_id, student_id, group_id, comment):
    """
    Ota-onaga izoh yuborish
    """
    try:
        from telegram import Bot
        from accounts.models import User
        from courses.models import Group
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        student = User.objects.get(pk=student_id, role='student')
        group = Group.objects.get(pk=group_id)
        
        message = f"💬 Farzandingiz haqida izoh\n\n"
        message += f"Farzand: {student.get_full_name() or student.username}\n"
        message += f"Guruh: {group.name}\n"
        message += f"Mentor: {group.mentor.get_full_name() if group.mentor else 'Belgilanmagan'}\n\n"
        message += f"Izoh:\n{comment}"
        
        bot.send_message(chat_id=telegram_id, text=message)
        logger.info(f"Parent comment sent to {telegram_id}")
        
    except Exception as e:
        logger.error(f"Error sending parent comment notification: {e}")


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
        from accounts.models import StudentProfile
        for student in lesson.group.students.filter(role='student'):
            try:
                student_profile = StudentProfile.objects.get(user=student)
                parent_telegram_id = student_profile.parent_telegram_id
                
                if not parent_telegram_id:
                    continue
                
                try:
                    message = f"✅ Farzandingizning darsi yakunlandi\n\n"
                    message += f"Ism: {student.get_full_name() or student.username}\n"
                    message += f"Guruh: {lesson.group.name}\n"
                    if lesson.topic:
                        message += f"Mavzu: {lesson.topic.name}\n"
                    bot.send_message(chat_id=parent_telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending lesson completion to parent: {e}")
            except StudentProfile.DoesNotExist:
                continue
    
    except Exception as e:
        logger.error(f"Error in send_lesson_completion_notification: {e}")


@shared_task
def send_lead_assignment_notification(lead_id):
    """
    Sotuvchiga yangi lid tayinlanganda xabar
    """
    try:
        from telegram import Bot
        from crm.models import Lead
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        lead = Lead.objects.select_related('assigned_sales', 'interested_course', 'branch').get(pk=lead_id)
        
        if lead.assigned_sales and lead.assigned_sales.telegram_id:
            try:
                message = f"🆕 Yangi lid tayinlandi\n\n"
                message += f"Ism: {lead.name}\n"
                message += f"Telefon: {lead.phone}\n"
                if lead.interested_course:
                    message += f"Kurs: {lead.interested_course.name}\n"
                if lead.branch:
                    message += f"Filial: {lead.branch.name}\n"
                message += f"\n5 daqiqadan keyin follow-up yaratiladi."
                
                bot.send_message(chat_id=lead.assigned_sales.telegram_id, text=message)
            except Exception as e:
                logger.error(f"Error sending lead assignment notification: {e}")
    
    except Exception as e:
        logger.error(f"Error in send_lead_assignment_notification: {e}")


@shared_task
def send_followup_reminder():
    """
    Follow-up eslatmalari (ish vaqtida)
    """
    try:
        from telegram import Bot
        from crm.models import FollowUp, WorkSchedule
        from datetime import datetime
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        now = timezone.now()
        weekday = now.weekday()
        current_time = now.time()
        
        # Bugungi follow-up'lar (1 soatdan keyin)
        one_hour_later = now + timedelta(hours=1)
        
        followups = FollowUp.objects.filter(
            due_date__gte=now,
            due_date__lte=one_hour_later,
            completed=False
        ).select_related('lead', 'sales')
        
        for followup in followups:
            # Sotuvchi ish vaqtida bo'lishi kerak
            work_schedule = WorkSchedule.objects.filter(
                sales=followup.sales,
                weekday=weekday,
                is_active=True,
                start_time__lte=current_time,
                end_time__gte=current_time
            ).exists()
            
            if work_schedule and followup.sales.telegram_id:
                try:
                    message = f"⏰ Follow-up eslatmasi\n\n"
                    message += f"Lid: {followup.lead.name}\n"
                    message += f"Telefon: {followup.lead.phone}\n"
                    message += f"Vaqt: {followup.due_date.strftime('%Y-%m-%d %H:%M')}\n"
                    message += f"Qolgan vaqt: {(followup.due_date - now).seconds // 60} daqiqa"
                    
                    bot.send_message(chat_id=followup.sales.telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending followup reminder: {e}")
    
    except Exception as e:
        logger.error(f"Error in send_followup_reminder: {e}")


@shared_task
def send_trial_reminder(trial_lesson_id):
    """
    Sinov darsi eslatmalari (8-10 soat va 2 soat oldin)
    """
    try:
        from telegram import Bot
        from crm.models import TrialLesson
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        trial = TrialLesson.objects.select_related('lead', 'group', 'room').get(pk=trial_lesson_id)
        
        # Sinov vaqti
        trial_datetime = timezone.make_aware(
            datetime.combine(trial.date, trial.time)
        ) if trial.time else None
        now = timezone.now()
        
        if not trial_datetime:
            return
        
        # 8-10 soat oldin
        hours_before = (trial_datetime - now).total_seconds() / 3600
        
        if 8 <= hours_before <= 10:
            # Sotuvchiga xabar
            if trial.lead.assigned_sales and trial.lead.assigned_sales.telegram_id:
                try:
                    message = f"📅 Sinov darsi eslatmasi\n\n"
                    message += f"Lid: {trial.lead.name}\n"
                    message += f"Guruh: {trial.group.name}\n"
                    message += f"Vaqt: {trial.date} {trial.time.strftime('%H:%M')}\n"
                    if trial.room:
                        message += f"Xona: {trial.room.name}\n"
                    message += f"\n8-10 soatdan keyin sinov boshlanadi."
                    
                    bot.send_message(chat_id=trial.lead.assigned_sales.telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending trial reminder: {e}")
        
        # 2 soat oldin
        elif 1.5 <= hours_before <= 2.5:
            # Sotuvchiga xabar
            if trial.lead.assigned_sales and trial.lead.assigned_sales.telegram_id:
                try:
                    message = f"⏰ Sinov darsi 2 soatdan keyin boshlanadi\n\n"
                    message += f"Lid: {trial.lead.name}\n"
                    message += f"Guruh: {trial.group.name}\n"
                    message += f"Vaqt: {trial.time.strftime('%H:%M')}\n"
                    if trial.room:
                        message += f"Xona: {trial.room.name}\n"
                    
                    bot.send_message(chat_id=trial.lead.assigned_sales.telegram_id, text=message)
                except Exception as e:
                    logger.error(f"Error sending trial reminder: {e}")
    
    except Exception as e:
        logger.error(f"Error in send_trial_reminder: {e}")


@shared_task
def send_payment_reminder(reminder_id):
    """
    To'lov eslatmasini Telegram orqali yuborish
    """
    try:
        from telegram import Bot
        from finance.models import PaymentReminder
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        reminder = PaymentReminder.objects.select_related(
            'contract', 'contract__student', 'payment_plan', 'debt'
        ).get(pk=reminder_id)
        
        student = reminder.contract.student
        
        if student.telegram_id:
            try:
                message = f"💳 To'lov eslatmasi\n\n"
                message += f"O'quvchi: {student.get_full_name() or student.username}\n"
                message += f"Shartnoma: {reminder.contract.contract_number}\n"
                
                if reminder.payment_plan:
                    message += f"Oylik to'lov: {reminder.payment_plan.installment_number}\n"
                    message += f"Miqdor: {reminder.payment_plan.amount} so'm\n"
                    message += f"Muddati: {reminder.payment_plan.due_date}\n"
                    if reminder.payment_plan.is_overdue:
                        message += f"⚠️ Muddati o'tgan: {reminder.payment_plan.days_overdue} kun\n"
                
                if reminder.debt:
                    message += f"Qarz miqdori: {reminder.debt.amount} so'm\n"
                    message += f"Muddati: {reminder.debt.due_date}\n"
                    if reminder.debt.is_overdue:
                        message += f"⚠️ Muddati o'tgan: {reminder.debt.days_overdue} kun\n"
                
                if reminder.notes:
                    message += f"\n{reminder.notes}"
                
                bot.send_message(chat_id=student.telegram_id, text=message)
                
                # Eslatma yuborilgan deb belgilash
                reminder.is_sent = True
                reminder.sent_at = timezone.now()
                reminder.save()
                
            except Exception as e:
                logger.error(f"Error sending payment reminder: {e}")
        
        # Ota-onalarga ham yuborish
        from accounts.models import ParentProfile
        parents = User.objects.filter(
            role='parent',
            parent_profile__students=student,
            telegram_id__isnull=False
        )
        
        for parent in parents:
            try:
                bot.send_message(chat_id=parent.telegram_id, text=message)
            except Exception as e:
                logger.error(f"Error sending payment reminder to parent: {e}")
    
    except Exception as e:
        logger.error(f"Error in send_payment_reminder: {e}")

