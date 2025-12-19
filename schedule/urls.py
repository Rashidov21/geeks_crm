from django.urls import path
from . import views

app_name = 'schedule'

urlpatterns = [
    path('', views.TimetableView.as_view(), name='timetable'),
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path('rooms/', views.RoomScheduleView.as_view(), name='rooms'),
]

