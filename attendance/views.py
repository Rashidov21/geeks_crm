from django.views.generic import ListView, CreateView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
from .models import Attendance, AttendanceStatistics
from courses.models import Lesson, Group
from accounts.mixins import MentorRequiredMixin, TailwindFormMixin


class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendances'
    
    def get_queryset(self):
        queryset = Attendance.objects.select_related('student', 'lesson', 'lesson__group')
        if self.request.user.is_student:
            queryset = queryset.filter(student=self.request.user)
        elif self.request.user.is_mentor:
            queryset = queryset.filter(lesson__group__mentor=self.request.user)
        return queryset.order_by('-lesson__date', '-lesson__start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Stats for cards
        attendances = self.get_queryset()
        context['present_count'] = attendances.filter(status='present').count()
        context['late_count'] = attendances.filter(status='late').count()
        context['absent_count'] = attendances.filter(status='absent').count()
        total = attendances.count()
        if total > 0:
            context['attendance_percentage'] = ((context['present_count'] + context['late_count']) / total) * 100
        else:
            context['attendance_percentage'] = 0
        
        # Mentor uchun guruhlar ro'yxati
        if self.request.user.is_mentor:
            context['groups'] = Group.objects.filter(mentor=self.request.user, is_active=True)
        elif self.request.user.is_admin or self.request.user.is_manager:
            context['groups'] = Group.objects.filter(is_active=True)
        
        # Permissions
        user = self.request.user
        context['can_create'] = user.is_admin or user.is_manager or user.is_mentor
        context['can_edit'] = user.is_admin or user.is_manager or user.is_mentor
        context['can_delete'] = user.is_admin or user.is_manager
        
        return context


class GroupAttendanceView(LoginRequiredMixin, TemplateView):
    """Guruh bo'yicha interaktiv davomat sahifasi"""
    template_name = 'attendance/group_attendance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(Group, pk=group_id)
        
        # Faqat mentor yoki admin/manager ko'ra oladi
        if not (self.request.user.is_admin or self.request.user.is_manager or 
                (self.request.user.is_mentor and group.mentor == self.request.user)):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
        
        context['group'] = group
        
        # Yil va oy parametrlari
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        context['year'] = year
        context['month'] = month
        context['month_name'] = calendar.month_name[month]
        
        # Oyning kunlari
        _, num_days = calendar.monthrange(year, month)
        
        # Guruh darslari (shu oy uchun)
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, num_days).date()
        
        lessons = Lesson.objects.filter(
            group=group,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        lesson_dates = list(lessons.values_list('date', flat=True).distinct())
        context['lesson_dates'] = lesson_dates
        
        # Talabalar va ularning davomati
        students = group.students.all().order_by('first_name', 'last_name')
        
        student_data = []
        for student in students:
            # Har bir talaba uchun davomat ma'lumotlari
            attendances = Attendance.objects.filter(
                student=student,
                lesson__group=group,
                lesson__date__gte=start_date,
                lesson__date__lte=end_date
            ).select_related('lesson')
            
            # Davomat dictionary (date -> status)
            att_dict = {att.lesson.date: att.status for att in attendances}
            
            # Statistika
            present = sum(1 for s in att_dict.values() if s == 'present')
            late = sum(1 for s in att_dict.values() if s == 'late')
            absent = sum(1 for s in att_dict.values() if s == 'absent')
            total = len(lesson_dates)
            percentage = ((present + late) / total * 100) if total > 0 else 0
            
            # Qarz holati (masalan, to'lov qilmagan)
            has_debt = False  # Bu yerda finance modeli bilan bog'lash mumkin
            
            student_data.append({
                'student': student,
                'attendances': att_dict,
                'present': present,
                'late': late,
                'absent': absent,
                'total': total,
                'percentage': percentage,
                'has_debt': has_debt,
            })
        
        context['student_data'] = student_data
        context['total_lessons'] = len(lesson_dates)
        
        # Navigatsiya uchun
        if month == 1:
            context['prev_month'] = 12
            context['prev_year'] = year - 1
        else:
            context['prev_month'] = month - 1
            context['prev_year'] = year
        
        if month == 12:
            context['next_month'] = 1
            context['next_year'] = year + 1
        else:
            context['next_month'] = month + 1
            context['next_year'] = year
        
        return context


class AttendanceToggleView(LoginRequiredMixin, View):
    """AJAX orqali davomat belgilash"""
    
    def post(self, request):
        import json
        data = json.loads(request.body)
        
        student_id = data.get('student_id')
        date_str = data.get('date')
        group_id = data.get('group_id')
        status = data.get('status', 'present')
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            group = get_object_or_404(Group, pk=group_id)
            
            # Ruxsat tekshirish
            if not (request.user.is_admin or request.user.is_manager or 
                    (request.user.is_mentor and group.mentor == request.user)):
                return JsonResponse({'success': False, 'error': 'Ruxsat yo\'q'}, status=403)
            
            # Darsni topish yoki yaratish
            lesson, created = Lesson.objects.get_or_create(
                group=group,
                date=date,
                defaults={
                    'start_time': group.start_time,
                    'end_time': group.end_time,
                    'title': f'{group.name} - {date}'
                }
            )
            
            from accounts.models import User
            student = get_object_or_404(User, pk=student_id)
            
            # Davomat yaratish yoki yangilash
            attendance, created = Attendance.objects.update_or_create(
                lesson=lesson,
                student=student,
                defaults={'status': status}
            )
            
            return JsonResponse({
                'success': True,
                'status': attendance.status,
                'created': created
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


class AttendanceCreateView(TailwindFormMixin, MentorRequiredMixin, CreateView):
    model = Attendance
    template_name = 'attendance/attendance_form.html'
    fields = ['lesson', 'student', 'status', 'notes']
    
    def get_success_url(self):
        from django.urls import reverse
        return reverse('attendance:attendance_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter lessons by mentor if specific lesson_id not provided
        if 'lesson_id' in self.kwargs:
            form.fields['lesson'].initial = self.kwargs['lesson_id']
            form.fields['lesson'].widget = form.fields['lesson'].hidden_widget()
        else:
            # Show only mentor's lessons
            form.fields['lesson'].queryset = Lesson.objects.filter(
                group__mentor=self.request.user
            ).order_by('-date')
        return form
    
    def form_valid(self, form):
        if 'lesson_id' in self.kwargs:
            form.instance.lesson = Lesson.objects.get(pk=self.kwargs['lesson_id'])
        return super().form_valid(form)


class AttendanceStatisticsView(LoginRequiredMixin, ListView):
    model = AttendanceStatistics
    template_name = 'attendance/statistics.html'
    context_object_name = 'statistics'
    
    def get_queryset(self):
        queryset = AttendanceStatistics.objects.select_related('student', 'group')
        if self.request.user.is_student:
            queryset = queryset.filter(student=self.request.user)
        return queryset.order_by('-attendance_percentage')
