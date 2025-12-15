from django.urls import path
from . import views

app_name = 'parents'

urlpatterns = [
    # Dashboard
    path('', views.ParentDashboardView.as_view(), name='dashboard'),
    
    # Student details
    path('student/<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    
    # Lesson history
    path('student/<int:student_id>/lessons/', views.LessonHistoryView.as_view(), name='lesson_history'),
    
    # Homework status
    path('student/<int:student_id>/homeworks/', views.HomeworkStatusView.as_view(), name='homework_status'),
    
    # Exam results
    path('student/<int:student_id>/exams/', views.ExamResultsView.as_view(), name='exam_results'),
    
    # Attendance
    path('student/<int:student_id>/attendance/', views.AttendanceListView.as_view(), name='attendance_list'),
    
    # Monthly reports
    path('reports/', views.MonthlyReportListView.as_view(), name='monthly_report_list'),
    path('reports/<int:pk>/', views.MonthlyReportView.as_view(), name='monthly_report_detail'),
]

