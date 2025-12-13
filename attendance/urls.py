from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.AttendanceListView.as_view(), name='attendance_list'),
    path('lesson/<int:lesson_id>/', views.AttendanceCreateView.as_view(), name='attendance_create'),
    path('statistics/', views.AttendanceStatisticsView.as_view(), name='attendance_statistics'),
]

