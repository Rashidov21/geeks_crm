from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy
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
                    date__gte=date_threshold,
                    is_present=True
                ).values('student').distinct()
                context['mentor_active_students_count'] = active_attendances.count()
            else:
                context['mentor_active_students_count'] = 0
        
        return context


class ProfileEditView(UpdateView):
    model = User
    template_name = 'accounts/profile_edit.html'
    fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profil muvaffaqiyatli yangilandi.')
        return super().form_valid(form)


# Custom error handlers
def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)