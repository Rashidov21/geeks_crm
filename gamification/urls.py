from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    # Points
    path('points/<int:group_id>/', views.StudentPointsView.as_view(), name='student_points'),
    path('points/history/', views.PointHistoryView.as_view(), name='point_history'),
    
    # Badges
    path('badges/', views.StudentBadgesView.as_view(), name='student_badges'),
    
    # Rankings
    path('ranking/group/<int:group_id>/', views.GroupRankingView.as_view(), name='group_ranking'),
    path('ranking/branch/<int:branch_id>/', views.BranchRankingView.as_view(), name='branch_ranking'),
    path('ranking/overall/', views.OverallRankingView.as_view(), name='overall_ranking'),
    path('ranking/monthly/<str:ranking_type>/', views.MonthlyRankingView.as_view(), name='monthly_ranking'),
    path('ranking/monthly/<str:ranking_type>/<int:year>/<int:month>/', views.MonthlyRankingView.as_view(), name='monthly_ranking_detail'),
]

