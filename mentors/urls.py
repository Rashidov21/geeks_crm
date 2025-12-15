from django.urls import path
from . import views

app_name = 'mentors'

urlpatterns = [
    # KPI
    path('kpi/', views.MentorKPIView.as_view(), name='kpi'),
    path('kpi/<int:mentor_id>/<int:year>/<int:month>/', views.MentorKPIView.as_view(), name='kpi_detail'),
    
    # Rankings
    path('ranking/', views.MentorRankingView.as_view(), name='mentor_ranking'),
    path('ranking/<int:year>/<int:month>/', views.MentorRankingView.as_view(), name='mentor_ranking_detail'),
    
    # Monthly Reports
    path('reports/', views.MonthlyReportListView.as_view(), name='monthly_report_list'),
    path('reports/create/', views.MonthlyReportCreateView.as_view(), name='monthly_report_create'),
    path('reports/<int:pk>/edit/', views.MonthlyReportUpdateView.as_view(), name='monthly_report_edit'),
    
    # Lesson Quality
    path('lesson/<int:lesson_id>/rate/', views.LessonQualityCreateView.as_view(), name='lesson_quality_create'),
    
    # Parent Feedback
    path('feedback/create/', views.ParentFeedbackCreateView.as_view(), name='parent_feedback_create'),
]

