from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.models import User, Branch


class Course(models.Model):
    """
    Kurslar
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='courses')
    duration_weeks = models.IntegerField(default=12)  # Haftalar soni
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'branch']),
        ]
    
    def __str__(self):
        return self.name


class Module(models.Model):
    """
    Modullar (kurs ichidagi bo'limlar)
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Module')
        verbose_name_plural = _('Modules')
        ordering = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.name} - {self.name}"


class Topic(models.Model):
    """
    Mavzular (modul ichidagi darslar)
    """
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    duration_minutes = models.IntegerField(default=90)  # Dars davomiyligi
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Topic')
        verbose_name_plural = _('Topics')
        ordering = ['module', 'order']
    
    def __str__(self):
        return f"{self.module.name} - {self.name}"


class TopicMaterial(models.Model):
    """
    Mavzu materiallari (video, fayl, link)
    """
    MATERIAL_TYPE_CHOICES = [
        ('video', 'Video'),
        ('file', 'Fayl'),
        ('link', 'Link'),
        ('text', 'Matn'),
    ]
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='materials')
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPE_CHOICES, default='text')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='materials/', blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)  # Matn materiallar uchun
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Topic Material')
        verbose_name_plural = _('Topic Materials')
        ordering = ['topic', 'order']
    
    def __str__(self):
        return f"{self.topic.name} - {self.title}"


class Room(models.Model):
    """
    Xonalar
    """
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='rooms')
    name = models.CharField(max_length=100)
    capacity = models.IntegerField(default=20)
    equipment = models.TextField(blank=True, null=True)  # Uskunalar ro'yxati
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Room')
        verbose_name_plural = _('Rooms')
        ordering = ['branch', 'name']
    
    def __str__(self):
        return f"{self.branch.name} - {self.name}"


class Group(models.Model):
    """
    Guruhlar
    """
    SCHEDULE_CHOICES = [
        ('odd', 'Toq kunlar'),
        ('even', 'Juft kunlar'),
        ('daily', 'Har kuni'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=200)
    mentor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='mentor_groups', limit_choices_to={'role': 'mentor'})
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='groups')
    students = models.ManyToManyField(User, related_name='student_groups', blank=True, 
                                     limit_choices_to={'role': 'student'})
    schedule_type = models.CharField(max_length=10, choices=SCHEDULE_CHOICES, default='odd')
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.IntegerField(default=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')
        ordering = ['course', 'name']
    
    def __str__(self):
        return f"{self.course.name} - {self.name}"
    
    @property
    def enrolled_students_count(self):
        """Enrolled students soni (trial students hisobga olinadi)"""
        from accounts.models import User
        return self.students.filter(role='student').count()
    
    @property
    def trial_students_count(self):
        """Trial students soni"""
        from crm.models import Lead
        return Lead.objects.filter(
            trial_group=self,
            status__code__in=['trial_registered', 'trial_attended']
        ).count()
    
    @property
    def total_students_count(self):
        """Jami students (enrolled + trial)"""
        return self.enrolled_students_count + self.trial_students_count
    
    @property
    def fill_percentage(self):
        """Guruh to'lish darajasi"""
        if self.capacity == 0:
            return 0
        return (self.total_students_count / self.capacity) * 100


class GroupTransfer(models.Model):
    """
    O'quvchini bir guruhdan boshqasiga ko'chirish
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_transfers',
                               limit_choices_to={'role': 'student'})
    from_group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='transfers_from')
    to_group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='transfers_to')
    reason = models.TextField(blank=True, null=True)
    transferred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='transfers_made',
                                     limit_choices_to={'role__in': ['admin', 'manager']})
    transferred_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = _('Group Transfer')
        verbose_name_plural = _('Group Transfers')
        ordering = ['-transferred_at']
        indexes = [
            models.Index(fields=['student', 'transferred_at']),
            models.Index(fields=['from_group', 'to_group']),
        ]
    
    def __str__(self):
        return f"{self.student.username}: {self.from_group.name} → {self.to_group.name}"
    
    def save(self, *args, **kwargs):
        # O'quvchini eski guruhdan olib tashlash va yangi guruhga qo'shish
        if not self.pk:  # Yangi transfer
            self.from_group.students.remove(self.student)
            self.to_group.students.add(self.student)
            
            # Progress yangilash (yangi guruhga ko'chirish)
            from .models import StudentProgress
            old_progress = StudentProgress.objects.filter(
                student=self.student,
                course=self.from_group.course
            ).first()
            
            if old_progress:
                # Yangi guruh kursiga progress yaratish/yangilash
                new_progress, created = StudentProgress.objects.get_or_create(
                    student=self.student,
                    course=self.to_group.course
                )
                # Agar kurs bir xil bo'lsa, progressni saqlab qolish
                if self.from_group.course == self.to_group.course:
                    new_progress.completed_topics.set(old_progress.completed_topics.all())
                    new_progress.calculate_progress()
        
        super().save(*args, **kwargs)


class Lesson(models.Model):
    """
    Darslar
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='lessons')
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)  # Mentor uchun eslatmalar
    questions = models.TextField(blank=True, null=True)  # Savollar ro'yxati
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Lesson')
        verbose_name_plural = _('Lessons')
        ordering = ['-date', '-start_time']
        indexes = [
            models.Index(fields=['group', 'date']),
            models.Index(fields=['date', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.group.name} - {self.date} {self.start_time}"


class StudentProgress(models.Model):
    """
    O'quvchi progressi (kurs bo'yicha)
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_progress',
                               limit_choices_to={'role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='student_progress')
    progress_percentage = models.FloatField(default=0.0)  # 0-100%
    completed_topics = models.ManyToManyField(Topic, blank=True, related_name='completed_by_students')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Student Progress')
        verbose_name_plural = _('Student Progresses')
        unique_together = ['student', 'course']
        ordering = ['-progress_percentage']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.name} ({self.progress_percentage}%)"
    
    def calculate_progress(self):
        """Progress foizini hisoblash"""
        # Kursdagi barcha topiclar soni
        total_topics = Topic.objects.filter(module__course=self.course).count()
        
        if total_topics > 0:
            completed_count = self.completed_topics.count()
            self.progress_percentage = (completed_count / total_topics) * 100
        else:
            self.progress_percentage = 0.0
        
        self.save()
        return self.progress_percentage
