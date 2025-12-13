"""
URL configuration for geeks_crm project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('courses/', include('courses.urls')),
    path('attendance/', include('attendance.urls')),
    path('homework/', include('homework.urls')),
    path('exams/', include('exams.urls')),
    # path('gamification/', include('gamification.urls')),
    # path('mentors/', include('mentors.urls')),
    # path('parents/', include('parents.urls')),
    # path('crm/', include('crm.urls')),
    # path('finance/', include('finance.urls')),
    # path('telegram/', include('telegram_bot.urls')),
]

# Media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
