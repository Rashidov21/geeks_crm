from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.models import User, Branch
from courses.models import Group, Lesson
from homework.models import Homework
from exams.models import ExamResult
from attendance.models import Attendance


class PointTransaction(models.Model):
    """
    Ball transaksiyalari (har bir harakat uchun)
    """
    POINT_TYPE_CHOICES = [
        ('attendance_present', 'Darsga qatnashish'),
        ('homework_on_time', 'Uy vazifani vaqtida topshirish'),
        ('homework_late', 'Uy vazifani kech topshirish'),
        ('attendance_absent', 'Darsni qoldirish'),
        ('exam_high_score', 'Imtihondan yuqori ball'),
        ('badge_earned', 'Badge olish'),
        ('manual', 'Qo\'lda qo\'shish'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_transactions',
                               limit_choices_to={'role': 'student'})
    points = models.IntegerField()  # + yoki - ball
    point_type = models.CharField(max_length=30, choices=POINT_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    
    # Related objects (optional)
    attendance = models.ForeignKey(Attendance, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='point_transactions')
    homework = models.ForeignKey(Homework, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='point_transactions')
    exam_result = models.ForeignKey(ExamResult, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='point_transactions')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Point Transaction')
        verbose_name_plural = _('Point Transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'created_at']),
            models.Index(fields=['point_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.points} ball - {self.get_point_type_display()}"


class StudentPoints(models.Model):
    """
    O'quvchi umumiy ballari (guruh bo'yicha)
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_points',
                               limit_choices_to={'role': 'student'})
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='student_points')
    total_points = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Student Points')
        verbose_name_plural = _('Student Points')
        unique_together = ['student', 'group']
        ordering = ['-total_points']
        indexes = [
            models.Index(fields=['group', 'total_points']),
            models.Index(fields=['student', 'group']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.group.name} - {self.total_points} ball"
    
    def calculate_total_points(self):
        """Jami ballarni hisoblash"""
        transactions = PointTransaction.objects.filter(
            student=self.student,
            created_at__gte=self.group.created_at
        )
        
        # Guruhga tegishli transaksiyalarni filtrlash
        group_transactions = []
        for transaction in transactions:
            if transaction.attendance and transaction.attendance.lesson.group == self.group:
                group_transactions.append(transaction)
            elif transaction.homework and transaction.homework.lesson.group == self.group:
                group_transactions.append(transaction)
            elif transaction.exam_result and transaction.exam_result.exam.group == self.group:
                group_transactions.append(transaction)
            elif transaction.point_type == 'manual':
                # Manual balllar barcha guruhlar uchun
                group_transactions.append(transaction)
        
        self.total_points = sum(t.points for t in group_transactions)
        self.save()
        return self.total_points


class Badge(models.Model):
    """
    Badge/Medallar
    """
    BADGE_TYPE_CHOICES = [
        ('top_student', 'Top Student'),
        ('perfect_attendance', 'Perfect Attendance'),
        ('fast_learner', 'Fast Learner'),
        ('homework_master', 'Homework Master'),
        ('champion_month', 'Champion of the Month'),
        ('exam_champion', 'Exam Champion'),
        ('consistent_learner', 'Consistent Learner'),
    ]
    
    name = models.CharField(max_length=200)
    badge_type = models.CharField(max_length=30, choices=BADGE_TYPE_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=100, default='🏆')  # Emoji yoki icon class
    points_required = models.IntegerField(default=0)  # Bu badge uchun kerakli ball
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Badge')
        verbose_name_plural = _('Badges')
        ordering = ['points_required']
    
    def __str__(self):
        return f"{self.icon} {self.name}"


class StudentBadge(models.Model):
    """
    O'quvchilarning badge'lari
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges',
                               limit_choices_to={'role': 'student'})
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='student_badges')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='student_badges',
                             null=True, blank=True)  # Guruh bo'yicha badge
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Student Badge')
        verbose_name_plural = _('Student Badges')
        unique_together = ['student', 'badge', 'group']
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['student', 'earned_at']),
            models.Index(fields=['badge', 'earned_at']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.badge.name}"


class GroupRanking(models.Model):
    """
    Guruh bo'yicha reyting
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='rankings')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_rankings',
                               limit_choices_to={'role': 'student'})
    rank = models.IntegerField()  # O'rin (1, 2, 3...)
    total_points = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Group Ranking')
        verbose_name_plural = _('Group Rankings')
        unique_together = ['group', 'student']
        ordering = ['group', 'rank']
        indexes = [
            models.Index(fields=['group', 'rank']),
            models.Index(fields=['student', 'group']),
        ]
    
    def __str__(self):
        return f"{self.group.name} - {self.student.username} - {self.rank} o'rin"


class BranchRanking(models.Model):
    """
    Filial bo'yicha reyting
    """
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='rankings')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='branch_rankings',
                               limit_choices_to={'role': 'student'})
    rank = models.IntegerField()
    total_points = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Branch Ranking')
        verbose_name_plural = _('Branch Rankings')
        unique_together = ['branch', 'student']
        ordering = ['branch', 'rank']
        indexes = [
            models.Index(fields=['branch', 'rank']),
            models.Index(fields=['student', 'branch']),
        ]
    
    def __str__(self):
        return f"{self.branch.name} - {self.student.username} - {self.rank} o'rin"


class OverallRanking(models.Model):
    """
    Markaz bo'yicha umumiy reyting
    """
    student = models.OneToOneField(User, on_delete=models.CASCADE, related_name='overall_ranking',
                                  limit_choices_to={'role': 'student'})
    rank = models.IntegerField()
    total_points = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Overall Ranking')
        verbose_name_plural = _('Overall Rankings')
        ordering = ['rank']
        indexes = [
            models.Index(fields=['rank']),
            models.Index(fields=['total_points']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.rank} o'rin - {self.total_points} ball"


class MonthlyRanking(models.Model):
    """
    Oylik reyting (Top-10, Top-25, Top-50, Top-100)
    """
    RANKING_TYPE_CHOICES = [
        ('top_10', 'Top 10'),
        ('top_25', 'Top 25'),
        ('top_50', 'Top 50'),
        ('top_100', 'Top 100'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_rankings',
                               limit_choices_to={'role': 'student'})
    ranking_type = models.CharField(max_length=10, choices=RANKING_TYPE_CHOICES)
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    rank = models.IntegerField()
    total_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Monthly Ranking')
        verbose_name_plural = _('Monthly Rankings')
        unique_together = ['student', 'ranking_type', 'month', 'year']
        ordering = ['year', 'month', 'ranking_type', 'rank']
        indexes = [
            models.Index(fields=['year', 'month', 'ranking_type', 'rank']),
            models.Index(fields=['student', 'year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.get_ranking_type_display()} - {self.year}-{self.month:02d} - {self.rank} o'rin"
