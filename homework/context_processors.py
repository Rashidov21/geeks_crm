from django.utils import timezone
from .models import Homework


def homework_notifications(request):
    """
    Sidebar badge'lar uchun context processor
    """
    context = {}
    
    if request.user.is_authenticated:
        if request.user.is_mentor:
            # Mentor uchun: topshirilgan lekin baholanmagan vazifalar soni
            submitted_count = Homework.objects.filter(
                lesson__group__mentor=request.user,
                is_submitted=True
            ).filter(
                grade__isnull=True
            ).count()
            context['submitted_homeworks_count'] = submitted_count
        
        elif request.user.is_student:
            # Student uchun: topshirmagan vazifalar soni
            pending_count = Homework.objects.filter(
                student=request.user,
                is_submitted=False
            ).count()
            context['pending_homeworks_count'] = pending_count
    
    return context

