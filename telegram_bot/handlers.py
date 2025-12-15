"""
Telegram bot handlers
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from django.conf import settings
from accounts.models import User
from courses.models import Lesson, Group
from homework.models import Homework
from exams.models import Exam
from attendance.models import Attendance
from gamification.models import StudentPoints, GroupRanking
from parents.models import MonthlyParentReport
from mentors.models import MonthlyReport
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Botni ishga tushirish"""
    user = update.effective_user
    
    try:
        # User ni topish
        db_user = User.objects.filter(telegram_id=user.id).first()
        
        if not db_user:
            await update.message.reply_text(
                "❌ Siz tizimda ro'yxatdan o'tmagansiz. "
                "Iltimos, avval veb-sahifada ro'yxatdan o'ting va Telegram ID ni qo'shing."
            )
            return
        
        # Role bo'yicha salomlashish
        role_messages = {
            'student': "👋 Salom! Siz o'quvchi sifatida ro'yxatdan o'tgansiz.",
            'parent': "👋 Salom! Siz ota-ona sifatida ro'yxatdan o'tgansiz.",
            'mentor': "👋 Salom! Siz mentor sifatida ro'yxatdan o'tgansiz.",
            'admin': "👋 Salom! Siz admin sifatida ro'yxatdan o'tgansiz.",
        }
        
        message = role_messages.get(db_user.role, "👋 Salom!")
        message += "\n\nQuyidagi buyruqlardan foydalaning:\n"
        message += "/help - Yordam\n"
        
        if db_user.role == 'student':
            message += "/lessons - Darslar ro'yxati\n"
            message += "/homework - Uy vazifalari\n"
            message += "/exams - Imtihonlar\n"
            message += "/points - Mening ballarim\n"
            message += "/ranking - Reyting\n"
        elif db_user.role == 'parent':
            message += "/children - Farzandlarim\n"
            message += "/reports - Oylik hisobotlar\n"
        elif db_user.role == 'mentor':
            message += "/schedule - Dars jadvali\n"
            message += "/homework_grade - Vazifalarni baholash\n"
            message += "/groups - Mening guruhlarim\n"
        
        await update.message.reply_text(message)
    
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam buyrug'i"""
    user = update.effective_user
    
    try:
        db_user = User.objects.filter(telegram_id=user.id).first()
        
        if not db_user:
            await update.message.reply_text("❌ Siz tizimda ro'yxatdan o'tmagansiz.")
            return
        
        help_text = "📚 <b>Mavjud buyruqlar:</b>\n\n"
        
        if db_user.role == 'student':
            help_text += "👨‍🎓 <b>O'quvchi buyruqlari:</b>\n"
            help_text += "/lessons - Bugungi va kelgusi darslar\n"
            help_text += "/homework - Uy vazifalari ro'yxati\n"
            help_text += "/exams - Imtihonlar ro'yxati\n"
            help_text += "/points - Mening ballarim va reytingim\n"
            help_text += "/ranking - Guruh reytingi\n"
            help_text += "/profile - Mening profilim\n"
        
        elif db_user.role == 'parent':
            help_text += "👨‍👩‍👦 <b>Ota-ona buyruqlari:</b>\n"
            help_text += "/children - Farzandlarim ro'yxati\n"
            help_text += "/reports - Oylik hisobotlar\n"
            help_text += "/attendance - Davomat ma'lumotlari\n"
        
        elif db_user.role == 'mentor':
            help_text += "👨‍🏫 <b>Mentor buyruqlari:</b>\n"
            help_text += "/schedule - Dars jadvali\n"
            help_text += "/homework_grade - Baholash kerak bo'lgan vazifalar\n"
            help_text += "/groups - Mening guruhlarim\n"
            help_text += "/kpi - Mening KPI ko'rsatkichlarim\n"
        
        help_text += "\n/start - Botni qayta ishga tushirish\n"
        help_text += "/help - Yordam"
        
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def student_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """O'quvchi uchun darslar ro'yxati"""
    user = update.effective_user
    
    try:
        db_user = User.objects.filter(telegram_id=user.id, role='student').first()
        
        if not db_user:
            await update.message.reply_text("❌ Siz o'quvchi sifatida ro'yxatdan o'tmagansiz.")
            return
        
        # Bugungi va kelgusi darslar
        today = timezone.now().date()
        lessons = Lesson.objects.filter(
            group__students=db_user,
            date__gte=today
        ).select_related('group', 'topic', 'mentor').order_by('date', 'start_time')[:5]
        
        if not lessons:
            await update.message.reply_text("📅 Hozircha darslar yo'q.")
            return
        
        message = "📚 <b>Darslar ro'yxati:</b>\n\n"
        
        for lesson in lessons:
            date_str = lesson.date.strftime('%d.%m.%Y')
            time_str = lesson.start_time.strftime('%H:%M')
            
            message += f"📖 <b>{lesson.group.name}</b>\n"
            message += f"📅 {date_str} {time_str}\n"
            
            if lesson.topic:
                message += f"📝 {lesson.topic.name}\n"
            
            if lesson.mentor:
                message += f"👨‍🏫 {lesson.mentor.get_full_name() or lesson.mentor.username}\n"
            
            # Bugungi dars bo'lsa
            if lesson.date == today:
                message += "✅ <b>Bugun</b>\n"
            
            message += "\n"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    except Exception as e:
        logger.error(f"Error in student_lessons: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def student_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """O'quvchi uchun uy vazifalari"""
    user = update.effective_user
    
    try:
        db_user = User.objects.filter(telegram_id=user.id, role='student').first()
        
        if not db_user:
            await update.message.reply_text("❌ Siz o'quvchi sifatida ro'yxatdan o'tmagansiz.")
            return
        
        # Topshirilmagan va deadline yaqinlashgan vazifalar
        today = timezone.now()
        homeworks = Homework.objects.filter(
            student=db_user,
            is_submitted=False
        ).select_related('lesson', 'lesson__group').order_by('deadline')[:5]
        
        if not homeworks:
            await update.message.reply_text("✅ Barcha uy vazifalari topshirilgan!")
            return
        
        message = "📝 <b>Uy vazifalari:</b>\n\n"
        
        for homework in homeworks:
            deadline_str = homework.deadline.strftime('%d.%m.%Y %H:%M')
            days_left = (homework.deadline - today).days
            
            message += f"📖 <b>{homework.lesson.group.name}</b>\n"
            message += f"📅 Deadline: {deadline_str}\n"
            
            if days_left < 0:
                message += "❌ <b>Muddati o'tib ketgan!</b>\n"
            elif days_left == 0:
                message += "⚠️ <b>Bugun deadline!</b>\n"
            elif days_left <= 3:
                message += f"⚠️ {days_left} kun qoldi\n"
            else:
                message += f"⏰ {days_left} kun qoldi\n"
            
            if homework.title:
                message += f"📝 {homework.title}\n"
            
            message += "\n"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    except Exception as e:
        logger.error(f"Error in student_homework: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def student_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """O'quvchi uchun imtihonlar"""
    user = update.effective_user
    
    try:
        db_user = User.objects.filter(telegram_id=user.id, role='student').first()
        
        if not db_user:
            await update.message.reply_text("❌ Siz o'quvchi sifatida ro'yxatdan o'tmagansiz.")
            return
        
        # Kelgusi imtihonlar
        now = timezone.now()
        exams = Exam.objects.filter(
            group__students=db_user,
            date__gte=now,
            is_active=True
        ).select_related('course', 'group').order_by('date')[:5]
        
        if not exams:
            await update.message.reply_text("📚 Hozircha imtihonlar yo'q.")
            return
        
        message = "📚 <b>Imtihonlar:</b>\n\n"
        
        for exam in exams:
            date_str = exam.date.strftime('%d.%m.%Y %H:%M')
            days_left = (exam.date - now).days
            
            message += f"📖 <b>{exam.title}</b>\n"
            message += f"📅 {date_str}\n"
            message += f"⏱️ {exam.duration_minutes} daqiqa\n"
            
            if days_left == 0:
                message += "✅ <b>Bugun!</b>\n"
            elif days_left == 1:
                message += "⚠️ <b>Ertaga!</b>\n"
            elif days_left <= 7:
                message += f"⚠️ {days_left} kun qoldi\n"
            
            message += "\n"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    except Exception as e:
        logger.error(f"Error in student_exams: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def student_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """O'quvchi uchun ballar va reyting"""
    user = update.effective_user
    
    try:
        db_user = User.objects.filter(telegram_id=user.id, role='student').first()
        
        if not db_user:
            await update.message.reply_text("❌ Siz o'quvchi sifatida ro'yxatdan o'tmagansiz.")
            return
        
        # Guruh bo'yicha ballar
        groups = Group.objects.filter(students=db_user, is_active=True)
        
        if not groups:
            await update.message.reply_text("❌ Siz hech qanday guruhga yozilmagansiz.")
            return
        
        message = "🏆 <b>Mening ballarim:</b>\n\n"
        
        for group in groups:
            student_points = StudentPoints.objects.filter(
                student=db_user,
                group=group
            ).first()
            
            if student_points:
                # Reyting
                ranking = GroupRanking.objects.filter(
                    student=db_user,
                    group=group
                ).first()
                
                message += f"📖 <b>{group.name}</b>\n"
                message += f"🎯 {student_points.total_points} ball\n"
                
                if ranking:
                    message += f"🏅 {ranking.rank} o'rin\n"
                
                message += "\n"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    except Exception as e:
        logger.error(f"Error in student_points: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def parent_children(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ota-ona uchun farzandlar ro'yxati"""
    user = update.effective_user
    
    try:
        db_user = User.objects.filter(telegram_id=user.id, role='parent').first()
        
        if not db_user:
            await update.message.reply_text("❌ Siz ota-ona sifatida ro'yxatdan o'tmagansiz.")
            return
        
        try:
            students = db_user.parent_profile.students.all()
        except:
            await update.message.reply_text("❌ Farzandlar topilmadi.")
            return
        
        if not students:
            await update.message.reply_text("❌ Sizda farzandlar ro'yxatdan o'tmagan.")
            return
        
        message = "👨‍👩‍👦 <b>Farzandlarim:</b>\n\n"
        
        for student in students:
            message += f"👤 <b>{student.get_full_name() or student.username}</b>\n"
            
            # Bugungi davomat
            today = timezone.now().date()
            attendance = Attendance.objects.filter(
                student=student,
                lesson__date=today
            ).first()
            
            if attendance:
                status_emoji = {
                    'present': '✅',
                    'late': '⏰',
                    'absent': '❌'
                }
                message += f"{status_emoji.get(attendance.status, '❓')} Bugun: {attendance.get_status_display()}\n"
            else:
                message += "❓ Bugungi davomat hali kiritilmagan\n"
            
            message += "\n"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    except Exception as e:
        logger.error(f"Error in parent_children: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def parent_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ota-ona uchun oylik hisobotlar"""
    user = update.effective_user
    
    try:
        db_user = User.objects.filter(telegram_id=user.id, role='parent').first()
        
        if not db_user:
            await update.message.reply_text("❌ Siz ota-ona sifatida ro'yxatdan o'tmagansiz.")
            return
        
        # Oxirgi 3 ta hisobot
        reports = MonthlyParentReport.objects.filter(
            parent=db_user
        ).select_related('student', 'group').order_by('-year', '-month')[:3]
        
        if not reports:
            await update.message.reply_text("📊 Hozircha oylik hisobotlar yo'q.")
            return
        
        message = "📊 <b>Oylik hisobotlar:</b>\n\n"
        
        for report in reports:
            message += f"👤 {report.student.get_full_name() or report.student.username}\n"
            message += f"📅 {report.year}-{report.month:02d}\n"
            message += f"📖 {report.group.name}\n"
            message += f"📈 Davomat: {report.attendance_percentage:.1f}%\n"
            message += f"📝 Vazifalar: {report.homework_completion_rate:.1f}%\n"
            
            if report.average_exam_score > 0:
                message += f"📚 Imtihon: {report.average_exam_score:.1f}%\n"
            
            message += "\n"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    except Exception as e:
        logger.error(f"Error in parent_reports: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def mentor_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mentor uchun dars jadvali"""
    user = update.effective_user
    
    try:
        db_user = User.objects.filter(telegram_id=user.id, role='mentor').first()
        
        if not db_user:
            await update.message.reply_text("❌ Siz mentor sifatida ro'yxatdan o'tmagansiz.")
            return
        
        # Bugungi va kelgusi darslar
        today = timezone.now().date()
        lessons = Lesson.objects.filter(
            mentor=db_user,
            date__gte=today
        ).select_related('group', 'topic').order_by('date', 'start_time')[:5]
        
        if not lessons:
            await update.message.reply_text("📅 Hozircha darslar yo'q.")
            return
        
        message = "📚 <b>Dars jadvali:</b>\n\n"
        
        for lesson in lessons:
            date_str = lesson.date.strftime('%d.%m.%Y')
            time_str = lesson.start_time.strftime('%H:%M')
            
            message += f"📖 <b>{lesson.group.name}</b>\n"
            message += f"📅 {date_str} {time_str}\n"
            
            if lesson.topic:
                message += f"📝 {lesson.topic.name}\n"
            
            if lesson.date == today:
                message += "✅ <b>Bugun</b>\n"
            
            message += "\n"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    except Exception as e:
        logger.error(f"Error in mentor_schedule: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def mentor_homework_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mentor uchun baholash kerak bo'lgan vazifalar"""
    user = update.effective_user
    
    try:
        db_user = User.objects.filter(telegram_id=user.id, role='mentor').first()
        
        if not db_user:
            await update.message.reply_text("❌ Siz mentor sifatida ro'yxatdan o'tmagansiz.")
            return
        
        # Baholanmagan vazifalar
        from homework.models import HomeworkGrade
        homeworks = Homework.objects.filter(
            lesson__mentor=db_user,
            is_submitted=True
        ).exclude(
            id__in=HomeworkGrade.objects.values_list('homework_id', flat=True)
        ).select_related('student', 'lesson', 'lesson__group').order_by('submitted_at')[:5]
        
        if not homeworks:
            await update.message.reply_text("✅ Barcha vazifalar baholangan!")
            return
        
        message = "📝 <b>Baholash kerak bo'lgan vazifalar:</b>\n\n"
        
        for homework in homeworks:
            message += f"👤 {homework.student.get_full_name() or homework.student.username}\n"
            message += f"📖 {homework.lesson.group.name}\n"
            
            if homework.title:
                message += f"📝 {homework.title}\n"
            
            submitted_str = homework.submitted_at.strftime('%d.%m.%Y %H:%M')
            message += f"📅 Topshirilgan: {submitted_str}\n"
            
            if homework.is_late:
                message += "⚠️ <b>Kech topshirilgan</b>\n"
            
            message += "\n"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    except Exception as e:
        logger.error(f"Error in mentor_homework_grade: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xatoliklarni qayta ishlash"""
    logger.error(f"Update {update} caused error {context.error}")


def setup_handlers(application: Application):
    """Handlers ni sozlash"""
    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Student commands
    application.add_handler(CommandHandler("lessons", student_lessons))
    application.add_handler(CommandHandler("homework", student_homework))
    application.add_handler(CommandHandler("exams", student_exams))
    application.add_handler(CommandHandler("points", student_points))
    
    # Parent commands
    application.add_handler(CommandHandler("children", parent_children))
    application.add_handler(CommandHandler("reports", parent_reports))
    
    # Mentor commands
    application.add_handler(CommandHandler("schedule", mentor_schedule))
    application.add_handler(CommandHandler("homework_grade", mentor_homework_grade))
    
    # Error handler
    application.add_error_handler(error_handler)

