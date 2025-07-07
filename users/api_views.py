from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import User, UserProfile, UserActivity
from .serializers import (
    UserSerializer, UserDetailSerializer, UserRegistrationSerializer,
    UserLoginSerializer, PasswordChangeSerializer, UserActivitySerializer,
    UserStatsSerializer, UserProfileSerializer
)


class UserListCreateView(generics.ListCreateAPIView):
    """List all users or create a new user"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.query_params.get('role')
        building = self.request.query_params.get('building')
        search = self.request.query_params.get('search')
        
        if role:
            queryset = queryset.filter(role=role)
        
        if building:
            queryset = queryset.filter(
                Q(apartments__building_id=building) |
                Q(managed_buildings__id=building) |
                Q(caretaker_buildings__id=building)
            ).distinct()
        
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a user"""
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object()


class UserRegistrationView(generics.CreateAPIView):
    """Register a new user"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        # Create auth token
        token, created = Token.objects.get_or_create(user=user)
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type='registration',
            description='User registered',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'User created successfully'
        }, status=status.HTTP_201_CREATED)


class UserLoginView(generics.GenericAPIView):
    """User login"""
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Create or get token
        token, created = Token.objects.get_or_create(user=user)
        
        # Update login tracking
        user.login_count += 1
        user.last_login_ip = request.META.get('REMOTE_ADDR')
        user.save()
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            description='User logged in',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        return Response({
            'user': UserDetailSerializer(user).data,
            'token': token.key,
            'message': 'Login successful'
        })


class UserLogoutView(generics.GenericAPIView):
    """User logout"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        # Delete token
        try:
            request.user.auth_token.delete()
        except:
            pass
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='logout',
            description='User logged out',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({'message': 'Logout successful'})


class PasswordChangeView(generics.GenericAPIView):
    """Change user password"""
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type='password_change',
            description='Password changed',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({'message': 'Password changed successfully'})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get or update user profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def perform_update(self, serializer):
        serializer.save()
        
        # Log activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='profile_update',
            description='Profile updated',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )


class UserActivityListView(generics.ListAPIView):
    """List user activities"""
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            # Admins can see all activities
            return UserActivity.objects.all()
        else:
            # Users can only see their own activities
            return UserActivity.objects.filter(user=user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Get user statistics"""
    if not request.user.is_admin:
        return Response({'error': 'Permission denied'}, status=403)
    
    # Calculate statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Role breakdown
    residents = User.objects.filter(role=User.RESIDENT).count()
    admins = User.objects.filter(role=User.ADMIN).count()
    caretakers = User.objects.filter(role=User.CARETAKER).count()
    security = User.objects.filter(role=User.SECURITY).count()
    
    # Verification stats
    verified_users = User.objects.filter(is_verified=True).count()
    
    # Recent registrations (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_registrations = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'residents': residents,
        'admins': admins,
        'caretakers': caretakers,
        'security': security,
        'verified_users': verified_users,
        'recent_registrations': recent_registrations
    }
    
    serializer = UserStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_dashboard_data(request):
    """Get dashboard data for the current user"""
    user = request.user
    
    # Common data
    data = {
        'user': UserDetailSerializer(user).data,
        'notifications': user.get_notification_count(),
        'complaints': user.get_complaint_count(),
    }
    
    # Role-specific data
    if user.is_admin:
        buildings = user.get_buildings()
        data.update({
            'buildings': buildings.count(),
            'total_apartments': sum(b.apartments.count() for b in buildings),
            'occupied_apartments': sum(b.apartments.filter(is_occupied=True).count() for b in buildings),
        })
    
    elif user.is_resident:
        apartments = user.get_apartments()
        data.update({
            'apartments': apartments.count(),
            'buildings': apartments.values('building').distinct().count(),
        })
    
    elif user.is_caretaker:
        buildings = user.get_buildings()
        data.update({
            'buildings': buildings.count(),
            'pending_tasks': 0,  # Would need to implement tasks
        })
    
    return Response(data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_phone(request):
    """Verify user's phone number"""
    # This would integrate with an SMS service
    # For now, just mark as verified
    user = request.user
    user.phone_verified = True
    user.save()
    
    return Response({'message': 'Phone number verified successfully'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_email(request):
    """Verify user's email"""
    # This would send a verification email
    # For now, just mark as verified
    user = request.user
    user.email_verified = True
    user.save()
    
    return Response({'message': 'Email verified successfully'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_users(request):
    """Search users by name or email"""
    query = request.query_params.get('q', '')
    if not query:
        return Response({'users': []})
    
    users = User.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    )[:10]  # Limit to 10 results
    
    serializer = UserSerializer(users, many=True)
    return Response({'users': serializer.data})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_profile_picture(request):
    """Upload profile picture"""
    if 'profile_picture' not in request.FILES:
        return Response({'error': 'No file uploaded'}, status=400)
    
    user = request.user
    user.profile_picture = request.FILES['profile_picture']
    user.save()
    
    return Response({
        'message': 'Profile picture uploaded successfully',
        'profile_picture': user.profile_picture.url if user.profile_picture else None
    })


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_profile_picture(request):
    """Delete profile picture"""
    user = request.user
    if user.profile_picture:
        user.profile_picture.delete()
        user.save()
    
    return Response({'message': 'Profile picture deleted successfully'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_permissions(request):
    """Get user permissions"""
    user = request.user
    
    permissions = {
        'can_create_announcements': user.can_create_announcements,
        'can_view_financial_reports': user.can_view_financial_reports,
        'can_manage_complaints': user.can_manage_complaints,
        'is_admin': user.is_admin,
        'is_resident': user.is_resident,
        'is_caretaker': user.is_caretaker,
        'is_security': user.is_security,
        'is_staff_member': user.is_staff_member,
    }
    
    return Response(permissions)
