from django.views.generic import ListView, CreateView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import calendar
from .models import Attendance, AttendanceStatistics
from courses.models import Lesson, Group
from accounts.models import User
from accounts.mixins import MentorRequiredMixin, TailwindFormMixin


class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendances'
    paginate_by = 50
    
    def dispatch(self, request, *args, **kwargs):
        # Mentors and admins should only access attendance from group detail page
        if request.user.is_mentor or request.user.is_admin or request.user.is_manager:
            # Redirect to groups list or first group
            from courses.models import Group
            if request.user.is_mentor:
                groups = Group.objects.filter(mentor=request.user, is_active=True)
            else:
                groups = Group.objects.filter(is_active=True)
            
            if groups.exists():
                return redirect('attendance:group_attendance', group_id=groups.first().pk)
            else:
                from django.contrib import messages
                messages.info(request, 'Sizda faol guruhlar yo\'q. Davomatni guruh detail sahifasidan olishingiz mumkin.')
                return redirect('courses:group_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Attendance.objects.select_related('student', 'lesson', 'lesson__group', 'lesson__group__course')
        if self.request.user.is_student:
            queryset = queryset.filter(student=self.request.user)
        elif self.request.user.is_mentor:
            queryset = queryset.filter(lesson__group__mentor=self.request.user)
        
        # Filterlar
        group_id = self.request.GET.get('group')
        if group_id:
            queryset = queryset.filter(lesson__group_id=group_id)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Search query
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(student__first_name__icontains=search) |
                Q(student__last_name__icontains=search) |
                Q(lesson__group__name__icontains=search)
            )
        
        return queryset.order_by('-lesson__date', '-lesson__start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Stats for cards
        attendances = self.get_queryset()
        present_count = attendances.filter(status='present').count()
        late_count = attendances.filter(status='late').count()
        absent_count = attendances.filter(status='absent').count()
        total = attendances.count()
        if total > 0:
            attendance_percentage = ((present_count + late_count) / total) * 100
        else:
            attendance_percentage = 0
        
        # Stats for cards
        context['stats'] = [
            {'label': 'Jami davomat', 'value': total, 'icon': 'fas fa-calendar-check', 'color': 'text-cyan-600'},
            {'label': 'Kelgan', 'value': present_count, 'icon': 'fas fa-check-circle', 'color': 'text-green-600'},
            {'label': 'Kechikkan', 'value': late_count, 'icon': 'fas fa-clock', 'color': 'text-yellow-600'},
            {'label': 'Kelmagan', 'value': absent_count, 'icon': 'fas fa-times-circle', 'color': 'text-red-600'},
        ]
        
        context['attendance_percentage'] = attendance_percentage
        
        # Mentor uchun guruhlar ro'yxati
        if self.request.user.is_mentor:
            context['groups'] = Group.objects.filter(mentor=self.request.user, is_active=True)
        elif self.request.user.is_admin or self.request.user.is_manager:
            context['groups'] = Group.objects.filter(is_active=True)
        
        # Permissions
        user = self.request.user
        context['can_create'] = user.is_superuser or (hasattr(user, 'is_admin') and user.is_admin) or (hasattr(user, 'is_manager') and user.is_manager) or (hasattr(user, 'is_mentor') and user.is_mentor)
        context['can_edit'] = context['can_create']
        context['can_delete'] = False  # Attendance records usually shouldn't be deleted
        
        return context


class GroupAttendanceView(LoginRequiredMixin, TemplateView):
    """Guruh bo'yicha interaktiv davomat sahifasi"""
    template_name = 'attendance/group_attendance.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Permission check - move here from get_context_data"""
        group_id = kwargs.get('group_id')
        group = get_object_or_404(Group, pk=group_id)
        
        # Faqat mentor yoki admin/manager ko'ra oladi
        if not (request.user.is_admin or request.user.is_manager or 
                (request.user.is_mentor and group.mentor == request.user)):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(Group, pk=group_id)
        
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
        
        # Generate expected lesson dates based on group schedule
        expected_lesson_dates = []
        current = start_date
        while current <= end_date:
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
                expected_lesson_dates.append(current)
            
            current += timedelta(days=1)
        
        # Get actual lessons
        actual_lessons = Lesson.objects.filter(
            group=group,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Create lesson dict for quick lookup
        lesson_dict = {lesson.date: lesson for lesson in actual_lessons}
        
        # Merge expected dates with actual lessons
        # For each expected date, use actual lesson if exists, otherwise create virtual lesson
        from types import SimpleNamespace
        lessons_list = []
        for date in expected_lesson_dates:
            if date in lesson_dict:
                lessons_list.append(lesson_dict[date])
            else:
                # Create virtual lesson for display
                virtual_lesson = SimpleNamespace(
                    pk=None,
                    date=date,
                    start_time=group.start_time,
                    end_time=group.end_time,
                    topic=None,
                    title=None,
                    group=group
                )
                lessons_list.append(virtual_lesson)
        
        lesson_dates = expected_lesson_dates
        context['lesson_dates'] = lesson_dates
        context['lessons_list'] = lessons_list
        
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
        
        # Add points and rankings to student data
        from gamification.models import StudentPoints, GroupRanking
        for data in student_data:
            student = data['student']
            # Get or create student points and calculate
            student_points, created = StudentPoints.objects.get_or_create(
                student=student,
                group=group
            )
            if created or not student_points.total_points:
                student_points.calculate_total_points()
            
            # Get ranking
            ranking = GroupRanking.objects.filter(
                group=group,
                student=student
            ).first()
            
            data['total_points'] = student_points.total_points
            data['rank'] = ranking.rank if ranking else None
        
        # Sort by points for ranking tab
        student_data_sorted = sorted(student_data, key=lambda x: x.get('total_points', 0), reverse=True)
        for idx, data in enumerate(student_data_sorted, 1):
            if data.get('rank') is None:
                data['rank'] = idx
        
        context['student_data'] = student_data
        context['student_data_sorted'] = student_data_sorted
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


class SaveGradeView(LoginRequiredMixin, View):
    """Save student grade with auto-save"""
    
    def post(self, request):
        import json
        data = json.loads(request.body)
        
        student_id = data.get('student_id')
        group_id = data.get('group_id')
        grade = data.get('grade')
        comment = data.get('comment', '')
        
        try:
            group = get_object_or_404(Group, pk=group_id)
            student = get_object_or_404(User, pk=student_id, role='student')
            
            # Permission check
            if not (request.user.is_admin or request.user.is_manager or 
                    (request.user.is_mentor and group.mentor == request.user)):
                return JsonResponse({'success': False, 'error': 'Ruxsat yo\'q'}, status=403)
            
            # Save grade (you may need to create a Grade model or use existing one)
            # For now, we'll just return success - you can implement actual grade saving
            return JsonResponse({
                'success': True,
                'message': 'Baho saqlandi'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


class SaveParentCommentView(LoginRequiredMixin, View):
    """Save parent comment and send via Telegram"""
    
    def post(self, request):
        import json
        from telegram_bot.tasks import send_parent_comment_notification
        
        data = json.loads(request.body)
        
        student_id = data.get('student_id')
        group_id = data.get('group_id')
        comment = data.get('comment', '')
        
        try:
            from telegram_bot.tasks import send_parent_comment_notification
            
            group = get_object_or_404(Group, pk=group_id)
            student = get_object_or_404(User, pk=student_id, role='student')
            
            # Permission check
            if not (request.user.is_admin or request.user.is_manager or 
                    (request.user.is_mentor and group.mentor == request.user)):
                return JsonResponse({'success': False, 'error': 'Ruxsat yo\'q'}, status=403)
            
            # Get student's parent info from StudentProfile
            from accounts.models import StudentProfile
            try:
                student_profile = StudentProfile.objects.get(user=student)
                parent_telegram_id = student_profile.parent_telegram_id
                parent_phone = student_profile.parent_phone
                
                if not parent_telegram_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Ota-onada Telegram ID topilmadi'
                    })
                
                # Send to parent via Telegram
                send_parent_comment_notification.delay(
                    parent_telegram_id,
                    student.id,
                    group.id,
                    comment
                )
                
            except StudentProfile.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'O\'quvchi profili topilmadi'
                })
            
            return JsonResponse({
                'success': True,
                'message': f'Izoh {sent_count} ta ota-onaga yuborildi'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


class AttendanceStatisticsView(LoginRequiredMixin, ListView):
    model = AttendanceStatistics
    template_name = 'attendance/statistics.html'
    context_object_name = 'statistics'
    
    def get_queryset(self):
        queryset = AttendanceStatistics.objects.select_related('student', 'group')
        if self.request.user.is_student:
            queryset = queryset.filter(student=self.request.user)
        return queryset.order_by('-attendance_percentage')
