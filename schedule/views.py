from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta, datetime
from courses.models import Lesson, Group, Room
from accounts.mixins import RoleRequiredMixin


class TimetableView(LoginRequiredMixin, TemplateView):
    """Haftalik jadval ko'rinishi"""
    template_name = 'schedule/timetable.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Haftaning boshlanishi (dushanba)
        today = timezone.now().date()
        week_offset = int(self.request.GET.get('week', 0))
        start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        end_of_week = start_of_week + timedelta(days=6)
        
        # Hafta kunlari
        days = []
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            days.append({
                'date': day,
                'name': ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba'][i],
                'is_today': day == today
            })
        context['days'] = days
        context['week_offset'] = week_offset
        context['start_of_week'] = start_of_week
        context['end_of_week'] = end_of_week
        
        # Darslar
        lessons = Lesson.objects.filter(
            date__gte=start_of_week,
            date__lte=end_of_week
        ).select_related('group', 'group__room', 'group__mentor', 'topic')
        
        # Foydalanuvchi roliga qarab filtrlash
        if self.request.user.is_student:
            lessons = lessons.filter(group__students=self.request.user)
        elif self.request.user.is_mentor:
            lessons = lessons.filter(mentor=self.request.user)
        
        # Kunlar bo'yicha guruhlash
        lessons_by_day = {day['date']: [] for day in days}
        for lesson in lessons:
            if lesson.date in lessons_by_day:
                lessons_by_day[lesson.date].append(lesson)
        
        context['lessons_by_day'] = lessons_by_day
        context['rooms'] = Room.objects.filter(is_active=True)
        
        return context


class CalendarView(LoginRequiredMixin, TemplateView):
    """Oylik kalendar ko'rinishi"""
    template_name = 'schedule/calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Oy va yil
        today = timezone.now().date()
        month_offset = int(self.request.GET.get('month', 0))
        
        # Hozirgi oy
        target_date = today.replace(day=1)
        if month_offset != 0:
            month = target_date.month + month_offset
            year = target_date.year
            while month > 12:
                month -= 12
                year += 1
            while month < 1:
                month += 12
                year -= 1
            target_date = target_date.replace(year=year, month=month)
        
        # Oyning birinchi va oxirgi kuni
        first_day = target_date.replace(day=1)
        if target_date.month == 12:
            last_day = target_date.replace(year=target_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = target_date.replace(month=target_date.month + 1, day=1) - timedelta(days=1)
        
        # Kalendar uchun kunlar
        calendar_days = []
        
        # Oldingi oy kunlari
        start_weekday = first_day.weekday()
        for i in range(start_weekday):
            day = first_day - timedelta(days=start_weekday - i)
            calendar_days.append({'date': day, 'is_current_month': False, 'is_today': day == today})
        
        # Joriy oy kunlari
        current = first_day
        while current <= last_day:
            calendar_days.append({'date': current, 'is_current_month': True, 'is_today': current == today})
            current += timedelta(days=1)
        
        # Keyingi oy kunlari
        remaining = 42 - len(calendar_days)  # 6 hafta * 7 kun
        for i in range(remaining):
            day = last_day + timedelta(days=i + 1)
            calendar_days.append({'date': day, 'is_current_month': False, 'is_today': day == today})
        
        # Haftalarga bo'lish
        weeks = [calendar_days[i:i+7] for i in range(0, len(calendar_days), 7)]
        context['weeks'] = weeks
        context['month_offset'] = month_offset
        context['current_month'] = target_date
        context['month_names'] = ['Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun', 
                                   'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr']
        
        # Darslar
        lessons = Lesson.objects.filter(
            date__gte=first_day - timedelta(days=7),
            date__lte=last_day + timedelta(days=7)
        ).select_related('group')
        
        if self.request.user.is_student:
            lessons = lessons.filter(group__students=self.request.user)
        elif self.request.user.is_mentor:
            lessons = lessons.filter(mentor=self.request.user)
        
        # Kunlar bo'yicha guruhlash
        lessons_by_date = {}
        for lesson in lessons:
            if lesson.date not in lessons_by_date:
                lessons_by_date[lesson.date] = []
            lessons_by_date[lesson.date].append(lesson)
        
        context['lessons_by_date'] = lessons_by_date
        
        return context


class RoomScheduleView(LoginRequiredMixin, TemplateView):
    """Xonalar bo'yicha jadval"""
    template_name = 'schedule/rooms.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.now().date()
        selected_date = self.request.GET.get('date')
        if selected_date:
            try:
                selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            except:
                selected_date = today
        else:
            selected_date = today
        
        context['selected_date'] = selected_date
        
        # Xonalar
        rooms = Room.objects.filter(is_active=True)
        
        # Darslar
        lessons = Lesson.objects.filter(date=selected_date).select_related('group', 'group__room', 'group__mentor')
        
        # Vaqt slotlari (8:00 - 21:00)
        time_slots = []
        for hour in range(8, 22):
            time_slots.append(f'{hour:02d}:00')
        
        context['time_slots'] = time_slots
        
        # Xona va vaqt bo'yicha darslar
        room_schedule = {}
        for room in rooms:
            room_schedule[room.id] = {
                'room': room,
                'lessons': {}
            }
        
        for lesson in lessons:
            if lesson.group and lesson.group.room:
                room_id = lesson.group.room.id
                if room_id in room_schedule:
                    start_hour = lesson.start_time.hour if lesson.start_time else 9
                    time_key = f'{start_hour:02d}:00'
                    room_schedule[room_id]['lessons'][time_key] = lesson
        
        context['room_schedule'] = room_schedule
        context['rooms'] = rooms
        
        return context

