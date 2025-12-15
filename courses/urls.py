from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Courses
    path('', views.CourseListView.as_view(), name='course_list'),
    path('<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    
    # Modules and Topics
    path('module/<int:pk>/', views.ModuleDetailView.as_view(), name='module_detail'),
    path('topic/<int:pk>/', views.TopicDetailView.as_view(), name='topic_detail'),
    
    # Groups
    path('groups/', views.GroupListView.as_view(), name='group_list'),
    path('groups/<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    
    # Lessons
    path('lessons/', views.LessonListView.as_view(), name='lesson_list'),
    path('lessons/<int:pk>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    
    # Progress
    path('progress/', views.StudentProgressView.as_view(), name='progress'),
    
    # Group Transfers
    path('transfers/', views.GroupTransferListView.as_view(), name='group_transfer_list'),
    path('transfers/create/', views.GroupTransferCreateView.as_view(), name='group_transfer_create'),
]

