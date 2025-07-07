from rest_framework import serializers
from .models import Task, Report
from buildings.serializers import BuildingSerializer
from users.serializers import UserSerializer


class TaskSerializer(serializers.ModelSerializer):
    building = BuildingSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    building_id = serializers.IntegerField(write_only=True)
    assigned_to_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'building', 'title', 'description', 'assigned_to', 'status',
            'priority', 'due_date', 'frequency', 'recurrence_end_date',
            'created_by', 'completion_notes', 'created_at', 'updated_at',
            'building_id', 'assigned_to_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'building', 'title', 'description', 'assigned_to', 'priority',
            'due_date', 'frequency', 'recurrence_end_date'
        ]


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'assigned_to', 'status', 'priority',
            'due_date', 'frequency', 'recurrence_end_date', 'completion_notes'
        ]


class ReportSerializer(serializers.ModelSerializer):
    building = BuildingSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    building_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'building', 'title', 'description', 'type', 'images',
            'created_by', 'created_at', 'updated_at', 'building_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class ReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            'building', 'title', 'description', 'type', 'images'
        ]
