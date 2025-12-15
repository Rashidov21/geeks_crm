"""
Django signals for Finance app
Avtomatik yangilanishlar
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Contract, Payment, PaymentPlan, PaymentHistory


@receiver(post_save, sender=Payment)
def create_payment_history(sender, instance, created, **kwargs):
    """
    To'lov yaratilganda yoki o'zgarganda tarix yaratish
    """
    if created:
        PaymentHistory.objects.create(
            payment=instance,
            action='created',
            new_value=f"To'lov yaratildi: {instance.amount} so'm",
            changed_by=instance.created_by,
            notes=f"To'lov raqami: {instance.payment_number}"
        )
    else:
        # Status o'zgargan
        if 'status' in kwargs.get('update_fields', []):
            old_status = Payment.objects.get(pk=instance.pk).status if Payment.objects.filter(pk=instance.pk).exists() else None
            
            if old_status != instance.status:
                PaymentHistory.objects.create(
                    payment=instance,
                    action='status_changed',
                    old_value=old_status,
                    new_value=instance.status,
                    changed_by=None,
                    notes=f"Status o'zgardi: {old_status} → {instance.status}"
                )


@receiver(post_save, sender=Contract)
def create_payment_plans(sender, instance, created, **kwargs):
    """
    Shartnoma yaratilganda to'lov rejasini avtomatik yaratish
    """
    if created and instance.status == 'active':
        # Oylik to'lov rejasi (soddalashtirilgan)
        from datetime import timedelta
        
        # Kurs davomiyligi bo'yicha oylik to'lovlar
        course_duration = instance.course.duration_weeks
        months = (course_duration // 4) or 1  # Haftalarni oylarga aylantirish
        
        # Har oy uchun to'lov rejasi
        monthly_amount = (instance.total_amount - instance.discount_amount) / months
        
        current_date = instance.start_date
        for i in range(1, months + 1):
            # Har oy uchun 30 kun qo'shish
            due_date = current_date + timedelta(days=30 * i)
            
            PaymentPlan.objects.create(
                contract=instance,
                installment_number=i,
                amount=monthly_amount,
                due_date=due_date
            )


@receiver(post_save, sender=Payment)
def update_contract_paid_amount(sender, instance, **kwargs):
    """
    To'lov yaratilganda yoki o'zgarganda contract paid_amount ni yangilash
    """
    if instance.status == 'completed':
        # Contract paid_amount ni qayta hisoblash
        total_paid = Payment.objects.filter(
            contract=instance.contract,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        instance.contract.paid_amount = total_paid
        instance.contract.save()

