from django.urls import path
from . import views

app_name = 'homework'

urlpatterns = [
    path('', views.HomeworkListView.as_view(), name='homework_list'),
    path('create/', views.HomeworkCreateView.as_view(), name='homework_create'),
    path('<int:pk>/', views.HomeworkDetailView.as_view(), name='homework_detail'),
    path('<int:pk>/grade/', views.HomeworkGradeView.as_view(), name='homework_grade'),
]

