from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Foydalanuvchi modeli - rol asosida ruxsat tizimi bilan
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Menejer'),
        ('mentor', 'Mentor'),
        ('student', "O'quvchi"),
        ('parent', 'Ota-ona'),
        ('accountant', 'Buxgalter'),
        ('sales', 'Sotuvchi'),
        ('sales_manager', 'Sotuvchilar menejeri'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', verbose_name='Rol')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefon')
    telegram_id = models.BigIntegerField(blank=True, null=True, unique=True, verbose_name='Telegram ID')
    telegram_username = models.CharField(max_length=100, blank=True, null=True, verbose_name='Telegram username')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Avatar')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan sana')
    
    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['telegram_id']),
            models.Index(fields=['created_at']),
        ]
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

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
    Filiallar
    """
    name = models.CharField(max_length=200, verbose_name='Nomi')
    address = models.TextField(blank=True, null=True, verbose_name='Manzil')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefon')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan sana')
    
    class Meta:
        verbose_name = 'Filial'
        verbose_name_plural = 'Filiallar'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class StudentProfile(models.Model):
    """
    O'quvchi profili
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', 
                                limit_choices_to={'role': 'student'}, verbose_name='Foydalanuvchi')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='students', verbose_name='Filial')
    birth_date = models.DateField(blank=True, null=True, verbose_name="Tug'ilgan sana")
    address = models.TextField(blank=True, null=True, verbose_name='Manzil')
    parent_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='Ota-ona ismi')
    parent_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Ota-ona telefoni')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan sana')
    
    class Meta:
        verbose_name = "O'quvchi profili"
        verbose_name_plural = "O'quvchi profillari"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - O'quvchi"


class ParentProfile(models.Model):
    """
    Ota-ona profili
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile',
                                limit_choices_to={'role': 'parent'}, verbose_name='Foydalanuvchi')
    students = models.ManyToManyField(User, related_name='parents', limit_choices_to={'role': 'student'},
                                     verbose_name="O'quvchilar")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan sana')
    
    class Meta:
        verbose_name = 'Ota-ona profili'
        verbose_name_plural = 'Ota-ona profillari'
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Ota-ona"
