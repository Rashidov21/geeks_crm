from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.StatisticsDashboardView.as_view(), name='dashboard'),
    path('branch/<int:branch_id>/', views.BranchStatisticsView.as_view(), name='branch_statistics'),
    path('course/<int:course_id>/', views.CourseStatisticsView.as_view(), name='course_statistics'),
]

