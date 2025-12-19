from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Contracts
    path('contracts/', views.ContractListView.as_view(), name='contract_list'),
    path('contracts/create/', views.ContractCreateView.as_view(), name='contract_create'),
    path('contracts/<int:pk>/', views.ContractDetailView.as_view(), name='contract_detail'),
    
    # Payments
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment_create'),
    
    # Debts
    path('debts/', views.DebtListView.as_view(), name='debt_list'),
    
    # Reports
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/list/', views.FinancialReportListView.as_view(), name='financial_report_list'),
    path('reports/<int:pk>/', views.FinancialReportDetailView.as_view(), name='financial_report_detail'),
]

