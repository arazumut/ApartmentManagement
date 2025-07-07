from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Package
from .serializers import PackageSerializer, PackageCreateSerializer, PackageUpdateSerializer
from core.permissions import IsCaretakerOrAdmin, IsResidentOwnerOrCaretaker


@extend_schema_view(
    list=extend_schema(description='List all packages'),
    retrieve=extend_schema(description='Retrieve a specific package'),
    create=extend_schema(description='Create a new package'),
    update=extend_schema(description='Update a package'),
    partial_update=extend_schema(description='Partially update a package'),
    destroy=extend_schema(description='Delete a package'),
)
class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'building', 'apartment']
    search_fields = ['tracking_number', 'sender', 'description']
    ordering_fields = ['received_at', 'delivered_at']
    ordering = ['-received_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return PackageCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PackageUpdateSerializer
        return PackageSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsCaretakerOrAdmin]
        else:
            permission_classes = [IsAuthenticated, IsResidentOwnerOrCaretaker]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        queryset = Package.objects.all()
        
        if user.role == user.RESIDENT:
            # Residents can only see their own packages
            queryset = queryset.filter(apartment__resident=user)
        elif user.role == user.CARETAKER:
            # Caretakers can see packages for buildings they manage
            queryset = queryset.filter(building__caretaker=user)
        # Admins can see all packages
        
        return queryset

    @extend_schema(description='Mark package as delivered')
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        package = self.get_object()
        package.status = Package.DELIVERED
        package.delivered_at = timezone.now()
        package.save()
        serializer = self.get_serializer(package)
        return Response(serializer.data)

    @extend_schema(description='Get packages by building')
    @action(detail=False, methods=['get'])
    def by_building(self, request):
        building_id = request.query_params.get('building_id')
        if not building_id:
            return Response({'error': 'building_id parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        packages = self.get_queryset().filter(building_id=building_id)
        serializer = self.get_serializer(packages, many=True)
        return Response(serializer.data)

    @extend_schema(description='Get packages by apartment')
    @action(detail=False, methods=['get'])
    def by_apartment(self, request):
        apartment_id = request.query_params.get('apartment_id')
        if not apartment_id:
            return Response({'error': 'apartment_id parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        packages = self.get_queryset().filter(apartment_id=apartment_id)
        serializer = self.get_serializer(packages, many=True)
        return Response(serializer.data)
