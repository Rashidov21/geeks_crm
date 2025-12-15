from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.models import User, Branch
from courses.models import Course, Group, Room


class LeadStatus(models.Model):
    """
    Lead statuslari
    """
    STATUS_CHOICES = [
        ('new', 'Yangi'),
        ('contacted', 'Aloqa qilindi'),
        ('interested', 'Qiziqmoqda'),
        ('trial_registered', 'Sinovga yozildi'),
        ('trial_attended', 'Sinovga keldi'),
        ('trial_not_attended', 'Sinovga kelmadi'),
        ('offer_sent', 'Sotuv taklifi'),
        ('enrolled', 'Kursga yozildi'),
        ('lost', 'Yo\'qotilgan'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=30, choices=STATUS_CHOICES, unique=True)
    order = models.IntegerField(default=0)
    color = models.CharField(max_length=20, default='#3B82F6')  # Kanban board uchun rang
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Lead Status')
        verbose_name_plural = _('Lead Statuses')
        ordering = ['order']
    
    def __str__(self):
        return self.name


class Lead(models.Model):
    """
    Leadlar (potensial o'quvchilar)
    """
    SOURCE_CHOICES = [
        ('website', 'Veb-sayt'),
        ('social_media', 'Ijtimoiy tarmoq'),
        ('referral', 'Tavsiya'),
        ('walk_in', 'Tashrif'),
        ('phone', 'Telefon'),
        ('other', 'Boshqa'),
    ]
    
    # Asosiy ma'lumotlar
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    telegram_username = models.CharField(max_length=100, blank=True, null=True)
    
    # Lead ma'lumotlari
    status = models.ForeignKey(LeadStatus, on_delete=models.SET_NULL, null=True, related_name='leads')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='other')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    
    # Sotuvchi
    sales = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='assigned_leads', limit_choices_to={'role__in': ['sales', 'sales_manager']})
    assigned_at = models.DateTimeField(null=True, blank=True)
    
    # Sinov darsi
    trial_group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='trial_leads')
    trial_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='trial_leads')
    trial_date = models.DateField(blank=True, null=True)
    trial_time = models.TimeField(blank=True, null=True)
    trial_result = models.CharField(max_length=20, choices=[
        ('attended', 'Keldi'),
        ('not_attended', 'Kelmadi'),
        ('accepted', 'Qabul qildi'),
        ('rejected', 'Rad etdi'),
    ], blank=True, null=True)
    
    # Qo'shimcha ma'lumotlar
    notes = models.TextField(blank=True, null=True)
    expected_start_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='created_leads')
    
    class Meta:
        verbose_name = _('Lead')
        verbose_name_plural = _('Leads')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['sales', 'status']),
            models.Index(fields=['branch', 'status']),
            models.Index(fields=['trial_date', 'trial_time']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name or ''} - {self.phone}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name or ''}".strip()
    
    @property
    def days_in_status(self):
        """Statusda qancha kun bo'lgan"""
        if self.status:
            # LeadHistory dan oxirgi status o'zgarishini topish
            last_change = LeadHistory.objects.filter(
                lead=self,
                new_status=self.status
            ).order_by('-created_at').first()
            
            if last_change:
                return (timezone.now() - last_change.created_at).days
        return 0


class LeadHistory(models.Model):
    """
    Lead tarixi (status o'zgarishlari)
    """
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='history')
    old_status = models.ForeignKey(LeadStatus, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='old_status_history')
    new_status = models.ForeignKey(LeadStatus, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='new_status_history')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='lead_history_changes')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Lead History')
        verbose_name_plural = _('Lead Histories')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lead', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.lead.full_name} - {self.old_status} → {self.new_status}"


class FollowUp(models.Model):
    """
    Follow-up vazifalar
    """
    PRIORITY_CHOICES = [
        ('high', 'Yuqori'),
        ('medium', 'O\'rtacha'),
        ('low', 'Past'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='followups')
    sales = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followups',
                             limit_choices_to={'role__in': ['sales', 'sales_manager']})
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    scheduled_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_overdue = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Follow Up')
        verbose_name_plural = _('Follow Ups')
        ordering = ['scheduled_at']
        indexes = [
            models.Index(fields=['sales', 'scheduled_at']),
            models.Index(fields=['is_completed', 'scheduled_at']),
            models.Index(fields=['is_overdue', 'scheduled_at']),
            models.Index(fields=['lead', 'scheduled_at']),
        ]
    
    def __str__(self):
        return f"{self.lead.full_name} - {self.title} - {self.scheduled_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Overdue tekshirish
        if not self.is_completed and self.scheduled_at < timezone.now():
            self.is_overdue = True
        else:
            self.is_overdue = False
        
        super().save(*args, **kwargs)


class TrialLesson(models.Model):
    """
    Sinov darslari
    """
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='trial_lessons')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='trial_lessons')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='trial_lessons')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    result = models.CharField(max_length=20, choices=[
        ('attended', 'Keldi'),
        ('not_attended', 'Kelmadi'),
        ('accepted', 'Qabul qildi'),
        ('rejected', 'Rad etdi'),
    ], blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Trial Lesson')
        verbose_name_plural = _('Trial Lessons')
        ordering = ['-date', '-start_time']
        indexes = [
            models.Index(fields=['lead', 'date']),
            models.Index(fields=['group', 'date']),
            models.Index(fields=['date', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.lead.full_name} - {self.group.name} - {self.date}"


class SalesProfile(models.Model):
    """
    Sotuvchi profili
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='sales_profile',
                               limit_choices_to={'role__in': ['sales', 'sales_manager']})
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='sales')
    is_active = models.BooleanField(default=True)
    max_leads_per_day = models.IntegerField(default=10)  # Kuniga maksimal lidlar soni
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Sales Profile')
        verbose_name_plural = _('Sales Profiles')
    
    def __str__(self):
        return f"{self.user.username} - Sales"


class WorkSchedule(models.Model):
    """
    Sotuvchi ish jadvali
    """
    WEEKDAY_CHOICES = [
        (0, 'Dushanba'),
        (1, 'Seshanba'),
        (2, 'Chorshanba'),
        (3, 'Payshanba'),
        (4, 'Juma'),
        (5, 'Shanba'),
        (6, 'Yakshanba'),
    ]
    
    sales = models.ForeignKey(User, on_delete=models.CASCADE, related_name='work_schedules',
                             limit_choices_to={'role__in': ['sales', 'sales_manager']})
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Work Schedule')
        verbose_name_plural = _('Work Schedules')
        unique_together = ['sales', 'weekday']
        ordering = ['sales', 'weekday']
    
    def __str__(self):
        return f"{self.sales.username} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class Leave(models.Model):
    """
    Sotuvchi ruxsatlari
    """
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('approved', 'Tasdiqlandi'),
        ('rejected', 'Rad etildi'),
    ]
    
    sales = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaves',
                             limit_choices_to={'role__in': ['sales', 'sales_manager']})
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)  # Agar faqat bir kun bo'lsa
    end_time = models.TimeField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_leaves',
                                   limit_choices_to={'role__in': ['admin', 'manager', 'sales_manager']})
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Leave')
        verbose_name_plural = _('Leaves')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sales', 'start_date', 'end_date']),
            models.Index(fields=['status', 'start_date']),
        ]
    
    def __str__(self):
        return f"{self.sales.username} - {self.start_date} to {self.end_date}"
    
    @property
    def is_active(self):
        """Ruxsat hozirgi vaqtda faolmi?"""
        today = timezone.now().date()
        return self.status == 'approved' and self.start_date <= today <= self.end_date


class SalesKPI(models.Model):
    """
    Sotuvchi KPI
    """
    sales = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_kpis',
                             limit_choices_to={'role__in': ['sales', 'sales_manager']})
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    
    # KPI mezonlari
    total_contacts = models.IntegerField(default=0)  # Kunlik aloqalar soni
    followup_completion_rate = models.FloatField(default=0.0)  # Follow-up completion rate
    conversion_rate = models.FloatField(default=0.0)  # Sinovdan sotuvga conversion rate
    average_response_time = models.FloatField(default=0.0)  # O'rtacha javob berish vaqti (daqiqa)
    overdue_followups = models.IntegerField(default=0)  # Overdue follow-up'lar soni
    enrolled_leads = models.IntegerField(default=0)  # Kursga yozilgan lidlar
    
    total_kpi_score = models.FloatField(default=0.0)  # Umumiy KPI balli (0-100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Sales KPI')
        verbose_name_plural = _('Sales KPIs')
        unique_together = ['sales', 'month', 'year']
        ordering = ['-year', '-month', '-total_kpi_score']
        indexes = [
            models.Index(fields=['sales', 'year', 'month']),
            models.Index(fields=['total_kpi_score', 'year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.sales.username} - {self.year}-{self.month:02d} - {self.total_kpi_score:.1f} ball"
    
    def calculate_kpi(self):
        """KPI ballini hisoblash"""
        # Soddalashtirilgan hisoblash
        # Har bir mezon uchun ball (0-100)
        
        # 1. Follow-up completion rate (30% vazn)
        self.total_kpi_score += self.followup_completion_rate * 0.30
        
        # 2. Conversion rate (30% vazn)
        self.total_kpi_score += self.conversion_rate * 0.30
        
        # 3. Response time (20% vazn) - qisqa vaqt = yaxshi
        if self.average_response_time > 0:
            response_score = max(0, 100 - (self.average_response_time / 60))  # Soatga o'tkazib, 100 dan ayirish
            self.total_kpi_score += response_score * 0.20
        
        # 4. Overdue follow-ups (10% vazn) - kam overdue = yaxshi
        if self.total_contacts > 0:
            overdue_rate = (self.overdue_followups / self.total_contacts) * 100
            overdue_score = max(0, 100 - overdue_rate)
            self.total_kpi_score += overdue_score * 0.10
        
        # 5. Enrolled leads (10% vazn)
        if self.total_contacts > 0:
            enrolled_rate = (self.enrolled_leads / self.total_contacts) * 100
            self.total_kpi_score += enrolled_rate * 0.10
        
        self.save()
        return self.total_kpi_score


class Message(models.Model):
    """
    Manager/Admin dan sotuvchilarga xabarlar
    """
    PRIORITY_CHOICES = [
        ('urgent', 'Shoshilinch'),
        ('high', 'Yuqori'),
        ('normal', 'Oddiy'),
        ('low', 'Past'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages',
                              limit_choices_to={'role__in': ['admin', 'manager', 'sales_manager']})
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages',
                                 limit_choices_to={'role__in': ['sales', 'sales_manager']},
                                 null=True, blank=True)  # null = barcha sotuvchilar
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username if self.recipient else 'All'} - {self.title}"
