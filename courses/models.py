from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User, Branch


class Course(models.Model):
    """
    Kurslar
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    duration_months = models.IntegerField(default=6)  # Oylar soni
    total_lessons = models.IntegerField(default=0)  # Jami darslar soni
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='courses')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'branch']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.name


class Module(models.Model):
    """
    Kurs modullari
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)  # Tartib raqami
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Module')
        verbose_name_plural = _('Modules')
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.name} - {self.name}"


class Topic(models.Model):
    """
    Mavzular
    """
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
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
    Mavzu materiallari (video, PDF, matn, topshiriq)
    """
    MATERIAL_TYPE_CHOICES = [
        ('video', 'Video'),
        ('text', 'Matn'),
        ('pdf', 'PDF'),
        ('file', 'Fayl'),
        ('assignment', 'Amaliy topshiriq'),
    ]
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='materials')
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)  # Matn uchun
    file = models.FileField(upload_to='materials/', blank=True, null=True)  # PDF, video, fayl uchun
    video_url = models.URLField(blank=True, null=True)  # Video link uchun
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
    capacity = models.IntegerField(default=20)  # Sig'imi
    description = models.TextField(blank=True, null=True)
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
            status__in=['trial_registered', 'trial_attended']
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
    homework_description = models.TextField(blank=True, null=True)  # Uy vazifasi
    mentor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='lessons', limit_choices_to={'role': 'mentor'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Lesson')
        verbose_name_plural = _('Lessons')
        ordering = ['-date', '-start_time']
        indexes = [
            models.Index(fields=['date', 'start_time']),
            models.Index(fields=['group', 'date']),
            models.Index(fields=['mentor', 'date']),
        ]
    
    def __str__(self):
        return f"{self.group.name} - {self.date} {self.start_time}"


class StudentProgress(models.Model):
    """
    O'quvchi progressi (har bir kurs uchun)
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progresses',
                                limit_choices_to={'role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='student_progresses')
    progress_percentage = models.FloatField(default=0.0)  # 0-100%
    completed_topics = models.ManyToManyField(Topic, related_name='completed_by_students', blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Student Progress')
        verbose_name_plural = _('Student Progresses')
        unique_together = ['student', 'course']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.name} ({self.progress_percentage}%)"
    
    def calculate_progress(self):
        """Progress foizini hisoblash"""
        total_topics = Topic.objects.filter(module__course=self.course).count()
        if total_topics == 0:
            self.progress_percentage = 0.0
        else:
            completed_count = self.completed_topics.count()
            self.progress_percentage = (completed_count / total_topics) * 100
        self.save()
        return self.progress_percentage
