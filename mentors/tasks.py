"""
Celery tasks for mentors app
KPI avtomatik hisoblash
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Avg, Count, Q
from .models import MentorKPI, MentorRanking, LessonQuality, MonthlyReport
from accounts.models import User
from courses.models import Group, Lesson
from homework.models import Homework, HomeworkGrade
from attendance.models import Attendance
from gamification.models import GroupRanking
import logging

logger = logging.getLogger(__name__)


@shared_task
def calculate_mentor_kpi(mentor_id, month=None, year=None):
    """
    Mentor KPI ni hisoblash
    """
    try:
        mentor = User.objects.get(pk=mentor_id, role='mentor')
        
        if not month or not year:
            now = timezone.now()
            month = month or now.month
            year = year or now.year
        
        # KPI yaratish yoki olish
        kpi, created = MentorKPI.objects.get_or_create(
            mentor=mentor,
            month=month,
            year=year
        )
        
        # 1. Dars sifati (o'quvchilar bahosi 1-5 o'rtacha)
        lessons = Lesson.objects.filter(
            mentor=mentor,
            date__year=year,
            date__month=month
        )
        kpi.total_lessons = lessons.count()
        
        if kpi.total_lessons > 0:
            avg_rating = LessonQuality.objects.filter(
                lesson__mentor=mentor,
                lesson__date__year=year,
                lesson__date__month=month
            ).aggregate(avg=Avg('rating'))['avg'] or 0
            kpi.lesson_quality_score = avg_rating
        else:
            kpi.lesson_quality_score = 0
        
        # 2. Davomatni vaqtida kiritish (dars tugagandan keyin 24 soat ichida)
        total_attendances = 0
        on_time_attendances = 0
        
        for lesson in lessons:
            attendances = Attendance.objects.filter(lesson=lesson)
            total_attendances += attendances.count()
            
            # 24 soat ichida kiritilgan davomatlar
            from datetime import timedelta
            deadline = lesson.date + timedelta(days=1)
            on_time = attendances.filter(created_at__lte=deadline).count()
            on_time_attendances += on_time
        
        if total_attendances > 0:
            kpi.attendance_entry_score = (on_time_attendances / total_attendances) * 100
        else:
            kpi.attendance_entry_score = 0
        
        # 3. Uy vazifalarini o'z vaqtida baholash
        # Vazifalar keyingi dars boshida baholanishi kerak
        homeworks = Homework.objects.filter(
            lesson__mentor=mentor,
            lesson__date__year=year,
            lesson__date__month=month
        )
        
        total_homeworks = homeworks.count()
        graded_on_time = 0
        
        for homework in homeworks:
            grade = HomeworkGrade.objects.filter(homework=homework).first()
            if grade:
                # Keyingi darsni topish
                next_lesson = Lesson.objects.filter(
                    group=homework.lesson.group,
                    date__gt=homework.lesson.date
                ).order_by('date').first()
                
                if next_lesson and grade.graded_at <= next_lesson.date:
                    graded_on_time += 1
        
        if total_homeworks > 0:
            kpi.homework_grading_score = (graded_on_time / total_homeworks) * 100
        else:
            kpi.homework_grading_score = 0
        
        # 4. O'quvchilarning rivojlanish dinamikasi
        # O'tgan oy bilan solishtirish
        from courses.models import StudentProgress
        current_month_progress = StudentProgress.objects.filter(
            student__student_groups__mentor=mentor
        ).values('student').annotate(
            avg_progress=Avg('progress_percentage')
        )
        
        if month > 1:
            prev_month = month - 1
            prev_year = year
        else:
            prev_month = 12
            prev_year = year - 1
        
        prev_month_progress = StudentProgress.objects.filter(
            student__student_groups__mentor=mentor
        ).values('student').annotate(
            avg_progress=Avg('progress_percentage')
        )
        
        # Progress o'sishi
        progress_improvement = 0
        if current_month_progress and prev_month_progress:
            # Soddalashtirilgan hisoblash
            progress_improvement = 50  # Default 50%
        
        kpi.student_progress_score = progress_improvement
        
        # 5. Guruh reytingidagi o'rtacha ball
        groups = Group.objects.filter(mentor=mentor, is_active=True)
        total_group_avg = 0
        group_count = 0
        
        for group in groups:
            rankings = GroupRanking.objects.filter(group=group)
            if rankings.exists():
                avg_rank = rankings.aggregate(avg=Avg('rank'))['avg'] or 0
                # Past rank = yaxshi (1 eng yaxshi)
                # 100 - avg_rank = score (yuqori score = yaxshi)
                total_group_avg += max(0, 100 - avg_rank)
                group_count += 1
        
        if group_count > 0:
            kpi.group_rating_score = total_group_avg / group_count
        else:
            kpi.group_rating_score = 0
        
        # 6. Ota-onalar feedbacklari
        from .models import ParentFeedback
        positive_feedbacks = ParentFeedback.objects.filter(
            mentor=mentor,
            created_at__year=year,
            created_at__month=month,
            feedback_type='positive'
        ).count()
        
        total_feedbacks = ParentFeedback.objects.filter(
            mentor=mentor,
            created_at__year=year,
            created_at__month=month
        ).count()
        
        if total_feedbacks > 0:
            kpi.parent_feedback_score = (positive_feedbacks / total_feedbacks) * 100
        else:
            kpi.parent_feedback_score = 50  # Default 50% (feedback yo'q bo'lsa)
        
        # 7. Oylik hisobotlarni to'ldirish
        students = User.objects.filter(
            student_groups__mentor=mentor,
            role='student'
        ).distinct()
        
        kpi.total_students = students.count()
        kpi.total_reports = MonthlyReport.objects.filter(
            mentor=mentor,
            month=month,
            year=year
        ).count()
        
        kpi.completed_reports = MonthlyReport.objects.filter(
            mentor=mentor,
            month=month,
            year=year,
            is_completed=True
        ).count()
        
        # KPI hisoblash
        kpi.calculate_kpi()
        
        logger.info(f"KPI calculated for {mentor.username} - {year}-{month:02d}: {kpi.total_kpi_score:.1f}")
        
        return kpi.total_kpi_score
    
    except Exception as e:
        logger.error(f"Error calculating KPI for mentor {mentor_id}: {e}")
        return None


@shared_task
def calculate_all_mentors_kpi(month=None, year=None):
    """
    Barcha mentorlar KPI ni hisoblash
    """
    try:
        if not month or not year:
            now = timezone.now()
            month = month or now.month
            year = year or now.year
        
        mentors = User.objects.filter(role='mentor', is_active=True)
        
        for mentor in mentors:
            calculate_mentor_kpi.delay(mentor.id, month, year)
        
        logger.info(f"KPI calculation started for {mentors.count()} mentors")
    
    except Exception as e:
        logger.error(f"Error calculating KPIs: {e}")


@shared_task
def update_mentor_rankings(month=None, year=None):
    """
    Mentorlar reytingini yangilash
    """
    try:
        if not month or not year:
            now = timezone.now()
            month = month or now.month
            year = year or now.year
        
        # Barcha mentorlar KPI larni olish
        kpis = MentorKPI.objects.filter(month=month, year=year).order_by('-total_kpi_score')
        
        rank = 1
        for kpi in kpis:
            MentorRanking.objects.update_or_create(
                mentor=kpi.mentor,
                month=month,
                year=year,
                defaults={
                    'rank': rank,
                    'total_kpi_score': kpi.total_kpi_score
                }
            )
            rank += 1
        
        logger.info(f"Mentor rankings updated for {year}-{month:02d}")
    
    except Exception as e:
        logger.error(f"Error updating mentor rankings: {e}")

