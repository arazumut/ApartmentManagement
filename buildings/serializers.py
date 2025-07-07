from rest_framework import serializers
from .models import Building, Apartment

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['id', 'name', 'address', 'description', 'admin', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class ApartmentSerializer(serializers.ModelSerializer):
    building = BuildingSerializer(read_only=True)
    
    class Meta:
        model = Apartment
        fields = ['id', 'building', 'apartment_number', 'floor', 'resident', 'owner', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
