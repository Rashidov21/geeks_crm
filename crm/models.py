from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
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
        ('lost', "Yo'qotilgan"),
        ('reactivation', 'Qayta aloqa'),
    ]
    
    name = models.CharField(max_length=50, unique=True, verbose_name='Nomi')
    code = models.CharField(max_length=30, choices=STATUS_CHOICES, unique=True, verbose_name='Kod')
    order = models.IntegerField(default=0, verbose_name='Tartib')
    color = models.CharField(max_length=20, default='#3B82F6', verbose_name='Rang')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    
    class Meta:
        verbose_name = 'Lid statusi'
        verbose_name_plural = 'Lid statuslari'
        ordering = ['order']
    
    def __str__(self):
        return self.name


class Lead(models.Model):
    """
    Lidlar (potensial o'quvchilar)
    """
    SOURCE_CHOICES = [
        ('instagram', 'Instagram'),
        ('telegram', 'Telegram'),
        ('youtube', 'YouTube'),
        ('organic', 'Organik'),
        ('form', 'Veb-forma'),
        ('excel', 'Excel import'),
        ('google_sheets', 'Google Sheets'),
        ('referral', 'Tavsiya'),
        ('phone', 'Telefon'),
        ('walk_in', 'Tashrif'),
        ('other', 'Boshqa'),
    ]
    
    # Asosiy ma'lumotlar
    name = models.CharField(max_length=200, verbose_name='Ism', default='')
    phone = models.CharField(max_length=20, verbose_name='Telefon')
    secondary_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Qo'shimcha telefon")
    
    # Lead ma'lumotlari
    interested_course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, 
                                          related_name='leads', verbose_name='Qiziqayotgan kurs')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='other', verbose_name='Manba')
    status = models.ForeignKey(LeadStatus, on_delete=models.SET_NULL, null=True, related_name='leads',
                               verbose_name='Status')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='leads', verbose_name='Filial')
    
    # Sotuvchi
    assigned_sales = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='assigned_leads', 
                                       limit_choices_to={'role__in': ['sales', 'sales_manager']},
                                       verbose_name='Biriktirilgan sotuvchi')
    assigned_at = models.DateTimeField(null=True, blank=True, verbose_name='Biriktirilgan vaqt')
    
    # Sinov darsi
    trial_group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='trial_leads', verbose_name='Sinov guruhi')
    trial_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='trial_leads', verbose_name='Sinov xonasi')
    trial_date = models.DateField(blank=True, null=True, verbose_name='Sinov sanasi')
    trial_time = models.TimeField(blank=True, null=True, verbose_name='Sinov vaqti')
    trial_result = models.CharField(max_length=20, choices=[
        ('attended', 'Keldi'),
        ('not_attended', 'Kelmadi'),
        ('accepted', 'Qabul qildi'),
        ('rejected', 'Rad etdi'),
    ], blank=True, null=True, verbose_name='Sinov natijasi')
    
    # Status vaqtlari
    lost_at = models.DateTimeField(null=True, blank=True, verbose_name="Yo'qotilgan vaqt")
    enrolled_at = models.DateTimeField(null=True, blank=True, verbose_name='Yozilgan vaqt')
    enrolled_group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='enrolled_leads', verbose_name='Yozilgan guruh')
    
    # Qo'shimcha ma'lumotlar
    notes = models.TextField(blank=True, null=True, verbose_name='Izohlar')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='created_leads', verbose_name='Yaratuvchi')
    
    class Meta:
        verbose_name = 'Lid'
        verbose_name_plural = 'Lidlar'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['assigned_sales', 'status']),
            models.Index(fields=['branch', 'status']),
            models.Index(fields=['trial_date', 'trial_time']),
            models.Index(fields=['phone']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.phone}"
    
    @property
    def days_in_status(self):
        """Statusda qancha kun bo'lgan"""
        if self.status:
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
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='history',
                             verbose_name='Lid')
    old_status = models.ForeignKey(LeadStatus, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='old_status_history', verbose_name='Eski status')
    new_status = models.ForeignKey(LeadStatus, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='new_status_history', verbose_name='Yangi status')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='lead_history_changes', verbose_name="O'zgartiruvchi")
    notes = models.TextField(blank=True, null=True, verbose_name='Izohlar')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')
    
    class Meta:
        verbose_name = 'Lid tarixi'
        verbose_name_plural = 'Lid tarixlari'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lead', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.lead.name} - {self.old_status} → {self.new_status}"


class FollowUp(models.Model):
    """
    Follow-up vazifalar
    """
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='followups',
                             verbose_name='Lid')
    sales = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followups',
                              limit_choices_to={'role__in': ['sales', 'sales_manager']},
                              verbose_name='Sotuvchi')
    due_date = models.DateTimeField(verbose_name='Bajarish vaqti', default=timezone.now)
    completed = models.BooleanField(default=False, verbose_name='Bajarildi')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Bajarilgan vaqt')
    notes = models.TextField(blank=True, null=True, verbose_name='Izohlar')
    is_overdue = models.BooleanField(default=False, verbose_name='Kechikkan')
    reminder_sent = models.BooleanField(default=False, verbose_name='Eslatma yuborildi')
    followup_sequence = models.IntegerField(default=1, verbose_name='Ketma-ketlik raqami')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')
    
    class Meta:
        verbose_name = 'Follow-up'
        verbose_name_plural = 'Follow-uplar'
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['sales', 'due_date']),
            models.Index(fields=['completed', 'due_date']),
            models.Index(fields=['is_overdue', 'due_date']),
            models.Index(fields=['lead', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.lead.name} - {self.due_date.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Overdue tekshirish
        if not self.completed and self.due_date < timezone.now():
            self.is_overdue = True
        else:
            self.is_overdue = False
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def calculate_work_hours_due_date(sales_user, base_time):
        """
        Ish vaqti ichida bo'lgan due_date hisoblash
        """
        from .models import WorkSchedule, Leave
        
        due_date = base_time
        max_iterations = 14  # Maksimum 2 hafta oldinga
        
        for _ in range(max_iterations):
            weekday = due_date.weekday()
            current_time = due_date.time()
            
            # Ruxsatda emasligini tekshirish
            on_leave = Leave.objects.filter(
                sales=sales_user,
                start_date__lte=due_date.date(),
                end_date__gte=due_date.date(),
                status='approved'
            ).exists()
            
            if on_leave:
                due_date = due_date + timedelta(days=1)
                due_date = due_date.replace(hour=9, minute=0, second=0)
                continue
            
            # Ish jadvalini tekshirish
            schedule = WorkSchedule.objects.filter(
                sales=sales_user,
                weekday=weekday,
                is_active=True
            ).first()
            
            if not schedule:
                due_date = due_date + timedelta(days=1)
                due_date = due_date.replace(hour=9, minute=0, second=0)
                continue
            
            # Ish vaqti ichidami?
            if current_time < schedule.start_time:
                due_date = due_date.replace(
                    hour=schedule.start_time.hour,
                    minute=schedule.start_time.minute,
                    second=0
                )
                return due_date
            elif current_time > schedule.end_time:
                due_date = due_date + timedelta(days=1)
                due_date = due_date.replace(hour=9, minute=0, second=0)
                continue
            else:
                return due_date
        
        return base_time


class TrialLesson(models.Model):
    """
    Sinov darslari
    """
    RESULT_CHOICES = [
        ('attended', 'Keldi'),
        ('not_attended', 'Kelmadi'),
        ('accepted', 'Qabul qildi'),
        ('rejected', 'Rad etdi'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='trial_lessons',
                             verbose_name='Lid')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='trial_lessons',
                              verbose_name='Guruh')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='trial_lessons', verbose_name='Xona')
    date = models.DateField(verbose_name='Sana')
    time = models.TimeField(verbose_name='Vaqt', null=True, blank=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, blank=True, null=True,
                              verbose_name='Natija')
    notes = models.TextField(blank=True, null=True, verbose_name='Izohlar')
    reminder_sent = models.BooleanField(default=False, verbose_name='Eslatma yuborildi')
    sales_reminder_sent = models.BooleanField(default=False, verbose_name='Sotuvchi eslatmasi')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')
    
    class Meta:
        verbose_name = 'Sinov darsi'
        verbose_name_plural = 'Sinov darslari'
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['lead', 'date']),
            models.Index(fields=['group', 'date']),
            models.Index(fields=['date', 'time']),
        ]
    
    def __str__(self):
        return f"{self.lead.name} - {self.group.name} - {self.date}"


class SalesProfile(models.Model):
    """
    Sotuvchi profili
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='sales_profile',
                                limit_choices_to={'role__in': ['sales', 'sales_manager']},
                                verbose_name='Foydalanuvchi')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='sales', verbose_name='Filial')
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True, 
                                        verbose_name='Telegram chat ID')
    telegram_group_id = models.CharField(max_length=50, blank=True, null=True,
                                         verbose_name='Telegram guruh ID')
    
    # Faollik holati
    is_active_sales = models.BooleanField(default=True, verbose_name='Faol sotuvchi')
    is_on_leave = models.BooleanField(default=False, verbose_name='Ruxsatda')
    is_absent = models.BooleanField(default=False, verbose_name='Ishda emas')
    absent_reason = models.TextField(blank=True, null=True, verbose_name='Ishda emaslik sababi')
    absent_from = models.DateTimeField(null=True, blank=True, verbose_name='Ishda emaslik boshlanishi')
    absent_until = models.DateTimeField(null=True, blank=True, verbose_name='Ishda emaslik tugashi')
    
    # Ish vaqti
    work_start_time = models.TimeField(default='09:00', verbose_name='Ish boshlanish vaqti')
    work_end_time = models.TimeField(default='18:00', verbose_name='Ish tugash vaqti')
    
    # Ish kunlari
    work_monday = models.BooleanField(default=True, verbose_name='Dushanba')
    work_tuesday = models.BooleanField(default=True, verbose_name='Seshanba')
    work_wednesday = models.BooleanField(default=True, verbose_name='Chorshanba')
    work_thursday = models.BooleanField(default=True, verbose_name='Payshanba')
    work_friday = models.BooleanField(default=True, verbose_name='Juma')
    work_saturday = models.BooleanField(default=True, verbose_name='Shanba')
    work_sunday = models.BooleanField(default=False, verbose_name='Yakshanba')
    
    max_leads_per_day = models.IntegerField(default=10, verbose_name='Kunlik maksimal lidlar')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')
    
    class Meta:
        verbose_name = 'Sotuvchi profili'
        verbose_name_plural = 'Sotuvchi profillari'
    
    def __str__(self):
        return f"{self.user.username} - Sotuvchi"
    
    def is_working_day(self, weekday):
        """Berilgan kun ish kunimi?"""
        days = [
            self.work_monday, self.work_tuesday, self.work_wednesday,
            self.work_thursday, self.work_friday, self.work_saturday, self.work_sunday
        ]
        return days[weekday]
    
    def is_working_now(self):
        """Hozir ish vaqtidami?"""
        now = timezone.now()
        if not self.is_working_day(now.weekday()):
            return False
        
        current_time = now.time()
        return self.work_start_time <= current_time <= self.work_end_time


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
                              limit_choices_to={'role__in': ['sales', 'sales_manager']},
                              verbose_name='Sotuvchi')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, verbose_name='Hafta kuni')
    start_time = models.TimeField(verbose_name='Boshlanish vaqti')
    end_time = models.TimeField(verbose_name='Tugash vaqti')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    
    class Meta:
        verbose_name = 'Ish jadvali'
        verbose_name_plural = 'Ish jadvallari'
        unique_together = ['sales', 'weekday']
        ordering = ['sales', 'weekday']
    
    def __str__(self):
        return f"{self.sales.username} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class Leave(models.Model):
    """
    Ruxsat so'rovlari
    """
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('approved', 'Tasdiqlandi'),
        ('rejected', 'Rad etildi'),
    ]
    
    sales = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaves',
                              limit_choices_to={'role__in': ['sales', 'sales_manager']},
                              verbose_name='Sotuvchi')
    start_date = models.DateField(verbose_name='Boshlanish sanasi')
    end_date = models.DateField(verbose_name='Tugash sanasi')
    start_time = models.TimeField(blank=True, null=True, verbose_name='Boshlanish vaqti')
    end_time = models.TimeField(blank=True, null=True, verbose_name='Tugash vaqti')
    reason = models.TextField(verbose_name='Sabab')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending',
                              verbose_name='Holat')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_leaves',
                                    limit_choices_to={'role__in': ['admin', 'manager', 'sales_manager']},
                                    verbose_name='Tasdiqlagan')
    rejection_reason = models.TextField(blank=True, null=True, verbose_name='Rad etish sababi')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Tasdiqlangan vaqt')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')
    
    class Meta:
        verbose_name = "Ruxsat so'rovi"
        verbose_name_plural = "Ruxsat so'rovlari"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sales', 'start_date', 'end_date']),
            models.Index(fields=['status', 'start_date']),
        ]
    
    def __str__(self):
        return f"{self.sales.username} - {self.start_date} dan {self.end_date} gacha"
    
    @property
    def is_active(self):
        """Ruxsat hozirgi vaqtda faolmi?"""
        today = timezone.now().date()
        return self.status == 'approved' and self.start_date <= today <= self.end_date


class Offer(models.Model):
    """
    Takliflar
    """
    OFFER_TYPE_CHOICES = [
        ('discount', 'Chegirma'),
        ('bonus', 'Bonus'),
        ('package', 'Paket'),
        ('other', 'Boshqa'),
    ]
    
    PRIORITY_CHOICES = [
        ('urgent', 'Shoshilinch'),
        ('high', 'Yuqori'),
        ('normal', 'Oddiy'),
        ('low', 'Past'),
    ]
    
    CHANNEL_CHOICES = [
        ('all', 'Barchasi'),
        ('followup', 'Follow-up'),
        ('reactivation', 'Reaktivatsiya'),
        ('trial', 'Sinov'),
        ('general', 'Umumiy'),
    ]
    
    AUDIENCE_CHOICES = [
        ('all', 'Barchasi'),
        ('new', 'Yangi lidlar'),
        ('lost', "Yo'qotilgan"),
        ('reactivation', 'Reaktivatsiya'),
        ('trial', 'Sinov'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Sarlavha')
    description = models.TextField(verbose_name='Tavsif')
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPE_CHOICES, default='discount',
                                  verbose_name='Taklif turi')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal',
                                verbose_name='Muhimlik')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='all',
                               verbose_name='Kanal')
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all',
                                verbose_name='Auditoriya')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='offers', verbose_name='Kurs')
    valid_from = models.DateField(verbose_name='Boshlanish sanasi')
    valid_until = models.DateField(verbose_name='Tugash sanasi')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='created_offers', verbose_name='Yaratuvchi')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')
    
    class Meta:
        verbose_name = 'Taklif'
        verbose_name_plural = 'Takliflar'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'valid_from', 'valid_until']),
            models.Index(fields=['offer_type', 'is_active']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_valid(self):
        """Taklif hozir amalda ekanligini tekshirish"""
        today = timezone.now().date()
        return self.is_active and self.valid_from <= today <= self.valid_until


class Reactivation(models.Model):
    """
    Reaktivatsiya tracking
    """
    REACTIVATION_TYPE_CHOICES = [
        ('7_days', '7 kun'),
        ('14_days', '14 kun'),
        ('30_days', '30 kun'),
    ]
    
    RESULT_CHOICES = [
        ('contacted', 'Aloqa qilindi'),
        ('interested', 'Qiziqdi'),
        ('no_response', 'Javob yo\'q'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='reactivations',
                             verbose_name='Lid')
    days_since_lost = models.IntegerField(verbose_name="Yo'qotilganidan keyin kunlar")
    reactivation_type = models.CharField(max_length=10, choices=REACTIVATION_TYPE_CHOICES,
                                         verbose_name='Reaktivatsiya turi')
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='Yuborilgan vaqt')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, blank=True, null=True,
                              verbose_name='Natija')
    
    class Meta:
        verbose_name = 'Reaktivatsiya'
        verbose_name_plural = 'Reaktivatsiyalar'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['lead', 'reactivation_type']),
        ]
    
    def __str__(self):
        return f"{self.lead.name} - {self.reactivation_type}"


class SalesMessage(models.Model):
    """
    Manager/Admin dan sotuvchilarga xabarlar
    """
    PRIORITY_CHOICES = [
        ('urgent', 'Shoshilinch'),
        ('high', 'Yuqori'),
        ('normal', 'Oddiy'),
        ('low', 'Past'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_sales_messages',
                               limit_choices_to={'role__in': ['admin', 'manager', 'sales_manager']},
                               verbose_name='Yuboruvchi')
    recipients = models.ManyToManyField(User, related_name='received_sales_messages',
                                        limit_choices_to={'role__in': ['sales', 'sales_manager']},
                                        verbose_name='Qabul qiluvchilar')
    subject = models.CharField(max_length=200, verbose_name='Mavzu')
    message = models.TextField(verbose_name='Xabar')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal',
                                verbose_name='Muhimlik')
    telegram_sent = models.BooleanField(default=False, verbose_name='Telegram orqali yuborildi')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')
    
    class Meta:
        verbose_name = 'Sotuvchi xabari'
        verbose_name_plural = 'Sotuvchi xabarlari'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} - {self.subject}"


class SalesMessageRead(models.Model):
    """
    Xabar o'qilganligini kuzatish
    """
    message = models.ForeignKey(SalesMessage, on_delete=models.CASCADE, related_name='read_receipts',
                                verbose_name='Xabar')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reads',
                             verbose_name='Foydalanuvchi')
    read_at = models.DateTimeField(auto_now_add=True, verbose_name="O'qilgan vaqt")
    
    class Meta:
        verbose_name = "Xabar o'qilishi"
        verbose_name_plural = "Xabar o'qilishlari"
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.message.subject}"


class DailyKPI(models.Model):
    """
    Kunlik KPI
    """
    sales = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_kpis',
                              limit_choices_to={'role__in': ['sales', 'sales_manager']},
                              verbose_name='Sotuvchi')
    date = models.DateField(verbose_name='Sana')
    
    # KPI mezonlari
    daily_contacts = models.IntegerField(default=0, verbose_name='Kunlik aloqalar')
    daily_followups = models.IntegerField(default=0, verbose_name='Kunlik follow-uplar')
    followup_completion_rate = models.FloatField(default=0.0, verbose_name='Bajarilish foizi')
    trials_registered = models.IntegerField(default=0, verbose_name='Sinovga yozilganlar')
    trials_to_sales = models.IntegerField(default=0, verbose_name='Sinovdan sotuv')
    conversion_rate = models.FloatField(default=0.0, verbose_name='Konversiya foizi')
    response_time_minutes = models.FloatField(default=0.0, verbose_name='Javob vaqti (daqiqa)')
    overdue_count = models.IntegerField(default=0, verbose_name='Overdue soni')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')
    
    class Meta:
        verbose_name = 'Kunlik KPI'
        verbose_name_plural = 'Kunlik KPIlar'
        unique_together = ['sales', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['sales', 'date']),
        ]
    
    def __str__(self):
        return f"{self.sales.username} - {self.date}"


class SalesKPI(models.Model):
    """
    Oylik sotuvchi KPI
    """
    sales = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_kpis',
                              limit_choices_to={'role__in': ['sales', 'sales_manager']},
                              verbose_name='Sotuvchi')
    month = models.IntegerField(verbose_name='Oy')
    year = models.IntegerField(verbose_name='Yil')
    
    # KPI mezonlari
    total_contacts = models.IntegerField(default=0, verbose_name='Jami aloqalar')
    followup_completion_rate = models.FloatField(default=0.0, verbose_name='Follow-up bajarilishi')
    conversion_rate = models.FloatField(default=0.0, verbose_name='Konversiya foizi')
    average_response_time = models.FloatField(default=0.0, verbose_name="O'rtacha javob vaqti")
    overdue_followups = models.IntegerField(default=0, verbose_name='Overdue follow-uplar')
    enrolled_leads = models.IntegerField(default=0, verbose_name='Yozilgan lidlar')
    
    total_kpi_score = models.FloatField(default=0.0, verbose_name='Umumiy KPI ball')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')
    
    class Meta:
        verbose_name = 'Oylik KPI'
        verbose_name_plural = 'Oylik KPIlar'
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
        self.total_kpi_score = 0
        
        # 1. Follow-up completion rate (30% vazn)
        self.total_kpi_score += self.followup_completion_rate * 0.30
        
        # 2. Conversion rate (30% vazn)
        self.total_kpi_score += self.conversion_rate * 0.30
        
        # 3. Response time (20% vazn)
        if self.average_response_time > 0:
            response_score = max(0, 100 - (self.average_response_time / 60))
            self.total_kpi_score += response_score * 0.20
        
        # 4. Overdue follow-ups (10% vazn)
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


# Eski Message modelini saqlab qolamiz (backward compatibility uchun)
class Message(models.Model):
    """
    Eski xabar modeli (deprecated - SalesMessage ishlatilsin)
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
                                  null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Xabar (eski)'
        verbose_name_plural = 'Xabarlar (eski)'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username if self.recipient else 'All'} - {self.title}"
