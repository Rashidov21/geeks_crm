from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model with role-based access control
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('mentor', 'Mentor'),
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('accountant', 'Accountant'),
        ('sales', 'Sales'),
        ('sales_manager', 'Sales Manager'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True, null=True)
    telegram_id = models.BigIntegerField(blank=True, null=True, unique=True)
    telegram_username = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
    
    @property
    def is_manager(self):
        return self.role == 'manager'
    
    @property
    def is_mentor(self):
        return self.role == 'mentor'
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    @property
    def is_parent(self):
        return self.role == 'parent'
    
    @property
    def is_accountant(self):
        return self.role == 'accountant'
    
    @property
    def is_sales(self):
        return self.role == 'sales'
    
    @property
    def is_sales_manager(self):
        return self.role == 'sales_manager'


class Branch(models.Model):
    """
    Filiallar (branches)
    """
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Branch')
        verbose_name_plural = _('Branches')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class StudentProfile(models.Model):
    """
    Student profili
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', 
                                limit_choices_to={'role': 'student'})
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    birth_date = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    parent_name = models.CharField(max_length=200, blank=True, null=True)
    parent_phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Student Profile')
        verbose_name_plural = _('Student Profiles')
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Student"


class ParentProfile(models.Model):
    """
    Parent profili
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile',
                                limit_choices_to={'role': 'parent'})
    students = models.ManyToManyField(User, related_name='parents', limit_choices_to={'role': 'student'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Parent Profile')
        verbose_name_plural = _('Parent Profiles')
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Parent"
