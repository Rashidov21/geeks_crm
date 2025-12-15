"""
Django signals for CRM app
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Lead, FollowUp, TrialLesson
from telegram_bot.tasks import send_lead_assignment_notification, send_followup_reminder, send_trial_reminder


@receiver(post_save, sender=Lead)
def create_lead_history(sender, instance, created, **kwargs):
    """
    Lead status o'zgarganda tarix yaratish
    """
    if created:
        # Yangi lead
        if instance.status:
            LeadHistory.objects.create(
                lead=instance,
                new_status=instance.status,
                changed_by=instance.created_by,
                notes="Yangi lead yaratildi"
            )
    else:
        # Status o'zgargan
        if 'status' in kwargs.get('update_fields', []):
            old_status = Lead.objects.get(pk=instance.pk).status if Lead.objects.filter(pk=instance.pk).exists() else None
            
            if old_status != instance.status:
                LeadHistory.objects.create(
                    lead=instance,
                    old_status=old_status,
                    new_status=instance.status,
                    changed_by=None,  # Avtomatik yoki user
                    notes=f"Status o'zgardi: {old_status} → {instance.status}"
                )
        
        # Sotuvchi tayinlanganda
        if 'sales' in kwargs.get('update_fields', []) and instance.sales:
            from telegram_bot.tasks import send_lead_assignment_notification
            send_lead_assignment_notification.delay(instance.id)


@receiver(post_save, sender=TrialLesson)
def create_trial_followup_signal(sender, instance, created, **kwargs):
    """
    Sinov darsi yaratilganda eslatmalar va follow-up
    """
    if created:
        # Lead statusini yangilash
        trial_status = LeadStatus.objects.filter(code='trial_registered').first()
        if trial_status:
            instance.lead.status = trial_status
            instance.lead.trial_date = instance.date
            instance.lead.trial_time = instance.start_time
            instance.lead.trial_group = instance.group
            instance.lead.trial_room = instance.room
            instance.lead.save()
        
        # Eslatmalar yuborish
        from telegram_bot.tasks import send_trial_reminder
        send_trial_reminder.delay(instance.id)
    
    # Sinov natijasi kiritilganda
    if not created and 'result' in kwargs.get('update_fields', []):
        if instance.result:
            # Lead statusini yangilash
            if instance.result == 'attended':
                status = LeadStatus.objects.filter(code='trial_attended').first()
            elif instance.result == 'accepted':
                status = LeadStatus.objects.filter(code='offer_sent').first()
            elif instance.result == 'rejected':
                status = LeadStatus.objects.filter(code='lost').first()
            else:
                status = None
            
            if status:
                instance.lead.status = status
                instance.lead.trial_result = instance.result
                instance.lead.save()
            
            # 90 minutdan keyin follow-up
            from crm.tasks import create_trial_followup
            create_trial_followup.delay(instance.id)

