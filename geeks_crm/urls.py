"""
URL configuration for geeks_crm project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import never_cache
from ckeditor_uploader import views as ckeditor_views
from accounts.dashboard_views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('', DashboardView.as_view(), name='dashboard'),
    path('accounts/', include('accounts.urls')),
    path('courses/', include('courses.urls')),
    path('attendance/', include('attendance.urls')),
    path('homework/', include('homework.urls')),
    path('exams/', include('exams.urls')),
    path('gamification/', include('gamification.urls')),
    path('mentors/', include('mentors.urls')),
    path('parents/', include('parents.urls')),
    path('crm/', include('crm.urls')),
    path('analytics/', include('analytics.urls')),
    path('finance/', include('finance.urls')),
    path('telegram/', include('telegram_bot.urls')),
    path('schedule/', include('schedule.urls')),
]

# Media and Static files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'accounts.views.custom_404'
handler500 = 'accounts.views.custom_500'
