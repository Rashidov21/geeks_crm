"""
Celery tasks for parents app
Oylik hisobotlarni avtomatik generatsiya qilish
"""
from celery import shared_task
from django.utils import timezone
from .models import MonthlyParentReport
from accounts.models import User
from courses.models import Group
import logging

logger = logging.getLogger(__name__)


@shared_task
def generate_monthly_parent_reports(month=None, year=None):
    """
    Barcha ota-onalar uchun oylik hisobotlarni generatsiya qilish
    """
    try:
        if not month or not year:
            now = timezone.now()
            # O'tgan oy uchun hisobot
            month = month or (now.month - 1 if now.month > 1 else 12)
            year = year or (now.year if now.month > 1 else now.year - 1)
        
        # Barcha ota-onalar
        parents = User.objects.filter(role='parent', is_active=True)
        
        for parent in parents:
            # Ota-onaning farzandlari
            students = parent.parent_profile.students.all()
            
            for student in students:
                # Studentning guruhlari
                groups = Group.objects.filter(students=student, is_active=True)
                
                for group in groups:
                    # Hisobot yaratish yoki olish
                    report, created = MonthlyParentReport.objects.get_or_create(
                        parent=parent,
                        student=student,
                        group=group,
                        month=month,
                        year=year
                    )
                    
                    # Hisobotni generatsiya qilish
                    report.generate_report()
                    
                    # Telegram orqali yuborish
                    if not report.is_sent:
                        send_monthly_report_to_parent.delay(report.id)
        
        logger.info(f"Monthly parent reports generated for {month}/{year}")
    
    except Exception as e:
        logger.error(f"Error generating monthly parent reports: {e}")


@shared_task
def send_monthly_report_to_parent(report_id):
    """
    Oylik hisobotni Telegram orqali yuborish
    """
    try:
        from telegram import Bot
        from django.conf import settings
        
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        report = MonthlyParentReport.objects.select_related('parent', 'student', 'group').get(pk=report_id)
        
        if not report.parent.telegram_id:
            logger.warning(f"Parent {report.parent.username} has no telegram_id")
            return
        
        # Xabar tayyorlash
        message = f"📊 Oylik hisobot - {report.year}-{report.month:02d}\n\n"
        message += f"Farzand: {report.student.get_full_name() or report.student.username}\n"
        message += f"Guruh: {report.group.name}\n\n"
        
        # Davomat
        message += f"📅 Davomat: {report.attendance_percentage:.1f}%\n"
        message += f"   Keldi: {report.present_count}, Kech: {report.late_count}, Kelmadi: {report.absent_count}\n\n"
        
        # Uy vazifalari
        message += f"📝 Uy vazifalari: {report.homework_completion_rate:.1f}%\n"
        message += f"   Bajarildi: {report.completed_homeworks}/{report.total_homeworks}\n"
        message += f"   Vaqtida: {report.on_time_homeworks}, Kech: {report.late_homeworks}\n\n"
        
        # Imtihonlar
        if report.total_exams > 0:
            message += f"📚 Imtihonlar: {report.total_exams} ta\n"
            message += f"   O'tdi: {report.passed_exams}, O'rtacha: {report.average_exam_score:.1f}%\n"
            message += f"   Eng yaxshi: {report.best_exam_score:.1f}%, Eng yomon: {report.worst_exam_score:.1f}%\n\n"
        
        # Progress
        message += f"📈 Progress: {report.progress_percentage:.1f}%\n"
        if report.progress_change:
            progress_text = {
                'improved': '✅ Yaxshilandi',
                'stable': '➡️ Barqaror',
                'declined': '⚠️ Pasaydi',
            }
            message += f"   {progress_text.get(report.progress_change, report.progress_change)}\n\n"
        
        # Kuchli va kuchsiz tomonlar
        message += f"💪 Kuchli tomonlar:\n{report.strengths}\n\n"
        message += f"⚠️ Kuchsiz tomonlar:\n{report.weaknesses}\n"
        
        # Mentor sharhi
        if report.mentor_report and report.mentor_report.additional_notes:
            message += f"\n👨‍🏫 Mentor sharhi:\n{report.mentor_report.additional_notes}"
        
        # Xabar yuborish
        bot.send_message(chat_id=report.parent.telegram_id, text=message)
        
        # Yuborilgan deb belgilash
        report.is_sent = True
        report.save()
        
        logger.info(f"Monthly report sent to parent {report.parent.username}")
    
    except Exception as e:
        logger.error(f"Error sending monthly report to parent: {e}")

