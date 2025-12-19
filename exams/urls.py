from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('', views.ExamListView.as_view(), name='exam_list'),
    path('create/', views.ExamCreateView.as_view(), name='exam_create'),
    path('<int:pk>/', views.ExamDetailView.as_view(), name='exam_detail'),
    path('<int:pk>/edit/', views.ExamUpdateView.as_view(), name='exam_edit'),
    path('<int:pk>/delete/', views.ExamDeleteView.as_view(), name='exam_delete'),
    path('<int:pk>/take/', views.ExamTakeView.as_view(), name='exam_take'),
    path('<int:pk>/results/', views.ExamResultsView.as_view(), name='exam_results'),
    path('<int:pk>/entry/', views.ExamResultEntryView.as_view(), name='exam_result_entry'),
    path('result/<int:pk>/', views.ExamResultView.as_view(), name='exam_result'),
]
