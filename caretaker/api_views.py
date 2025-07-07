from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import models
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Task, Report
from .serializers import (
    TaskSerializer, TaskCreateSerializer, TaskUpdateSerializer,
    ReportSerializer, ReportCreateSerializer
)
from core.permissions import IsCaretakerOrAdmin


@extend_schema_view(
    list=extend_schema(description='List all tasks'),
    retrieve=extend_schema(description='Retrieve a specific task'),
    create=extend_schema(description='Create a new task'),
    update=extend_schema(description='Update a task'),
    partial_update=extend_schema(description='Partially update a task'),
    destroy=extend_schema(description='Delete a task'),
)
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsCaretakerOrAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'frequency', 'building', 'assigned_to']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        return TaskSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.all()
        
        if user.role == user.CARETAKER:
            # Caretakers can see tasks for buildings they manage or tasks assigned to them
            queryset = queryset.filter(
                models.Q(building__caretaker=user) | models.Q(assigned_to=user)
            )
        # Admins can see all tasks
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(description='Mark task as completed')
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.status = Task.COMPLETED
        task.completion_notes = request.data.get('completion_notes', '')
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @extend_schema(description='Get overdue tasks')
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        now = timezone.now()
        overdue_tasks = self.get_queryset().filter(
            due_date__lt=now,
            status__in=[Task.PENDING, Task.IN_PROGRESS]
        )
        serializer = self.get_serializer(overdue_tasks, many=True)
        return Response(serializer.data)

    @extend_schema(description='Get tasks by building')
    @action(detail=False, methods=['get'])
    def by_building(self, request):
        building_id = request.query_params.get('building_id')
        if not building_id:
            return Response({'error': 'building_id parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        tasks = self.get_queryset().filter(building_id=building_id)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description='List all reports'),
    retrieve=extend_schema(description='Retrieve a specific report'),
    create=extend_schema(description='Create a new report'),
    update=extend_schema(description='Update a report'),
    partial_update=extend_schema(description='Partially update a report'),
    destroy=extend_schema(description='Delete a report'),
)
class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, IsCaretakerOrAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'building']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ReportCreateSerializer
        return ReportSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Report.objects.all()
        
        if user.role == user.CARETAKER:
            # Caretakers can see reports for buildings they manage
            queryset = queryset.filter(building__caretaker=user)
        # Admins can see all reports
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(description='Get reports by building')
    @action(detail=False, methods=['get'])
    def by_building(self, request):
        building_id = request.query_params.get('building_id')
        if not building_id:
            return Response({'error': 'building_id parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        reports = self.get_queryset().filter(building_id=building_id)
        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)
