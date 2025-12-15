"""
Celery tasks for gamification
Reytinglarni avtomatik yangilash
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime
from .models import (
    StudentPoints, GroupRanking, BranchRanking, OverallRanking, MonthlyRanking, PointTransaction
)
from accounts.models import User, Branch
from courses.models import Group
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_group_rankings():
    """
    Guruh bo'yicha reytinglarni yangilash
    """
    try:
        groups = Group.objects.filter(is_active=True)
        
        for group in groups:
            # Barcha o'quvchilar balllarini yangilash
            students = group.students.filter(role='student')
            for student in students:
                student_points, created = StudentPoints.objects.get_or_create(
                    student=student,
                    group=group
                )
                student_points.calculate_total_points()
            
            # Reyting yaratish/yangilash
            student_points_list = StudentPoints.objects.filter(
                group=group
            ).order_by('-total_points')
            
            rank = 1
            for student_points in student_points_list:
                GroupRanking.objects.update_or_create(
                    group=group,
                    student=student_points.student,
                    defaults={
                        'rank': rank,
                        'total_points': student_points.total_points
                    }
                )
                rank += 1
        
        logger.info(f"Group rankings updated for {groups.count()} groups")
    
    except Exception as e:
        logger.error(f"Error updating group rankings: {e}")


@shared_task
def update_branch_rankings():
    """
    Filial bo'yicha reytinglarni yangilash
    """
    try:
        branches = Branch.objects.filter(is_active=True)
        
        for branch in branches:
            # Filialdagi barcha o'quvchilar
            students = User.objects.filter(
                role='student',
                student_profile__branch=branch
            )
            
            student_totals = {}
            for student in students:
                # Barcha guruhlar bo'yicha jami ball
                total = StudentPoints.objects.filter(
                    student=student,
                    group__course__branch=branch
                ).aggregate(total=Sum('total_points'))['total'] or 0
                
                student_totals[student] = total
            
            # Reyting yaratish/yangilash
            sorted_students = sorted(student_totals.items(), key=lambda x: x[1], reverse=True)
            
            rank = 1
            for student, total_points in sorted_students:
                BranchRanking.objects.update_or_create(
                    branch=branch,
                    student=student,
                    defaults={
                        'rank': rank,
                        'total_points': total_points
                    }
                )
                rank += 1
        
        logger.info(f"Branch rankings updated for {branches.count()} branches")
    
    except Exception as e:
        logger.error(f"Error updating branch rankings: {e}")


@shared_task
def update_overall_rankings():
    """
    Markaz bo'yicha umumiy reytinglarni yangilash
    """
    try:
        students = User.objects.filter(role='student')
        
        student_totals = {}
        for student in students:
            # Barcha guruhlar bo'yicha jami ball
            total = StudentPoints.objects.filter(
                student=student
            ).aggregate(total=Sum('total_points'))['total'] or 0
            
            student_totals[student] = total
        
        # Reyting yaratish/yangilash
        sorted_students = sorted(student_totals.items(), key=lambda x: x[1], reverse=True)
        
        rank = 1
        for student, total_points in sorted_students:
            OverallRanking.objects.update_or_create(
                student=student,
                defaults={
                    'rank': rank,
                    'total_points': total_points
                }
            )
            rank += 1
        
        logger.info(f"Overall rankings updated for {len(sorted_students)} students")
    
    except Exception as e:
        logger.error(f"Error updating overall rankings: {e}")


@shared_task
def update_monthly_rankings():
    """
    Oylik reytinglarni yangilash (har oy oxirida)
    """
    try:
        now = timezone.now()
        last_month = now.month - 1 if now.month > 1 else 12
        last_year = now.year if now.month > 1 else now.year - 1
        
        students = User.objects.filter(role='student')
        
        student_totals = {}
        for student in students:
            # O'tgan oy uchun balllar
            total = PointTransaction.objects.filter(
                student=student,
                created_at__year=last_year,
                created_at__month=last_month
            ).aggregate(total=Sum('points'))['total'] or 0
            
            student_totals[student] = total
        
        # Reyting yaratish/yangilash
        sorted_students = sorted(student_totals.items(), key=lambda x: x[1], reverse=True)
        
        ranking_types = ['top_10', 'top_25', 'top_50', 'top_100']
        limits = {'top_10': 10, 'top_25': 25, 'top_50': 50, 'top_100': 100}
        
        for ranking_type in ranking_types:
            rank = 1
            limit = limits[ranking_type]
            
            for student, total_points in sorted_students[:limit]:
                MonthlyRanking.objects.update_or_create(
                    student=student,
                    ranking_type=ranking_type,
                    month=last_month,
                    year=last_year,
                    defaults={
                        'rank': rank,
                        'total_points': total_points
                    }
                )
                rank += 1
        
        logger.info(f"Monthly rankings updated for {last_year}-{last_month:02d}")
    
    except Exception as e:
        logger.error(f"Error updating monthly rankings: {e}")

