from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.AttendanceListView.as_view(), name='attendance_list'),
    path('form/', views.AttendanceCreateView.as_view(), name='attendance_form'),
    path('lesson/<int:lesson_id>/', views.AttendanceCreateView.as_view(), name='attendance_create'),
    path('group/<int:group_id>/', views.GroupAttendanceView.as_view(), name='group_attendance'),
    path('toggle/', views.AttendanceToggleView.as_view(), name='attendance_toggle'),
    path('save-grade/', views.SaveGradeView.as_view(), name='save_grade'),
    path('save-comment/', views.SaveParentCommentView.as_view(), name='save_comment'),
    path('statistics/', views.AttendanceStatisticsView.as_view(), name='attendance_statistics'),
]

