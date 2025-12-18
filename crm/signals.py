"""
Django signals for CRM app
Lead status o'zgarishlari, follow-up yaratish, eslatmalar
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta


@receiver(pre_save, sender='crm.Lead')
def track_lead_status_change(sender, instance, **kwargs):
    """
    Lead status o'zgarishini kuzatish
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
            instance._old_sales = old_instance.assigned_sales
        except sender.DoesNotExist:
            instance._old_status = None
            instance._old_sales = None
    else:
        instance._old_status = None
        instance._old_sales = None


@receiver(post_save, sender='crm.Lead')
def handle_lead_changes(sender, instance, created, **kwargs):
    """
    Lead yaratilganda yoki o'zgarganda
    """
    from .models import LeadHistory, FollowUp
    
    if created:
        # Yangi lead yaratildi
        if instance.status:
            LeadHistory.objects.create(
                lead=instance,
                new_status=instance.status,
                changed_by=instance.created_by,
                notes="Yangi lid yaratildi"
            )
        
        # Agar sotuvchi tayinlangan bo'lsa, follow-up yaratish
        if instance.assigned_sales:
            from .tasks import create_initial_followup
            create_initial_followup.delay(instance.id)
            
            # Telegram notification
            try:
                from telegram_bot.tasks import send_lead_assignment_notification
                send_lead_assignment_notification.delay(instance.id)
            except ImportError:
                pass
    
    else:
        # Status o'zgargan
        old_status = getattr(instance, '_old_status', None)
        if old_status != instance.status:
            LeadHistory.objects.create(
                lead=instance,
                old_status=old_status,
                new_status=instance.status,
                notes=f"Status o'zgardi: {old_status} → {instance.status}"
            )
            
            # Status bo'yicha follow-up yaratish
            if instance.status and instance.assigned_sales:
                from .tasks import create_status_followup
                create_status_followup.delay(instance.id, instance.status.code)
            
            # Lost status
            if instance.status and instance.status.code == 'lost' and not instance.lost_at:
                instance.lost_at = timezone.now()
                instance.save(update_fields=['lost_at'])
            
            # Enrolled status
            if instance.status and instance.status.code == 'enrolled' and not instance.enrolled_at:
                instance.enrolled_at = timezone.now()
                instance.save(update_fields=['enrolled_at'])
        
        # Sotuvchi o'zgargan
        old_sales = getattr(instance, '_old_sales', None)
        if old_sales != instance.assigned_sales and instance.assigned_sales:
            LeadHistory.objects.create(
                lead=instance,
                notes=f"Sotuvchi o'zgardi: {old_sales} → {instance.assigned_sales}"
            )
            
            # Telegram notification
            try:
                from telegram_bot.tasks import send_lead_assignment_notification
                send_lead_assignment_notification.delay(instance.id)
            except ImportError:
                pass


@receiver(post_save, sender='crm.TrialLesson')
def handle_trial_lesson(sender, instance, created, **kwargs):
    """
    Sinov darsi yaratilganda yoki natija kiritilganda
    """
    from .models import LeadStatus, FollowUp
    
    if created:
        # Lead statusini yangilash
        trial_status = LeadStatus.objects.filter(code='trial_registered').first()
        if trial_status:
            lead = instance.lead
            lead.status = trial_status
            lead.trial_date = instance.date
            lead.trial_time = instance.time
            lead.trial_group = instance.group
            lead.trial_room = instance.room
            lead.save()
        
        # Eslatma yuborish
        try:
            from telegram_bot.tasks import send_trial_reminder
            send_trial_reminder.delay(instance.id)
        except ImportError:
            pass
    
    # Sinov natijasi kiritilganda
    if instance.result:
        lead = instance.lead
        
        status_map = {
            'attended': 'trial_attended',
            'not_attended': 'trial_not_attended',
            'accepted': 'enrolled',
            'rejected': 'lost'
        }
        
        status_code = status_map.get(instance.result)
        if status_code:
            new_status = LeadStatus.objects.filter(code=status_code).first()
            if new_status and lead.status != new_status:
                lead.status = new_status
                lead.trial_result = instance.result
                
                if instance.result == 'accepted':
                    lead.enrolled_at = timezone.now()
                    lead.enrolled_group = instance.group
                elif instance.result == 'rejected':
                    lead.lost_at = timezone.now()
                
                lead.save()
        
        # Follow-up yaratish (90 daqiqadan keyin)
        if lead.assigned_sales and instance.result in ['attended', 'not_attended']:
            due_date = timezone.now() + timedelta(minutes=90)
            due_date = FollowUp.calculate_work_hours_due_date(lead.assigned_sales, due_date)
            
            FollowUp.objects.create(
                lead=lead,
                sales=lead.assigned_sales,
                due_date=due_date,
                notes=f"Sinov darsi natijasi: {instance.get_result_display()}"
            )


@receiver(post_save, sender='crm.FollowUp')
def handle_followup_completion(sender, instance, created, **kwargs):
    """
    Follow-up bajarilganda keyingi follow-up yaratish
    """
    from .models import FollowUp, LeadStatus
    
    if not created and instance.completed and instance.lead.assigned_sales:
        lead = instance.lead
        
        # Contacted statusidagi lidlar uchun ketma-ket follow-up'lar
        if lead.status and lead.status.code == 'contacted':
            # Ketma-ketlik: 24, 48, 72 soat
            sequence = instance.followup_sequence
            
            if sequence < 4:  # Maksimum 3 ta follow-up
                intervals = {1: 24, 2: 48, 3: 72}
                hours = intervals.get(sequence, 24)
                
                due_date = timezone.now() + timedelta(hours=hours)
                due_date = FollowUp.calculate_work_hours_due_date(lead.assigned_sales, due_date)
                
                # Mavjud follow-up bormi tekshirish
                existing = FollowUp.objects.filter(
                    lead=lead,
                    followup_sequence=sequence + 1
                ).exists()
                
                if not existing:
                    FollowUp.objects.create(
                        lead=lead,
                        sales=lead.assigned_sales,
                        due_date=due_date,
                        notes=f"Follow-up #{sequence + 1} ({hours} soat keyin)",
                        followup_sequence=sequence + 1
                    )


@receiver(post_save, sender='crm.Leave')
def handle_leave_approval(sender, instance, created, **kwargs):
    """
    Ruxsat tasdiqlanganda SalesProfile yangilash
    """
    from .models import SalesProfile
    
    if not created and instance.status == 'approved':
        if hasattr(instance.sales, 'sales_profile'):
            profile = instance.sales.sales_profile
            profile.is_on_leave = True
            profile.save()
        
        # Telegram notification
        try:
            from telegram_bot.tasks import send_leave_approved_notification
            send_leave_approved_notification.delay(instance.id)
        except ImportError:
            pass


@receiver(post_save, sender='crm.SalesMessage')
def handle_message_send(sender, instance, created, **kwargs):
    """
    Xabar yuborilganda Telegram orqali ham yuborish
    """
    if created and not instance.telegram_sent:
        try:
            from telegram_bot.tasks import send_sales_message
            send_sales_message.delay(instance.id)
            
            instance.telegram_sent = True
            instance.save(update_fields=['telegram_sent'])
        except ImportError:
            pass
