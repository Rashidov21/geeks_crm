from django.urls import path
from . import views

app_name = 'homework'

urlpatterns = [
    path('', views.HomeworkListView.as_view(), name='homework_list'),
    path('create/', views.HomeworkCreateView.as_view(), name='homework_create'),
    path('assign/', views.HomeworkAssignView.as_view(), name='homework_assign'),
    path('bulk-grade/', views.HomeworkBulkGradeView.as_view(), name='homework_bulk_grade'),
    path('<int:pk>/', views.HomeworkDetailView.as_view(), name='homework_detail'),
    path('<int:pk>/grade/', views.HomeworkGradeView.as_view(), name='homework_grade'),
    path('<int:pk>/submit/', views.HomeworkSubmitView.as_view(), name='homework_submit'),
]
