from rest_framework import serializers
from .models import Package
from buildings.serializers import BuildingSerializer, ApartmentSerializer
from users.serializers import UserSerializer


class PackageSerializer(serializers.ModelSerializer):
    building = BuildingSerializer(read_only=True)
    apartment = ApartmentSerializer(read_only=True)
    received_by = UserSerializer(read_only=True)
    delivered_to = UserSerializer(read_only=True)
    building_id = serializers.IntegerField(write_only=True)
    apartment_id = serializers.IntegerField(write_only=True)
    received_by_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Package
        fields = [
            'id', 'building', 'apartment', 'tracking_number', 'sender',
            'description', 'image', 'status', 'received_by', 'received_at',
            'delivered_to', 'delivered_at', 'delivery_signature', 'notes',
            'building_id', 'apartment_id', 'received_by_id'
        ]
        read_only_fields = ['id', 'received_at', 'delivered_at']


class PackageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            'building', 'apartment', 'tracking_number', 'sender',
            'description', 'image', 'status', 'received_by'
        ]


class PackageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            'tracking_number', 'sender', 'description', 'image', 'status'
        ]
