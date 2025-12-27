from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, UpdateView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Sum
from django.core.exceptions import PermissionDenied
from .models import User
from .decorators import role_required


class ProfileView(DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'
    
    def get_object(self):
        from django.http import Http404
        from django.core.exceptions import PermissionDenied
        
        pk = self.kwargs.get('pk')
        if pk:
            # Boshqa user profilini ko'rish
            try:
                target_user = User.objects.get(pk=pk)
            except User.DoesNotExist:
                raise Http404("User topilmadi")
            
            # O'z profilini ko'rish
            if target_user == self.request.user:
                return target_user
            
            # Admin, Manager, Mentor - barcha profillarni ko'ra oladi
            if (self.request.user.is_superuser or 
                (hasattr(self.request.user, 'is_admin') and self.request.user.is_admin) or 
                (hasattr(self.request.user, 'is_manager') and self.request.user.is_manager) or
                (hasattr(self.request.user, 'is_mentor') and self.request.user.is_mentor)):
                return target_user
            
            # Studentlar - faqat boshqa studentlarni ko'ra oladi
            if (hasattr(self.request.user, 'is_student') and self.request.user.is_student):
                if (hasattr(target_user, 'is_student') and target_user.is_student):
                    return target_user
                else:
                    raise PermissionDenied("Siz faqat boshqa studentlar profilini ko'ra olasiz")
            
            # Boshqa holatlar - ruxsat yo'q
            raise PermissionDenied("Siz bu profilni ko'rishga ruxsatingiz yo'q")
        else:
            # O'z profilini ko'rish
            return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = self.object
        context['current_user'] = self.request.user  # For template comparison
        
        # Mentorlar uchun statistika
        if user_profile.is_mentor:
            from courses.models import Group
            from finance.models import Debt, Contract
            from attendance.models import Attendance
            from django.utils import timezone
            from datetime import timedelta
            
            # Guruhlar
            groups = Group.objects.filter(mentor=user_profile, is_active=True)
            context['mentor_groups_count'] = groups.count()
            
            # O'quvchilar
            total_students = sum(g.students.filter(role='student', is_active=True).count() for g in groups)
            context['mentor_students_count'] = total_students
            
            # Qarzdor o'quvchilar
            student_ids = []
            for g in groups:
                student_ids.extend(g.students.filter(role='student', is_active=True).values_list('id', flat=True))
            
            if student_ids:
                contracts = Contract.objects.filter(student_id__in=student_ids, status='active')
                contract_ids = contracts.values_list('id', flat=True)
                debts = Debt.objects.filter(contract_id__in=contract_ids, is_paid=False)
                context['mentor_debtors_count'] = debts.values('contract__student').distinct().count()
            else:
                context['mentor_debtors_count'] = 0
            
            # Faol o'quvchilar (oxirgi 30 kunda davomat bo'lganlar)
            date_threshold = timezone.now().date() - timedelta(days=30)
            if student_ids:
                active_attendances = Attendance.objects.filter(
                    student_id__in=student_ids,
                    lesson__date__gte=date_threshold,
                    status='present'
                ).values('student').distinct()
                context['mentor_active_students_count'] = active_attendances.count()
            else:
                context['mentor_active_students_count'] = 0
        
        # Studentlar uchun statistika (viewing any student profile)
        if user_profile.role == 'student':
            from courses.models import Group
            from attendance.models import Attendance
            from homework.models import Homework
            from exams.models import Exam, ExamResult
            from gamification.models import StudentPoints
            from django.utils import timezone
            from datetime import timedelta
            
            # Guruhlar
            groups = Group.objects.filter(students=user_profile, is_active=True)
            context['student_groups'] = groups
            
            # Davomat
            this_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            attendances = Attendance.objects.filter(
                student=user_profile,
                lesson__date__gte=this_month_start.date()
            )
            total_att = attendances.count()
            present_att = attendances.filter(status__in=['present', 'late']).count()
            context['student_attendance_percentage'] = (present_att / total_att * 100) if total_att > 0 else 0
            
            # Uy vazifalari
            completed_homeworks = Homework.objects.filter(student=user_profile, is_submitted=True).count()
            total_homeworks = Homework.objects.filter(student=user_profile).count()
            context['student_homework_completion'] = (completed_homeworks / total_homeworks * 100) if total_homeworks > 0 else 0
            
            # Imtihonlar
            exam_results = ExamResult.objects.filter(student=user_profile)
            passed_exams = exam_results.filter(score__gte=60).count()
            total_exams = exam_results.count()
            context['student_exam_pass_rate'] = (passed_exams / total_exams * 100) if total_exams > 0 else 0
            
            # Progress
            from courses.models import StudentProgress
            progress_list = StudentProgress.objects.filter(student=user_profile)
            avg_progress = progress_list.aggregate(avg=Sum('progress_percentage'))['avg'] or 0
            context['student_progress_percentage'] = avg_progress / progress_list.count() if progress_list.count() > 0 else 0
            
            # Points
            student_points_list = StudentPoints.objects.filter(student=user_profile)
            context['student_total_points'] = sum(sp.total_points for sp in student_points_list)
        
        # Sales userlar uchun statistika
        if user_profile.is_sales or user_profile.is_sales_manager:
            from crm.models import Lead, FollowUp, TrialLesson, SalesKPI
            from django.utils import timezone
            from django.db.models import Count, Q
            
            # Jami lidlar
            total_leads = Lead.objects.filter(assigned_sales=user_profile).count()
            context['sales_total_leads'] = total_leads
            
            # Yozilgan lidlar (sales)
            enrolled_leads = Lead.objects.filter(assigned_sales=user_profile, status__code='enrolled').count()
            context['sales_enrolled_leads'] = enrolled_leads
            
            # Konversiya foizi
            conversion_rate = (enrolled_leads / total_leads * 100) if total_leads > 0 else 0
            context['sales_conversion_rate'] = conversion_rate
            
            # Sinov darslari soni
            trial_lessons_count = TrialLesson.objects.filter(lead__assigned_sales=user_profile).count()
            context['sales_trial_lessons'] = trial_lessons_count
            
            # Yo'qotilgan lidlar
            lost_leads = Lead.objects.filter(assigned_sales=user_profile, status__code='lost').count()
            context['sales_lost_leads'] = lost_leads
            
            # Kechikkan follow-uplar
            overdue_followups = FollowUp.objects.filter(
                sales=user_profile,
                completed=False,
                due_date__lt=timezone.now()
            ).count()
            context['sales_overdue_followups'] = overdue_followups
            
            # Bugungi follow-uplar
            today = timezone.now().date()
            today_followups = FollowUp.objects.filter(
                sales=user_profile,
                completed=False,
                due_date__date=today
            ).count()
            context['sales_today_followups'] = today_followups
            
            # Joriy oy uchun KPI
            current_month = timezone.now().month
            current_year = timezone.now().year
            try:
                current_kpi = SalesKPI.objects.get(
                    sales=user_profile,
                    month=current_month,
                    year=current_year
                )
                context['sales_current_kpi'] = current_kpi.total_kpi_score
            except SalesKPI.DoesNotExist:
                context['sales_current_kpi'] = 0
            
            # Lidlar ro'yxati (oxirgi 10 tasi)
            recent_leads = Lead.objects.filter(
                assigned_sales=user_profile
            ).select_related('status', 'interested_course').order_by('-created_at')[:10]
            context['sales_recent_leads'] = recent_leads
            context['sales_leads_count'] = total_leads
        
        return context


class ProfileEditView(UpdateView):
    model = User
    template_name = 'accounts/profile_edit.html'
    fields = ['first_name', 'last_name', 'email', 'phone']
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profil muvaffaqiyatli yangilandi.')
        return super().form_valid(form)


class AdminChangePasswordView(LoginRequiredMixin, View):
    """
    Admin boshqa user parolini o'zgartirish
    Faqat admin va manager uchun
    """
    def dispatch(self, request, *args, **kwargs):
        # Faqat admin va manager
        if not (request.user.is_admin or request.user.is_manager or request.user.is_superuser):
            raise PermissionDenied("Sizga bu funksiya uchun ruxsat yo'q")
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, pk):
        target_user = get_object_or_404(User, pk=pk)
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not new_password or not confirm_password:
            messages.error(request, 'Parol maydonlari to\'ldirilishi kerak.')
            return redirect('accounts:profile_detail', pk=pk)
        
        if new_password != confirm_password:
            messages.error(request, 'Parollar mos kelmaydi.')
            return redirect('accounts:profile_detail', pk=pk)
        
        if len(new_password) < 8:
            messages.error(request, 'Parol kamida 8 belgidan iborat bo\'lishi kerak.')
            return redirect('accounts:profile_detail', pk=pk)
        
        target_user.set_password(new_password)
        target_user.save()
        
        messages.success(request, f'{target_user.get_full_name() or target_user.username} paroli muvaffaqiyatli o\'zgartirildi.')
        return redirect('accounts:profile_detail', pk=pk)


class StudentGuideView(LoginRequiredMixin, TemplateView):
    """
    Studentlar uchun platforma qo'llanmasi
    """
    template_name = 'accounts/student_guide.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'student':
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)


def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)
