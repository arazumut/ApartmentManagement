from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Task, TaskImage
from users.models import User

# Create your views here.

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'caretaker/task_list.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        return Task.objects.all().order_by('-created_at')


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'caretaker/task_detail.html'
    context_object_name = 'task'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images'] = self.object.taskimage_set.all()
        return context


class TaskCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Task
    template_name = 'caretaker/task_form.html'
    fields = ['building', 'title', 'description', 'assigned_to', 'priority', 
              'due_date', 'frequency', 'recurrence_end_date']
    success_url = reverse_lazy('task_list')
    
    def test_func(self):
        # Only staff or managers can create tasks
        return self.request.user.is_staff or self.request.user.role == User.MANAGER
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.status = Task.PENDING
        return super().form_valid(form)


class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Task
    template_name = 'caretaker/task_form.html'
    fields = ['building', 'title', 'description', 'assigned_to', 'status', 
              'priority', 'due_date', 'frequency', 'recurrence_end_date']
    
    def test_func(self):
        # Only staff, managers, or the assigned caretaker can update tasks
        task = self.get_object()
        user = self.request.user
        return (user.is_staff or 
                user.role == User.MANAGER or 
                (user.role == User.CARETAKER and task.assigned_to == user))
    
    def get_success_url(self):
        return reverse_lazy('task_detail', kwargs={'pk': self.object.pk})


class CaretakerTaskListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Task
    template_name = 'caretaker/caretaker_task_list.html'
    context_object_name = 'tasks'
    
    def test_func(self):
        # Only caretakers can view their assigned tasks
        return self.request.user.role == User.CARETAKER
    
    def get_queryset(self):
        return Task.objects.filter(assigned_to=self.request.user).order_by('status', '-priority')


class CompleteTaskView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # Only the assigned caretaker can mark a task as complete
        task = get_object_or_404(Task, pk=self.kwargs.get('pk'))
        return self.request.user == task.assigned_to
    
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        completion_notes = request.POST.get('completion_notes', '')
        
        task.status = Task.COMPLETED
        task.completion_notes = completion_notes
        task.save()
        
        messages.success(request, f'Task "{task.title}" marked as complete.')
        return redirect('caretaker_task_list')


class UploadTaskImageView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # Only the assigned caretaker can upload images for a task
        task = get_object_or_404(Task, pk=self.kwargs.get('pk'))
        return self.request.user == task.assigned_to
    
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        image = request.FILES.get('image')
        
        if image:
            TaskImage.objects.create(task=task, image=image)
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'No image provided'})