from rest_framework import serializers
from .models import Building, Apartment
from users.serializers import UserSerializer


class BuildingSerializer(serializers.ModelSerializer):
    caretaker = UserSerializer(read_only=True)
    admin = UserSerializer(read_only=True)
    
    class Meta:
        model = Building
        fields = [
            'id', 'name', 'address', 'block_count', 'floors_per_block', 
            'apartments_per_floor', 'caretaker', 'admin', 'construction_year',
            'total_area_sqm', 'energy_efficiency_class', 'common_areas',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ApartmentSerializer(serializers.ModelSerializer):
    building = BuildingSerializer(read_only=True)
    resident = UserSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Apartment
        fields = [
            'id', 'building', 'block', 'floor', 'number', 'size_sqm', 
            'bedroom_count', 'resident', 'resident_type', 'owner', 
            'is_occupied', 'occupant_count'
        ]
        read_only_fields = ['id']


class BuildingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = [
            'name', 'address', 'block_count', 'floors_per_block', 
            'apartments_per_floor', 'caretaker', 'admin', 'construction_year',
            'total_area_sqm', 'energy_efficiency_class', 'common_areas'
        ]


class ApartmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apartment
        fields = [
            'building', 'block', 'floor', 'number', 'size_sqm', 
            'bedroom_count', 'resident', 'resident_type', 'owner', 
            'is_occupied', 'occupant_count'
        ]
