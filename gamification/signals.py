"""
Django signals for gamification app
Ball berish avtomatik tizimi
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import PointTransaction, StudentPoints, Badge, StudentBadge
from attendance.models import Attendance
from homework.models import Homework, HomeworkGrade
from exams.models import ExamResult


@receiver(post_save, sender=Attendance)
def award_points_for_attendance(sender, instance, created, **kwargs):
    """
    Davomat uchun ball berish
    - Keldi: +5
    - Kelmadi: -5
    """
    if created or 'status' in kwargs.get('update_fields', []):
        # Eski transaksiyalarni o'chirish
        PointTransaction.objects.filter(
            student=instance.student,
            attendance=instance,
            point_type__in=['attendance_present', 'attendance_absent']
        ).delete()
        
        if instance.status == 'present':
            points = 5
            point_type = 'attendance_present'
            description = f"Darsga qatnashish: {instance.lesson.group.name}"
        elif instance.status == 'late':
            points = 3  # Kech qoldi uchun kamroq ball
            point_type = 'attendance_present'
            description = f"Darsga kech qolib keldi: {instance.lesson.group.name}"
        elif instance.status == 'absent':
            points = -5
            point_type = 'attendance_absent'
            description = f"Darsni qoldirish: {instance.lesson.group.name}"
        else:
            return
        
        # Yangi transaksiya yaratish
        PointTransaction.objects.create(
            student=instance.student,
            points=points,
            point_type=point_type,
            description=description,
            attendance=instance
        )
        
        # StudentPoints yangilash
        update_student_points(instance.student, instance.lesson.group)


@receiver(post_save, sender=Homework)
def award_points_for_homework(sender, instance, created, **kwargs):
    """
    Uy vazifasi uchun ball berish
    - Vaqtida topshirish: +10
    - Kech topshirish: +3
    """
    if instance.is_submitted and instance.submitted_at:
        # Eski transaksiyalarni o'chirish
        PointTransaction.objects.filter(
            student=instance.student,
            homework=instance,
            point_type__in=['homework_on_time', 'homework_late']
        ).delete()
        
        if instance.is_late:
            points = 3
            point_type = 'homework_late'
            description = f"Uy vazifani kech topshirish: {instance.lesson.group.name}"
        else:
            points = 10
            point_type = 'homework_on_time'
            description = f"Uy vazifani vaqtida topshirish: {instance.lesson.group.name}"
        
        # Yangi transaksiya yaratish
        PointTransaction.objects.create(
            student=instance.student,
            points=points,
            point_type=point_type,
            description=description,
            homework=instance
        )
        
        # StudentPoints yangilash
        update_student_points(instance.student, instance.lesson.group)


@receiver(post_save, sender=ExamResult)
def award_points_for_exam(sender, instance, created, **kwargs):
    """
    Imtihon uchun ball berish
    - Yuqori ball (guruh o'rtachasidan yuqori): +20
    """
    if instance.is_passed and instance.percentage:
        # Guruh o'rtacha ballini hisoblash
        from django.db.models import Avg
        group_avg = ExamResult.objects.filter(
            exam=instance.exam,
            exam__group=instance.exam.group
        ).exclude(id=instance.id).aggregate(
            avg_percentage=Avg('percentage')
        )['avg_percentage'] or 0
        
        # Agar o'quvchi o'rtachadan yuqori ball olgan bo'lsa
        if instance.percentage > group_avg:
            # Eski transaksiyalarni o'chirish
            PointTransaction.objects.filter(
                student=instance.student,
                exam_result=instance,
                point_type='exam_high_score'
            ).delete()
            
            # Yangi transaksiya yaratish
            PointTransaction.objects.create(
                student=instance.student,
                points=20,
                point_type='exam_high_score',
                description=f"Imtihondan yuqori ball: {instance.exam.title} ({instance.percentage:.1f}%)",
                exam_result=instance
            )
            
            # StudentPoints yangilash
            if instance.exam.group:
                update_student_points(instance.student, instance.exam.group)


def update_student_points(student, group):
    """
    O'quvchi balllarini yangilash
    """
    student_points, created = StudentPoints.objects.get_or_create(
        student=student,
        group=group
    )
    student_points.calculate_total_points()
    
    # Badge tekshirish
    check_and_award_badges(student, group)


def check_and_award_badges(student, group):
    """
    Badge berish shartlarini tekshirish va berish
    """
    student_points = StudentPoints.objects.filter(student=student, group=group).first()
    if not student_points:
        return
    
    # Perfect Attendance badge
    from attendance.models import AttendanceStatistics
    attendance_stats = AttendanceStatistics.objects.filter(
        student=student,
        group=group
    ).first()
    
    if attendance_stats and attendance_stats.attendance_percentage == 100:
        badge = Badge.objects.filter(badge_type='perfect_attendance').first()
        if badge:
            StudentBadge.objects.get_or_create(
                student=student,
                badge=badge,
                group=group
            )
    
    # Homework Master badge
    from homework.models import Homework
    total_homeworks = Homework.objects.filter(
        student=student,
        lesson__group=group,
        is_submitted=True
    ).count()
    on_time_homeworks = Homework.objects.filter(
        student=student,
        lesson__group=group,
        is_submitted=True,
        is_late=False
    ).count()
    
    if total_homeworks > 0 and (on_time_homeworks / total_homeworks) >= 0.9:  # 90% vaqtida
        badge = Badge.objects.filter(badge_type='homework_master').first()
        if badge:
            StudentBadge.objects.get_or_create(
                student=student,
                badge=badge,
                group=group
            )
    
    # Ball asosida badge berish
    for badge in Badge.objects.filter(is_active=True, points_required__gt=0):
        if student_points.total_points >= badge.points_required:
            StudentBadge.objects.get_or_create(
                student=student,
                badge=badge,
                group=group
            )

