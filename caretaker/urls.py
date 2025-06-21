from django.urls import path
from .views import (
    TaskListView, TaskDetailView, TaskCreateView, TaskUpdateView,
    CaretakerTaskListView, CompleteTaskView, UploadTaskImageView
)

urlpatterns = [
    # Admin routes
    path('tasks/', TaskListView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task_detail'),
    path('tasks/create/', TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/update/', TaskUpdateView.as_view(), name='task_update'),
    
    # Caretaker routes
    path('my-tasks/', CaretakerTaskListView.as_view(), name='caretaker_task_list'),
    path('tasks/<int:pk>/complete/', CompleteTaskView.as_view(), name='complete_task'),
    path('tasks/<int:pk>/upload-image/', UploadTaskImageView.as_view(), name='upload_task_image'),
]
