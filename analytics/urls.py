from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.StatisticsDashboardView.as_view(), name='dashboard'),
    path('branches/', views.BranchStatisticsView.as_view(), name='branch_statistics'),
    path('branch/<int:branch_id>/', views.BranchStatisticsView.as_view(), name='branch_statistics_detail'),
    path('courses/', views.CourseStatisticsView.as_view(), name='course_statistics'),
    path('course/<int:course_id>/', views.CourseStatisticsView.as_view(), name='course_statistics_detail'),
]

