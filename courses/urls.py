from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Courses
    path('', views.CourseListView.as_view(), name='course_list'),
    path('create/', views.CourseCreateView.as_view(), name='course_create'),
    path('<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_edit'),
    path('<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    
    # Modules
    path('<int:course_id>/modules/create/', views.ModuleCreateView.as_view(), name='module_create'),
    path('module/<int:pk>/', views.ModuleDetailView.as_view(), name='module_detail'),
    path('module/<int:pk>/edit/', views.ModuleUpdateView.as_view(), name='module_edit'),
    path('module/<int:pk>/delete/', views.ModuleDeleteView.as_view(), name='module_delete'),
    
    # Topics
    path('module/<int:module_id>/topics/create/', views.TopicCreateView.as_view(), name='topic_create'),
    path('topic/<int:pk>/', views.TopicDetailView.as_view(), name='topic_detail'),
    path('topic/<int:pk>/edit/', views.TopicUpdateView.as_view(), name='topic_edit'),
    path('topic/<int:pk>/delete/', views.TopicDeleteView.as_view(), name='topic_delete'),
    
    # Groups
    path('groups/', views.GroupListView.as_view(), name='group_list'),
    path('groups/create/', views.GroupCreateView.as_view(), name='group_create'),
    path('groups/<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('groups/<int:pk>/edit/', views.GroupUpdateView.as_view(), name='group_edit'),
    path('groups/<int:pk>/delete/', views.GroupDeleteView.as_view(), name='group_delete'),
    path('groups/<int:pk>/add-student/', views.GroupAddStudentView.as_view(), name='group_add_student'),
    path('groups/<int:pk>/convert-lead/', views.ConvertLeadToStudentView.as_view(), name='convert_lead_to_student'),
    path('groups/<int:pk>/students/', views.GroupStudentsView.as_view(), name='group_students'),
    
    # Lessons
    path('lessons/', views.LessonListView.as_view(), name='lesson_list'),
    path('lessons/<int:pk>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    path('lessons/<int:pk>/edit/', views.LessonUpdateView.as_view(), name='lesson_edit'),
    
    # Progress
    path('progress/', views.StudentProgressView.as_view(), name='progress'),
    
    # Group Transfers
    path('transfers/', views.GroupTransferListView.as_view(), name='group_transfer_list'),
    path('transfers/create/', views.GroupTransferCreateView.as_view(), name='group_transfer_create'),
]
