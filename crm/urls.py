from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # Dashboard / Kanban
    path('', views.LeadKanbanView.as_view(), name='dashboard'),
    path('kanban/', views.LeadKanbanView.as_view(), name='kanban'),
    
    # Leads
    path('leads/', views.LeadListView.as_view(), name='lead_list'),
    path('leads/table/', views.LeadTableView.as_view(), name='lead_table'),
    path('leads/create/', views.LeadCreateView.as_view(), name='lead_create'),
    path('leads/<int:pk>/', views.LeadDetailView.as_view(), name='lead_detail'),
    path('leads/<int:pk>/edit/', views.LeadUpdateView.as_view(), name='lead_edit'),
    path('leads/<int:pk>/delete/', views.LeadDeleteView.as_view(), name='lead_delete'),
    path('leads/<int:pk>/assign/', views.LeadAssignView.as_view(), name='lead_assign'),
    path('leads/<int:pk>/status/', views.LeadStatusUpdateView.as_view(), name='lead_status_update'),
    path('leads/<int:pk>/group/', views.LeadGroupAssignView.as_view(), name='lead_group_assign'),
    path('leads/import/', views.LeadImportExcelView.as_view(), name='lead_import'),
    path('leads/google-sheets-import/', views.LeadGoogleSheetsImportView.as_view(), name='lead_google_import'),
    path('leads/export/', views.LeadExportView.as_view(), name='lead_export'),
    
    # Trial Lessons
    path('leads/<int:lead_pk>/trial/register/', views.TrialRegisterView.as_view(), name='trial_register'),
    path('trials/<int:pk>/result/', views.TrialResultView.as_view(), name='trial_result'),
    path('trials/create/', views.TrialLessonCreateView.as_view(), name='trial_lesson_create'),
    path('trials/<int:pk>/edit/', views.TrialLessonUpdateView.as_view(), name='trial_lesson_edit'),
    
    # Follow-ups
    path('followups/', views.FollowUpListView.as_view(), name='followup_list'),
    path('followups/today/', views.FollowUpTodayView.as_view(), name='followup_today'),
    path('followups/overdue/', views.FollowUpOverdueView.as_view(), name='followup_overdue'),
    path('followups/create/', views.FollowUpCreateView.as_view(), name='followup_create'),
    path('followups/<int:pk>/edit/', views.FollowUpUpdateView.as_view(), name='followup_edit'),
    path('followups/<int:pk>/complete/', views.FollowUpCompleteView.as_view(), name='followup_complete'),
    path('followups/overdue/bulk/reschedule/', views.FollowUpBulkRescheduleView.as_view(), name='followup_bulk_reschedule'),
    path('followups/overdue/bulk/reassign/', views.FollowUpBulkReassignView.as_view(), name='followup_bulk_reassign'),
    path('followups/overdue/bulk/complete/', views.FollowUpBulkCompleteView.as_view(), name='followup_bulk_complete'),
    path('followups/overdue/bulk/delete/', views.FollowUpBulkDeleteView.as_view(), name='followup_bulk_delete'),
    
    # Offers
    path('offers/', views.OfferListView.as_view(), name='offer_list'),
    path('offers/create/', views.OfferCreateView.as_view(), name='offer_create'),
    path('offers/<int:pk>/edit/', views.OfferUpdateView.as_view(), name='offer_edit'),
    path('offers/<int:pk>/delete/', views.OfferDeleteView.as_view(), name='offer_delete'),
    
    # Leave Requests
    path('leaves/', views.LeaveListView.as_view(), name='leave_list'),
    path('leaves/create/', views.LeaveCreateView.as_view(), name='leave_create'),
    path('leaves/pending/', views.LeavePendingView.as_view(), name='leave_pending'),
    path('leaves/<int:pk>/approve/', views.LeaveApproveView.as_view(), name='leave_approve'),
    
    # Sales Users
    path('users/sales/', views.SalesUserListView.as_view(), name='sales_list'),
    path('users/sales/create/', views.SalesUserCreateView.as_view(), name='sales_create'),
    path('users/sales/<int:pk>/edit/', views.SalesUserUpdateView.as_view(), name='sales_edit'),
    path('users/sales/<int:pk>/delete/', views.SalesUserDeleteView.as_view(), name='sales_delete'),
    path('users/sales/<int:pk>/absence/', views.SalesUserAbsenceView.as_view(), name='sales_absence'),
    
    # Manager Users
    path('users/managers/', views.ManagerUserListView.as_view(), name='manager_list'),
    path('users/managers/create/', views.ManagerUserCreateView.as_view(), name='manager_create'),
    path('users/managers/<int:pk>/edit/', views.ManagerUserUpdateView.as_view(), name='manager_edit'),
    path('users/managers/<int:pk>/delete/', views.ManagerUserDeleteView.as_view(), name='manager_delete'),
    
    # Work Schedules
    path('work-schedules/', views.WorkScheduleListView.as_view(), name='work_schedule_list'),
    path('work-schedules/create/', views.WorkScheduleCreateView.as_view(), name='work_schedule_create'),
    path('work-schedules/<int:pk>/edit/', views.WorkScheduleUpdateView.as_view(), name='work_schedule_edit'),
    path('work-schedules/<int:pk>/delete/', views.WorkScheduleDeleteView.as_view(), name='work_schedule_delete'),
    
    # Messages
    path('messages/', views.MessageListView.as_view(), name='message_list'),
    path('messages/create/', views.MessageCreateView.as_view(), name='message_create'),
    path('messages/sent/', views.MessageSentView.as_view(), name='message_sent'),
    path('messages/inbox/', views.MessageInboxView.as_view(), name='message_inbox'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
    path('messages/<int:pk>/delete/', views.MessageDeleteView.as_view(), name='message_delete'),
    
    # Analytics / KPI
    path('analytics/', views.CRMAnalyticsView.as_view(), name='analytics'),
    path('kpi/', views.SalesKPIListView.as_view(), name='sales_kpi'),
    path('kpi/my/', views.SalesKPIDetailView.as_view(), name='sales_kpi_my'),
    path('kpi/my/<int:year>/<int:month>/', views.SalesKPIDetailView.as_view(), name='sales_kpi_my_month'),
    path('kpi/<int:sales_id>/', views.SalesKPIDetailView.as_view(), name='sales_kpi_detail'),
    path('kpi/<int:sales_id>/<int:year>/<int:month>/', views.SalesKPIDetailView.as_view(), name='sales_kpi_detail_month'),
    path('kpi/ranking/', views.SalesKPIRankingView.as_view(), name='sales_kpi_ranking'),
    
    # Reactivations
    path('reactivations/', views.ReactivationListView.as_view(), name='reactivation_list'),
    
    # Landing
    path('landing/', views.LandingView.as_view(), name='landing'),
]
