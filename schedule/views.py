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
            lessons = lessons.filter(group__mentor=self.request.user)
        
        # Kunlar bo'yicha guruhlash
        lessons_by_day = {}
        for day in days:
            lessons_by_day[day['date']] = []
        for lesson in lessons:
            if lesson.date in lessons_by_day:
                lessons_by_day[lesson.date].append(lesson)
        
        # Template uchun list formatida ham beramiz
        context['lessons_by_day'] = lessons_by_day
        # Har bir kun uchun alohida list
        for day in days:
            day['lessons'] = lessons_by_day.get(day['date'], [])
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
        
        # Get groups for the user
        from courses.models import Group
        if self.request.user.is_student:
            groups = Group.objects.filter(students=self.request.user, is_active=True)
        elif self.request.user.is_mentor:
            groups = Group.objects.filter(mentor=self.request.user, is_active=True)
        else:
            groups = Group.objects.filter(is_active=True)
        
        # Generate lessons based on group schedule
        lessons_by_date = {}
        
        for group in groups:
            current = first_day
            while current <= last_day:
                # Check if this day matches the group's schedule
                should_have_lesson = False
                
                if group.schedule_type == 'daily':
                    should_have_lesson = True
                elif group.schedule_type == 'odd':
                    # Toq kunlar (1, 3, 5, 7, 9, 11, 13, ...)
                    should_have_lesson = current.day % 2 == 1
                elif group.schedule_type == 'even':
                    # Juft kunlar (2, 4, 6, 8, 10, 12, 14, ...)
                    should_have_lesson = current.day % 2 == 0
                
                if should_have_lesson:
                    # Check if lesson already exists
                    existing_lesson = Lesson.objects.filter(
                        group=group,
                        date=current
                    ).first()
                    
                    if existing_lesson:
                        lesson = existing_lesson
                    else:
                        # Create a virtual lesson object for display
                        from types import SimpleNamespace
                        lesson = SimpleNamespace(
                            group=group,
                            date=current,
                            start_time=group.start_time,
                            end_time=group.end_time,
                            topic=None,
                            title=f'{group.name} - {current}',
                            pk=None
                        )
                    
                    if current not in lessons_by_date:
                        lessons_by_date[current] = []
                    lessons_by_date[current].append(lesson)
                
                current += timedelta(days=1)
        
        # Template uchun har bir kun uchun alohida list
        for week in weeks:
            for day in week:
                day['lessons'] = lessons_by_date.get(day['date'], [])
        
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
            room_schedule[room.id] = {}
            for time_slot in time_slots:
                room_schedule[room.id][time_slot] = None
        
        for lesson in lessons:
            if lesson.group and lesson.group.room and lesson.start_time:
                room_id = lesson.group.room.id
                start_hour = lesson.start_time.hour
                time_key = f'{start_hour:02d}:00'
                if room_id in room_schedule and time_key in room_schedule[room_id]:
                    room_schedule[room_id][time_key] = lesson
        
        context['room_schedule'] = room_schedule
        context['rooms'] = rooms
        context['lessons'] = lessons
        
        return context

