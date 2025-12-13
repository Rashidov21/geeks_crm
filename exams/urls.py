from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('', views.ExamListView.as_view(), name='exam_list'),
    path('<int:pk>/', views.ExamDetailView.as_view(), name='exam_detail'),
    path('<int:pk>/take/', views.ExamTakeView.as_view(), name='exam_take'),
    path('result/<int:pk>/', views.ExamResultView.as_view(), name='exam_result'),
]

