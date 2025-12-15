from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # Leads
    path('leads/', views.LeadListView.as_view(), name='lead_list'),
    path('leads/create/', views.LeadCreateView.as_view(), name='lead_create'),
    path('leads/<int:pk>/', views.LeadDetailView.as_view(), name='lead_detail'),
    path('leads/<int:pk>/edit/', views.LeadUpdateView.as_view(), name='lead_edit'),
    
    # Follow-ups
    path('followups/', views.FollowUpListView.as_view(), name='followup_list'),
    path('followups/create/', views.FollowUpCreateView.as_view(), name='followup_create'),
    path('followups/<int:pk>/edit/', views.FollowUpUpdateView.as_view(), name='followup_edit'),
    
    # Trial Lessons
    path('trials/create/', views.TrialLessonCreateView.as_view(), name='trial_lesson_create'),
    path('trials/<int:pk>/edit/', views.TrialLessonUpdateView.as_view(), name='trial_lesson_edit'),
    
    # KPI
    path('kpi/', views.SalesKPIDetailView.as_view(), name='sales_kpi'),
    path('kpi/<int:sales_id>/<int:year>/<int:month>/', views.SalesKPIDetailView.as_view(), name='sales_kpi_detail'),
    path('kpi/ranking/', views.SalesKPIRankingView.as_view(), name='sales_kpi_ranking'),
    
    # Messages
    path('messages/', views.MessageListView.as_view(), name='message_list'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
]

