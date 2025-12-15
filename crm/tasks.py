"""
Celery tasks for CRM app
Avtomatik follow-up, taqsimlash, reaktivatsiya
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from .models import (
    Lead, LeadStatus, FollowUp, SalesProfile, WorkSchedule, Leave,
    SalesKPI, LeadHistory
)
from accounts.models import User
import logging

logger = logging.getLogger(__name__)


@shared_task
def assign_leads_to_sales():
    """
    Yangi lidlarni sotuvchilarga avtomatik taqsimlash
    """
    try:
        # Yangi lidlar (status = 'new')
        new_status = LeadStatus.objects.filter(code='new').first()
        if not new_status:
            return
        
        new_leads = Lead.objects.filter(
            status=new_status,
            sales__isnull=True
        )
        
        # Ish vaqtida bo'lgan sotuvchilar
        now = timezone.now()
        weekday = now.weekday()  # 0 = Monday
        
        # Ish vaqtida bo'lgan sotuvchilar
        available_sales = get_available_sales(weekday, now.time())
        
        if not available_sales:
            logger.warning("Ish vaqtida bo'lgan sotuvchilar topilmadi")
            return
        
        # Har bir sotuvchi uchun bugungi lidlar sonini hisoblash
        sales_loads = {}
        for sales in available_sales:
            today_leads = Lead.objects.filter(
                sales=sales,
                assigned_at__date=now.date()
            ).count()
            
            sales_profile = SalesProfile.objects.filter(user=sales).first()
            max_leads = sales_profile.max_leads_per_day if sales_profile else 10
            
            if today_leads < max_leads:
                sales_loads[sales] = today_leads
        
        # Eng kam yuklangan sotuvchilarga taqsimlash
        for lead in new_leads:
            if not sales_loads:
                break
            
            # Eng kam yuklangan sotuvchini topish
            min_sales = min(sales_loads.items(), key=lambda x: x[1])[0]
            
            lead.sales = min_sales
            lead.assigned_at = now
            lead.save()
            
            # Load yangilash
            sales_loads[min_sales] += 1
            if sales_loads[min_sales] >= (SalesProfile.objects.filter(user=min_sales).first().max_leads_per_day if SalesProfile.objects.filter(user=min_sales).exists() else 10):
                del sales_loads[min_sales]
            
            # LeadHistory yaratish
            LeadHistory.objects.create(
                lead=lead,
                new_status=new_status,
                changed_by=None,  # Avtomatik
                notes=f"Avtomatik taqsimlandi: {min_sales.username}"
            )
            
            # 5 daqiqadan keyin follow-up yaratish
            create_initial_followup.delay(lead.id)
        
        logger.info(f"{new_leads.count()} ta lid taqsimlandi")
    
    except Exception as e:
        logger.error(f"Error assigning leads: {e}")


def get_available_sales(weekday, current_time):
    """
    Ish vaqtida bo'lgan sotuvchilarni topish
    """
    # Ruxsat olmagan sotuvchilar
    today = timezone.now().date()
    on_leave = Leave.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
        status='approved'
    ).values_list('sales_id', flat=True)
    
    # Ish jadvali bo'yicha
    work_schedules = WorkSchedule.objects.filter(
        weekday=weekday,
        is_active=True,
        start_time__lte=current_time,
        end_time__gte=current_time
    ).exclude(sales_id__in=on_leave)
    
    sales_ids = work_schedules.values_list('sales_id', flat=True)
    
    return User.objects.filter(
        id__in=sales_ids,
        role__in=['sales', 'sales_manager'],
        is_active=True
    )


@shared_task
def create_initial_followup(lead_id):
    """
    Yangi lid uchun dastlabki follow-up yaratish (5 daqiqadan keyin)
    """
    try:
        lead = Lead.objects.get(pk=lead_id)
        
        if not lead.sales:
            return
        
        FollowUp.objects.create(
            lead=lead,
            sales=lead.sales,
            title="Yangi lid bilan aloqa qilish",
            description=f"{lead.full_name} bilan aloqa qilish kerak",
            scheduled_at=timezone.now() + timedelta(minutes=5),
            priority='high'
        )
        
        logger.info(f"Initial follow-up created for lead {lead_id}")
    
    except Exception as e:
        logger.error(f"Error creating initial follow-up: {e}")


@shared_task
def create_contacted_followups():
    """
    'Aloqa qilindi' statusidagi lidlar uchun ketma-ket follow-up'lar
    """
    try:
        contacted_status = LeadStatus.objects.filter(code='contacted').first()
        if not contacted_status:
            return
        
        leads = Lead.objects.filter(status=contacted_status)
        
        for lead in leads:
            if not lead.sales:
                continue
            
            # Oxirgi follow-up ni topish
            last_followup = FollowUp.objects.filter(
                lead=lead,
                is_completed=True
            ).order_by('-completed_at').first()
            
            if not last_followup:
                continue
            
            # Keyingi follow-up'lar: 24 soat, 3 kun, 7 kun, 14 kun
            intervals = [24, 72, 168, 336]  # Soatlar
            
            for hours in intervals:
                next_time = last_followup.completed_at + timedelta(hours=hours)
                
                # Agar hali yaratilmagan bo'lsa
                existing = FollowUp.objects.filter(
                    lead=lead,
                    scheduled_at=next_time
                ).exists()
                
                if not existing and next_time > timezone.now():
                    FollowUp.objects.create(
                        lead=lead,
                        sales=lead.sales,
                        title=f"Follow-up ({hours//24} kun keyin)",
                        description=f"{lead.full_name} bilan qayta aloqa qilish",
                        scheduled_at=next_time,
                        priority='medium'
                    )
    
    except Exception as e:
        logger.error(f"Error creating contacted followups: {e}")


@shared_task
def create_trial_followup(trial_lesson_id):
    """
    Sinov darsi tugagandan keyin follow-up yaratish (90 minutdan keyin)
    """
    try:
        from .models import TrialLesson
        
        trial = TrialLesson.objects.get(pk=trial_lesson_id)
        lead = trial.lead
        
        if not lead.sales:
            return
        
        FollowUp.objects.create(
            lead=lead,
            sales=lead.sales,
            title="Sinov darsi natijasini muhokama qilish",
            description=f"{lead.full_name} bilan sinov darsi natijasini muhokama qilish",
            scheduled_at=timezone.now() + timedelta(minutes=90),
            priority='high'
        )
        
        logger.info(f"Trial follow-up created for lead {lead.id}")
    
    except Exception as e:
        logger.error(f"Error creating trial follow-up: {e}")


@shared_task
def check_overdue_followups():
    """
    Overdue follow-up'larni tekshirish va yangilash
    """
    try:
        overdue_followups = FollowUp.objects.filter(
            is_completed=False,
            scheduled_at__lt=timezone.now()
        )
        
        for followup in overdue_followups:
            followup.is_overdue = True
            followup.save()
        
        logger.info(f"Checked {overdue_followups.count()} overdue followups")
    
    except Exception as e:
        logger.error(f"Error checking overdue followups: {e}")


@shared_task
def reactivate_lost_leads():
    """
    Yo'qotilgan lidlarni reaktivatsiya qilish (7, 14, 30 kun keyin)
    """
    try:
        lost_status = LeadStatus.objects.filter(code='lost').first()
        if not lost_status:
            return
        
        # 7, 14, 30 kun oldin yo'qotilgan lidlar
        now = timezone.now()
        intervals = [7, 14, 30]  # Kunlar
        
        for days in intervals:
            target_date = now - timedelta(days=days)
            
            # Bu kunda yo'qotilgan lidlar
            lost_leads = Lead.objects.filter(
                status=lost_status
            )
            
            # LeadHistory dan aniq vaqtni topish
            for lead in lost_leads:
                lost_history = LeadHistory.objects.filter(
                    lead=lead,
                    new_status=lost_status
                ).order_by('-created_at').first()
                
                if lost_history and lost_history.created_at.date() == target_date.date():
                    # Reaktivatsiya follow-up yaratish
                    if lead.sales:
                        FollowUp.objects.create(
                            lead=lead,
                            sales=lead.sales,
                            title=f"Reaktivatsiya ({days} kun keyin)",
                            description=f"{lead.full_name} bilan qayta aloqa qilish",
                            scheduled_at=now + timedelta(hours=1),
                            priority='low'
                        )
        
        logger.info("Lost leads reactivation checked")
    
    except Exception as e:
        logger.error(f"Error reactivating lost leads: {e}")


@shared_task
def calculate_sales_kpi(month=None, year=None):
    """
    Sotuvchilar KPI ni hisoblash
    """
    try:
        if not month or not year:
            now = timezone.now()
            month = month or now.month
            year = year or now.year
        
        if sales_id:
            sales = User.objects.filter(pk=sales_id, role__in=['sales', 'sales_manager'], is_active=True)
        else:
            sales = User.objects.filter(role__in=['sales', 'sales_manager'], is_active=True)
        
        for sales_user in sales:
            kpi, created = SalesKPI.objects.get_or_create(
                sales=sales_user,
                month=month,
                year=year
            )
            
            # 1. Total contacts (bu oy ichida aloqa qilingan lidlar)
            contacted_status = LeadStatus.objects.filter(code='contacted').first()
            kpi.total_contacts = Lead.objects.filter(
                sales=sales_user,
                status=contacted_status,
                assigned_at__year=year,
                assigned_at__month=month
            ).count()
            
            # 2. Follow-up completion rate
            total_followups = FollowUp.objects.filter(
                sales=sales_user,
                scheduled_at__year=year,
                scheduled_at__month=month
            ).count()
            
            completed_followups = FollowUp.objects.filter(
                sales=sales_user,
                scheduled_at__year=year,
                scheduled_at__month=month,
                is_completed=True
            ).count()
            
            if total_followups > 0:
                kpi.followup_completion_rate = (completed_followups / total_followups) * 100
            
            # 3. Conversion rate (sinovdan sotuvga)
            trial_leads = Lead.objects.filter(
                sales=sales_user,
                status__code__in=['trial_registered', 'trial_attended'],
                assigned_at__year=year,
                assigned_at__month=month
            ).count()
            
            enrolled_leads = Lead.objects.filter(
                sales=sales_user,
                status__code='enrolled',
                assigned_at__year=year,
                assigned_at__month=month
            ).count()
            
            if trial_leads > 0:
                kpi.conversion_rate = (enrolled_leads / trial_leads) * 100
            
            kpi.enrolled_leads = enrolled_leads
            
            # 4. Average response time (soddalashtirilgan)
            # Birinchi follow-up ni bajarish vaqti
            first_followups = FollowUp.objects.filter(
                sales=sales_user,
                scheduled_at__year=year,
                scheduled_at__month=month,
                is_completed=True
            ).order_by('scheduled_at')
            
            if first_followups.exists():
                # O'rtacha javob vaqti
                total_time = 0
                count = 0
                for followup in first_followups:
                    if followup.completed_at:
                        response_time = (followup.completed_at - followup.scheduled_at).total_seconds() / 60
                        total_time += response_time
                        count += 1
                
                if count > 0:
                    kpi.average_response_time = total_time / count
            
            # 5. Overdue follow-ups
            kpi.overdue_followups = FollowUp.objects.filter(
                sales=sales_user,
                scheduled_at__year=year,
                scheduled_at__month=month,
                is_overdue=True
            ).count()
            
            # KPI hisoblash
            kpi.calculate_kpi()
        
        logger.info(f"Sales KPIs calculated for {month}/{year}")
    
    except Exception as e:
        logger.error(f"Error calculating sales KPIs: {e}")


@shared_task
def check_leave_expiry():
    """
    Ruxsatlar tugashini tekshirish
    """
    try:
        today = timezone.now().date()
        
        # Tugagan ruxsatlar
        expired_leaves = Leave.objects.filter(
            end_date__lt=today,
            status='approved'
        )
        
        # Statusni avtomatik yangilash (ishlatilmaydi, lekin log qilish mumkin)
        for leave in expired_leaves:
            logger.info(f"Leave expired: {leave.sales.username} - {leave.end_date}")
    
    except Exception as e:
        logger.error(f"Error checking leave expiry: {e}")

