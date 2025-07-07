from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Building, Apartment
from .serializers import (
    BuildingSerializer, BuildingCreateSerializer,
    ApartmentSerializer, ApartmentCreateSerializer
)
from core.permissions import IsCaretakerOrAdmin, IsResidentOwnerOrCaretaker


@extend_schema_view(
    list=extend_schema(description='List all buildings'),
    retrieve=extend_schema(description='Retrieve a specific building'),
    create=extend_schema(description='Create a new building'),
    update=extend_schema(description='Update a building'),
    partial_update=extend_schema(description='Partially update a building'),
    destroy=extend_schema(description='Delete a building'),
)
class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['block_count', 'floors_per_block', 'construction_year']
    search_fields = ['name', 'address', 'common_areas']
    ordering_fields = ['created_at', 'name', 'construction_year']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return BuildingCreateSerializer
        return BuildingSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsCaretakerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @extend_schema(description='Get apartments in this building')
    @action(detail=True, methods=['get'])
    def apartments(self, request, pk=None):
        building = self.get_object()
        apartments = building.apartments.all()
        serializer = ApartmentSerializer(apartments, many=True)
        return Response(serializer.data)

    @extend_schema(description='Get building statistics')
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        building = self.get_object()
        apartments = building.apartments.all()
        
        stats = {
            'total_apartments': apartments.count(),
            'occupied_apartments': apartments.filter(is_occupied=True).count(),
            'vacant_apartments': apartments.filter(is_occupied=False).count(),
            'total_residents': sum(apt.occupant_count for apt in apartments),
            'average_apartment_size': apartments.aggregate(
                avg_size=models.Avg('size_sqm')
            )['avg_size'] or 0
        }
        return Response(stats)


@extend_schema_view(
    list=extend_schema(description='List all apartments'),
    retrieve=extend_schema(description='Retrieve a specific apartment'),
    create=extend_schema(description='Create a new apartment'),
    update=extend_schema(description='Update an apartment'),
    partial_update=extend_schema(description='Partially update an apartment'),
    destroy=extend_schema(description='Delete an apartment'),
)
class ApartmentViewSet(viewsets.ModelViewSet):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['building', 'floor', 'is_occupied', 'resident_type', 'bedroom_count']
    search_fields = ['number', 'block']
    ordering_fields = ['created_at', 'floor', 'number', 'size_sqm']
    ordering = ['building', 'floor', 'number']

    def get_serializer_class(self):
        if self.action == 'create':
            return ApartmentCreateSerializer
        return ApartmentSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsCaretakerOrAdmin]
        else:
            permission_classes = [IsAuthenticated, IsResidentOwnerOrCaretaker]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        queryset = Apartment.objects.all()
        
        if user.role == user.RESIDENT:
            # Residents can only see their own apartments
            queryset = queryset.filter(
                models.Q(resident=user) | models.Q(owner=user)
            )
        elif user.role == user.CARETAKER:
            # Caretakers can see apartments for buildings they manage
            queryset = queryset.filter(building__caretaker=user)
        # Admins can see all apartments
        
        return queryset

    @extend_schema(description='Get apartments by building')
    @action(detail=False, methods=['get'])
    def by_building(self, request):
        building_id = request.query_params.get('building_id')
        if not building_id:
            return Response({'error': 'building_id parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        apartments = self.get_queryset().filter(building_id=building_id)
        serializer = self.get_serializer(apartments, many=True)
        return Response(serializer.data)

    @extend_schema(description='Get vacant apartments')
    @action(detail=False, methods=['get'])
    def vacant(self, request):
        vacant_apartments = self.get_queryset().filter(is_occupied=False)
        serializer = self.get_serializer(vacant_apartments, many=True)
        return Response(serializer.data)
