"""
Celery tasks for CRM app
Avtomatik follow-up, taqsimlash, reaktivatsiya, KPI hisoblash
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def import_leads_from_google_sheets():
    """
    Google Sheets'dan lidlarni import qilish (Har 5 daqiqa)
    """
    try:
        from .models import Lead, LeadStatus
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        from django.conf import settings
        
        # Google Sheets credentials
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        creds_file = getattr(settings, 'GOOGLE_SHEETS_CREDENTIALS', None)
        sheet_id = getattr(settings, 'GOOGLE_SHEETS_ID', None)
        
        if not creds_file or not sheet_id:
            logger.warning("Google Sheets credentials not configured")
            return
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(sheet_id).sheet1
        records = sheet.get_all_records()
        
        new_status = LeadStatus.objects.filter(code='new').first()
        imported = 0
        duplicates = 0
        
        for record in records:
            name = record.get('name', '').strip()
            phone = record.get('phone', '').strip()
            
            if not name or not phone:
                continue
            
            # Duplicate tekshirish
            if Lead.objects.filter(phone=phone).exists():
                duplicates += 1
                continue
            
            Lead.objects.create(
                name=name,
                phone=phone,
                secondary_phone=record.get('secondary_phone', ''),
                source='google_sheets',
                status=new_status
            )
            imported += 1
        
        logger.info(f"Google Sheets import: {imported} yangi, {duplicates} dublikat")
        
        # Import qilingan lidlarni avtomatik taqsimlash
        if imported > 0:
            assign_leads_to_sales.delay()
    
    except Exception as e:
        logger.error(f"Google Sheets import xatosi: {e}")


@shared_task
def assign_leads_to_sales():
    """
    Yangi lidlarni sotuvchilarga avtomatik taqsimlash
    """
    try:
        from .models import Lead, LeadStatus, LeadHistory, SalesProfile
        from accounts.models import User
        
        new_status = LeadStatus.objects.filter(code='new').first()
        if not new_status:
            return
        
        new_leads = Lead.objects.filter(
            status=new_status,
            assigned_sales__isnull=True
        )
        
        if not new_leads.exists():
            return
        
        now = timezone.now()
        weekday = now.weekday()
        
        # Faol sotuvchilarni topish
        available_sales = get_available_sales(weekday, now.time())
        
        if not available_sales:
            logger.warning("Faol sotuvchilar topilmadi")
            return
        
        # Har bir sotuvchi uchun bugungi lidlar sonini hisoblash
        sales_loads = {}
        for sales in available_sales:
            today_leads = Lead.objects.filter(
                assigned_sales=sales,
                assigned_at__date=now.date()
            ).count()
            
            profile = SalesProfile.objects.filter(user=sales).first()
            max_leads = profile.max_leads_per_day if profile else 10
            
            if today_leads < max_leads:
                sales_loads[sales] = today_leads
        
        # Lidlarni taqsimlash
        for lead in new_leads:
            if not sales_loads:
                break
            
            min_sales = min(sales_loads.items(), key=lambda x: x[1])[0]
            
            lead.assigned_sales = min_sales
            lead.assigned_at = now
            lead.save()
            
            sales_loads[min_sales] += 1
            
            profile = SalesProfile.objects.filter(user=min_sales).first()
            max_leads = profile.max_leads_per_day if profile else 10
            if sales_loads[min_sales] >= max_leads:
                del sales_loads[min_sales]
            
            LeadHistory.objects.create(
                lead=lead,
                new_status=new_status,
                notes=f"Avtomatik taqsimlandi: {min_sales.username}"
            )
            
            # 5 daqiqadan keyin follow-up yaratish
            create_initial_followup.delay(lead.id)
        
        logger.info(f"{new_leads.count()} ta lid taqsimlandi")
    
    except Exception as e:
        logger.error(f"Lid taqsimlash xatosi: {e}")


def get_available_sales(weekday, current_time):
    """
    Ish vaqtida bo'lgan sotuvchilarni topish
    """
    from .models import Leave, SalesProfile
    from accounts.models import User
    
    today = timezone.now().date()
    
    # Ruxsatda bo'lgan sotuvchilar
    on_leave = Leave.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
        status='approved'
    ).values_list('sales_id', flat=True)
    
    # Faol sotuvchilar
    available = []
    sales_users = User.objects.filter(
        role__in=['sales', 'sales_manager'],
        is_active=True
    ).exclude(id__in=on_leave)
    
    for user in sales_users:
        profile = SalesProfile.objects.filter(user=user).first()
        if profile:
            if profile.is_absent or not profile.is_active_sales:
                continue
            if profile.is_working_day(weekday):
                if profile.work_start_time <= current_time <= profile.work_end_time:
                    available.append(user)
        else:
            available.append(user)
    
    return available


@shared_task
def create_initial_followup(lead_id):
    """
    Yangi lid uchun dastlabki follow-up yaratish (5 daqiqadan keyin)
    """
    try:
        from .models import Lead, FollowUp
        
        lead = Lead.objects.get(pk=lead_id)
        
        if not lead.assigned_sales:
            return
        
        due_date = timezone.now() + timedelta(minutes=5)
        
        # Ish vaqti tekshiruvi
        due_date = FollowUp.calculate_work_hours_due_date(lead.assigned_sales, due_date)
        
        FollowUp.objects.create(
            lead=lead,
            sales=lead.assigned_sales,
            due_date=due_date,
            notes="Yangi lid bilan aloqa qilish",
            followup_sequence=1
        )
        
        logger.info(f"Initial follow-up yaratildi: lead {lead_id}")
    
    except Exception as e:
        logger.error(f"Initial follow-up yaratish xatosi: {e}")


@shared_task
def send_followup_reminders():
    """
    Follow-up eslatmalarini yuborish (Har 15 daqiqa)
    """
    try:
        from .models import FollowUp
        
        now = timezone.now()
        upcoming = FollowUp.objects.filter(
            completed=False,
            reminder_sent=False,
            due_date__lte=now + timedelta(minutes=15),
            due_date__gte=now
        )
        
        for followup in upcoming:
            # Telegram orqali yuborish
            try:
                from telegram_bot.tasks import send_followup_reminder
                send_followup_reminder.delay(followup.id)
            except ImportError:
                pass
            
            followup.reminder_sent = True
            followup.save()
        
        logger.info(f"{upcoming.count()} ta follow-up eslatmasi yuborildi")
    
    except Exception as e:
        logger.error(f"Follow-up eslatma xatosi: {e}")


@shared_task
def check_overdue_followups():
    """
    Overdue follow-up'larni tekshirish (Har 30 daqiqa)
    """
    try:
        from .models import FollowUp
        
        now = timezone.now()
        overdue = FollowUp.objects.filter(
            completed=False,
            due_date__lt=now
        )
        
        updated = overdue.update(is_overdue=True)
        
        # 24+ soat overdue bo'lganlarni manager'ga escalate qilish
        critical_overdue = FollowUp.objects.filter(
            completed=False,
            is_overdue=True,
            due_date__lt=now - timedelta(hours=24)
        )
        
        for followup in critical_overdue:
            try:
                from telegram_bot.tasks import send_overdue_escalation
                send_overdue_escalation.delay(followup.id)
            except ImportError:
                pass
        
        logger.info(f"{updated} ta overdue follow-up yangilandi")
    
    except Exception as e:
        logger.error(f"Overdue tekshirish xatosi: {e}")


@shared_task
def send_trial_reminders():
    """
    Sinov darsi eslatmalarini yuborish (Har soat yoki har 5 daqiqada)
    Ish vaqtini hisobga olgan holda: 8-10 soat va 2 soat oldin
    """
    try:
        from .models import TrialLesson, FollowUp
        from datetime import datetime, timedelta
        
        now = timezone.now()
        
        # Kelajakdagi sinov darslari (7 kun ichida)
        future_date = now.date() + timedelta(days=7)
        trials = TrialLesson.objects.filter(
            date__lte=future_date,
            date__gte=now.date(),
            result__isnull=True
        ).select_related('lead', 'lead__assigned_sales')
        
        for trial in trials:
            if not trial.lead.assigned_sales or not trial.time:
                continue
            
            # Sinov darsi vaqti
            trial_datetime = timezone.make_aware(
                datetime.combine(trial.date, trial.time)
            )
            
            # Eslatma vaqtlari (ish vaqti hisobga olingan holda)
            reminder_8_10_hours = trial_datetime - timedelta(hours=10)  # 10 soat oldin
            reminder_2_hours = trial_datetime - timedelta(hours=2)       # 2 soat oldin
            
            # Hozirgi vaqt
            current_time = now
            
            # 8-10 soat oldin eslatma (ish vaqti ichida bo'lishi kerak)
            if (reminder_8_10_hours <= current_time <= reminder_8_10_hours + timedelta(hours=2) and
                not trial.reminder_8_10_sent):
                
                # Ish vaqtida yuborilishi kerak
                due_date = FollowUp.calculate_work_hours_due_date(
                    trial.lead.assigned_sales,
                    current_time
                )
                
                # Agar eslatma vaqti ish vaqtida bo'lsa, yuborish
                sales_profile = trial.lead.assigned_sales.sales_profile if hasattr(trial.lead.assigned_sales, 'sales_profile') else None
                if sales_profile and sales_profile.is_working_now():
                    try:
                        from telegram_bot.tasks import send_trial_reminder
                        send_trial_reminder.delay(trial.id, reminder_type='8_10_hours')
                        trial.reminder_8_10_sent = True
                        trial.save(update_fields=['reminder_8_10_sent'])
                    except ImportError:
                        pass
            
            # 2 soat oldin eslatma (ish vaqtida)
            if (reminder_2_hours <= current_time <= reminder_2_hours + timedelta(minutes=15) and
                not trial.reminder_2_hours_sent):
                
                # Ish vaqtida yuborilishi kerak
                due_date = FollowUp.calculate_work_hours_due_date(
                    trial.lead.assigned_sales,
                    current_time
                )
                
                sales_profile = trial.lead.assigned_sales.sales_profile if hasattr(trial.lead.assigned_sales, 'sales_profile') else None
                if sales_profile and sales_profile.is_working_now():
                    try:
                        from telegram_bot.tasks import send_trial_reminder
                        send_trial_reminder.delay(trial.id, reminder_type='2_hours')
                        trial.reminder_2_hours_sent = True
                        trial.save(update_fields=['reminder_2_hours_sent'])
                    except ImportError:
                        pass
        
        logger.info(f"Sinov eslatmalari tekshirildi")
    
    except Exception as e:
        logger.error(f"Sinov eslatma xatosi: {e}")


@shared_task
def check_reactivation():
    """
    Yo'qotilgan lidlarni reaktivatsiya qilish (Kunlik)
    """
    try:
        from .models import Lead, LeadStatus, FollowUp, Reactivation
        
        lost_status = LeadStatus.objects.filter(code='lost').first()
        if not lost_status:
            return
        
        now = timezone.now()
        intervals = [7, 14, 30]
        
        for days in intervals:
            target_date = (now - timedelta(days=days)).date()
            
            # Bu kunda yo'qotilgan lidlar
            leads = Lead.objects.filter(
                status=lost_status,
                lost_at__date=target_date
            )
            
            reactivation_type = f'{days}_days'
            
            for lead in leads:
                # Allaqachon reaktivatsiya qilinganmi?
                existing = Reactivation.objects.filter(
                    lead=lead,
                    reactivation_type=reactivation_type
                ).exists()
                
                if existing:
                    continue
                
                # Reaktivatsiya yaratish
                Reactivation.objects.create(
                    lead=lead,
                    days_since_lost=days,
                    reactivation_type=reactivation_type
                )
                
                # Follow-up yaratish
                if lead.assigned_sales:
                    FollowUp.objects.create(
                        lead=lead,
                        sales=lead.assigned_sales,
                        due_date=now + timedelta(hours=1),
                        notes=f"Reaktivatsiya ({days} kun keyin)",
                        followup_sequence=99
                    )
        
        logger.info("Reaktivatsiya tekshirildi")
    
    except Exception as e:
        logger.error(f"Reaktivatsiya xatosi: {e}")


@shared_task
def calculate_daily_kpi():
    """
    Kunlik KPI hisoblash (Har kuni 23:55 da)
    """
    try:
        from .models import Lead, LeadStatus, FollowUp, DailyKPI
        from accounts.models import User
        
        today = timezone.now().date()
        
        sales_users = User.objects.filter(
            role__in=['sales', 'sales_manager'],
            is_active=True
        )
        
        for sales in sales_users:
            kpi, created = DailyKPI.objects.get_or_create(
                sales=sales,
                date=today
            )
            
            # Kunlik aloqalar
            kpi.daily_contacts = Lead.objects.filter(
                assigned_sales=sales,
                status__code='contacted',
                updated_at__date=today
            ).count()
            
            # Kunlik follow-uplar
            total_followups = FollowUp.objects.filter(
                sales=sales,
                due_date__date=today
            ).count()
            
            completed_followups = FollowUp.objects.filter(
                sales=sales,
                due_date__date=today,
                completed=True
            ).count()
            
            kpi.daily_followups = total_followups
            if total_followups > 0:
                kpi.followup_completion_rate = (completed_followups / total_followups) * 100
            
            # Sinovga yozilganlar
            kpi.trials_registered = Lead.objects.filter(
                assigned_sales=sales,
                status__code='trial_registered',
                updated_at__date=today
            ).count()
            
            # Sinovdan sotuv
            kpi.trials_to_sales = Lead.objects.filter(
                assigned_sales=sales,
                status__code='enrolled',
                enrolled_at__date=today
            ).count()
            
            # Konversiya
            if kpi.trials_registered > 0:
                kpi.conversion_rate = (kpi.trials_to_sales / kpi.trials_registered) * 100
            
            # Overdue
            kpi.overdue_count = FollowUp.objects.filter(
                sales=sales,
                is_overdue=True,
                completed=False
            ).count()
            
            kpi.save()
        
        logger.info(f"Kunlik KPI hisoblandi: {today}")
    
    except Exception as e:
        logger.error(f"Kunlik KPI xatosi: {e}")


@shared_task
def calculate_monthly_kpi(month=None, year=None):
    """
    Oylik KPI hisoblash
    """
    try:
        from .models import Lead, LeadStatus, FollowUp, SalesKPI
        from accounts.models import User
        
        if not month or not year:
            now = timezone.now()
            month = now.month
            year = now.year
        
        sales_users = User.objects.filter(
            role__in=['sales', 'sales_manager'],
            is_active=True
        )
        
        for sales in sales_users:
            kpi, created = SalesKPI.objects.get_or_create(
                sales=sales,
                month=month,
                year=year
            )
            
            # Total contacts
            kpi.total_contacts = Lead.objects.filter(
                assigned_sales=sales,
                assigned_at__year=year,
                assigned_at__month=month
            ).count()
            
            # Follow-up completion rate
            total_followups = FollowUp.objects.filter(
                sales=sales,
                due_date__year=year,
                due_date__month=month
            ).count()
            
            completed_followups = FollowUp.objects.filter(
                sales=sales,
                due_date__year=year,
                due_date__month=month,
                completed=True
            ).count()
            
            if total_followups > 0:
                kpi.followup_completion_rate = (completed_followups / total_followups) * 100
            
            # Conversion rate
            trial_leads = Lead.objects.filter(
                assigned_sales=sales,
                status__code__in=['trial_registered', 'trial_attended'],
                assigned_at__year=year,
                assigned_at__month=month
            ).count()
            
            enrolled_leads = Lead.objects.filter(
                assigned_sales=sales,
                status__code='enrolled',
                enrolled_at__year=year,
                enrolled_at__month=month
            ).count()
            
            if trial_leads > 0:
                kpi.conversion_rate = (enrolled_leads / trial_leads) * 100
            
            kpi.enrolled_leads = enrolled_leads
            
            # Overdue followups
            kpi.overdue_followups = FollowUp.objects.filter(
                sales=sales,
                due_date__year=year,
                due_date__month=month,
                is_overdue=True
            ).count()
            
            kpi.calculate_kpi()
        
        logger.info(f"Oylik KPI hisoblandi: {month}/{year}")
    
    except Exception as e:
        logger.error(f"Oylik KPI xatosi: {e}")


@shared_task
def send_daily_statistics():
    """
    Kunlik statistikani yuborish (Har kuni 09:00 da)
    """
    try:
        from .models import Lead, FollowUp
        from accounts.models import User
        
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Kecha statistikasi
        stats = {
            'new_leads': Lead.objects.filter(created_at__date=yesterday).count(),
            'enrolled': Lead.objects.filter(enrolled_at__date=yesterday).count(),
            'followups_completed': FollowUp.objects.filter(
                completed_at__date=yesterday
            ).count(),
            'overdue': FollowUp.objects.filter(
                is_overdue=True,
                completed=False
            ).count()
        }
        
        # Telegram guruhiga yuborish
        try:
            from telegram_bot.tasks import send_daily_stats
            send_daily_stats.delay(stats)
        except ImportError:
            pass
        
        logger.info(f"Kunlik statistika yuborildi: {yesterday}")
    
    except Exception as e:
        logger.error(f"Kunlik statistika xatosi: {e}")


@shared_task
def create_status_followup(lead_id, status_code):
    """
    Status o'zgarganda tegishli follow-up yaratish
    """
    try:
        from .models import Lead, FollowUp
        
        lead = Lead.objects.get(pk=lead_id)
        
        if not lead.assigned_sales:
            return
        
        # Follow-up vaqtlari (daqiqalar bo'yicha)
        followup_times = {
            'new': 5,  # 5 daqiqa
            'contacted': 24 * 60,  # 24 soat (birinchi, keyin sequential follow-up'lar)
            'interested': 24 * 60,  # 24 soat
            'trial_registered': 24 * 60,  # Sinov sanasidan 1 kun oldin (alohida logic)
            'trial_attended': 90,  # 90 daqiqa (sinov tugagandan keyin)
            'trial_not_attended': 24 * 60,  # 24 soat
            'offer_sent': 48 * 60,  # 48 soat
        }
        
        minutes = followup_times.get(status_code)
        if not minutes:
            return
        
        # Mavjud follow-up sonini olish
        sequence = FollowUp.objects.filter(lead=lead).count() + 1
        
        due_date = timezone.now() + timedelta(minutes=minutes)
        due_date = FollowUp.calculate_work_hours_due_date(lead.assigned_sales, due_date)
        
        FollowUp.objects.create(
            lead=lead,
            sales=lead.assigned_sales,
            due_date=due_date,
            notes=f"Status: {status_code}",
            followup_sequence=sequence
        )
        
        logger.info(f"Status follow-up yaratildi: lead {lead_id}, status {status_code}")
    
    except Exception as e:
        logger.error(f"Status follow-up xatosi: {e}")


@shared_task
def create_contacted_followups():
    """
    'Contacted' statusidagi lidlar uchun ketma-ket follow-up'lar yaratish
    Har 2 soatda tekshiriladi va kerakli follow-up'lar yaratiladi
    """
    try:
        from .models import Lead, LeadStatus, FollowUp
        
        contacted_status = LeadStatus.objects.filter(code='contacted').first()
        if not contacted_status:
            return
        
        # 'Contacted' statusidagi lidlar
        contacted_leads = Lead.objects.filter(
            status=contacted_status,
            assigned_sales__isnull=False
        ).select_related('assigned_sales')
        
        for lead in contacted_leads:
            # Oxirgi bajarilgan follow-up'ni topish
            last_completed = FollowUp.objects.filter(
                lead=lead,
                completed=True
            ).order_by('-completed_at').first()
            
            if not last_completed:
                continue
            
            # Ketma-ketlik raqami
            sequence = last_completed.followup_sequence if last_completed.followup_sequence else 1
            
            # Maksimum 4 ta follow-up (24s, 3k, 7k, 14k)
            if sequence >= 4:
                continue
            
            # Keyingi follow-up mavjudmi?
            next_sequence = sequence + 1
            existing = FollowUp.objects.filter(
                lead=lead,
                followup_sequence=next_sequence,
                completed=False
            ).exists()
            
            if existing:
                continue
            
            # Vaqt intervallari
            intervals = {
                1: 24,      # 24 soat
                2: 72,      # 3 kun (72 soat)
                3: 168,     # 7 kun (168 soat)
                4: 336      # 14 kun (336 soat)
            }
            
            hours = intervals.get(next_sequence)
            if not hours:
                continue
            
            # Oxirgi follow-up bajarilgan vaqtdan boshlab hisoblash
            due_date = last_completed.completed_at + timedelta(hours=hours)
            due_date = FollowUp.calculate_work_hours_due_date(lead.assigned_sales, due_date)
            
            # Follow-up yaratish
            days_text = {1: '24 soat', 2: '3 kun', 3: '7 kun', 4: '14 kun'}
            FollowUp.objects.create(
                lead=lead,
                sales=lead.assigned_sales,
                due_date=due_date,
                notes=f"Follow-up #{next_sequence} ({days_text.get(next_sequence, '24 soat')} keyin)",
                followup_sequence=next_sequence
            )
        
        logger.info("Contacted follow-up'lar tekshirildi")
    
    except Exception as e:
        logger.error(f"Contacted follow-up yaratish xatosi: {e}")


@shared_task
def check_leave_expiry():
    """
    Ruxsatlar tugashini tekshirish
    """
    try:
        from .models import Leave, SalesProfile
        
        today = timezone.now().date()
        
        # Tugagan ruxsatlar
        expired_leaves = Leave.objects.filter(
            end_date__lt=today,
            status='approved'
        )
        
        for leave in expired_leaves:
            # SalesProfile yangilash
            if hasattr(leave.sales, 'sales_profile'):
                profile = leave.sales.sales_profile
                profile.is_on_leave = False
                profile.save()
        
        logger.info(f"{expired_leaves.count()} ta ruxsat tugadi")
    
    except Exception as e:
        logger.error(f"Ruxsat tekshirish xatosi: {e}")
