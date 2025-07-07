from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterFilter
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    Announcement, AnnouncementCategory, AnnouncementTemplate,
    AnnouncementRead, AnnouncementComment, AnnouncementLike,
    AnnouncementShare, AnnouncementFeedback, get_announcement_statistics
)
from .serializers import (
    AnnouncementListSerializer, AnnouncementDetailSerializer,
    AnnouncementCreateUpdateSerializer, AnnouncementCategorySerializer,
    AnnouncementTemplateSerializer, AnnouncementCommentSerializer,
    AnnouncementStatsSerializer, AnnouncementQuickActionSerializer
)
from .permissions import AnnouncementPermission
from core.permissions import IsAdminOrReadOnly


class AnnouncementCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for announcement categories"""
    
    queryset = AnnouncementCategory.objects.filter(is_active=True)
    serializer_class = AnnouncementCategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class AnnouncementTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for announcement templates"""
    
    queryset = AnnouncementTemplate.objects.filter(is_active=True)
    serializer_class = AnnouncementTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterFilter]
    search_fields = ['name', 'title_template', 'content_template']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    filterset_fields = ['category', 'priority']


class AnnouncementViewSet(viewsets.ModelViewSet):
    """ViewSet for announcements"""
    
    permission_classes = [IsAuthenticated, AnnouncementPermission]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterFilter]
    search_fields = ['title', 'content', 'short_description']
    ordering_fields = ['created_at', 'updated_at', 'publish_at', 'view_count', 'read_count']
    ordering = ['-is_pinned', '-publish_at']
    filterset_fields = [
        'category', 'priority', 'announcement_type', 'status',
        'is_pinned', 'is_urgent', 'building'
    ]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Announcement.objects.select_related(
            'building', 'category', 'created_by', 'updated_by'
        ).prefetch_related('reads', 'comments', 'likes')
        
        # Filter by user permissions
        if user.is_staff or user.is_superuser:
            return queryset
        else:
            # Get announcements for user's building
            try:
                if hasattr(user, 'apartment') and user.apartment:
                    return queryset.filter(
                        building=user.apartment.building,
                        status='published'
                    )
                else:
                    return queryset.none()
            except:
                return queryset.none()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AnnouncementListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AnnouncementCreateUpdateSerializer
        else:
            return AnnouncementDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Track view
        self.track_view(instance, request.user)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def track_view(self, announcement, user):
        """Track announcement view"""
        from .models import AnnouncementView
        
        # Get client IP
        ip = self.get_client_ip()
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        referer = self.request.META.get('HTTP_REFERER', '')
        
        # Create view record
        AnnouncementView.objects.create(
            announcement=announcement,
            user=user if user.is_authenticated else None,
            ip_address=ip,
            user_agent=user_agent,
            referer=referer
        )
        
        # Increment view count
        announcement.increment_view_count()
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark announcement as read"""
        announcement = self.get_object()
        user = request.user
        
        # Mark as read
        announcement.mark_as_read_by(user)
        
        return Response({'status': 'marked as read'})
    
    @action(detail=True, methods=['post'])
    def toggle_like(self, request, pk=None):
        """Toggle like status"""
        announcement = self.get_object()
        user = request.user
        
        like, created = AnnouncementLike.objects.get_or_create(
            announcement=announcement,
            user=user
        )
        
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        
        return Response({
            'liked': liked,
            'total_likes': announcement.likes.count()
        })
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add comment to announcement"""
        announcement = self.get_object()
        user = request.user
        
        if not announcement.allow_comments:
            return Response(
                {'error': 'Comments are not allowed for this announcement'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AnnouncementCommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(
                announcement=announcement,
                user=user,
                is_approved=True  # Auto-approve for now
            )
            return Response(
                AnnouncementCommentSerializer(comment).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get announcement comments"""
        announcement = self.get_object()
        
        if not announcement.allow_comments:
            return Response({'comments': []})
        
        comments = announcement.comments.filter(
            is_approved=True,
            parent=None
        ).order_by('-created_at')
        
        serializer = AnnouncementCommentSerializer(comments, many=True)
        return Response({'comments': serializer.data})
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Track announcement share"""
        announcement = self.get_object()
        user = request.user
        platform = request.data.get('platform', 'unknown')
        
        # Track share
        AnnouncementShare.objects.create(
            announcement=announcement,
            user=user,
            platform=platform
        )
        
        return Response({'status': 'shared'})
    
    @action(detail=True, methods=['post'])
    def feedback(self, request, pk=None):
        """Submit feedback for announcement"""
        announcement = self.get_object()
        user = request.user
        
        feedback_type = request.data.get('feedback_type')
        comment = request.data.get('comment', '')
        
        # Create or update feedback
        feedback, created = AnnouncementFeedback.objects.get_or_create(
            announcement=announcement,
            user=user,
            defaults={
                'feedback_type': feedback_type,
                'comment': comment
            }
        )
        
        if not created:
            feedback.feedback_type = feedback_type
            feedback.comment = comment
            feedback.save()
        
        return Response({'status': 'feedback submitted'})
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get announcement statistics"""
        announcement = self.get_object()
        
        stats = {
            'total_views': announcement.view_count,
            'total_reads': announcement.read_count,
            'total_likes': announcement.likes.count(),
            'total_comments': announcement.comments.filter(is_approved=True).count(),
            'total_shares': announcement.shares.count(),
            'read_percentage': announcement.get_read_percentage(),
            'target_user_count': announcement.get_target_users().count(),
            'feedback_summary': announcement.feedbacks.values('feedback_type').annotate(
                count=Count('id')
            )
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def quick_action(self, request):
        """Perform quick actions on announcements"""
        serializer = AnnouncementQuickActionSerializer(data=request.data)
        if serializer.is_valid():
            action_type = serializer.validated_data['action']
            announcement_id = request.data.get('announcement_id')
            
            if not announcement_id:
                return Response(
                    {'error': 'announcement_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            announcement = get_object_or_404(Announcement, id=announcement_id)
            
            # Check permissions
            if not self.get_permissions()[1].has_object_permission(request, self, announcement):
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if action_type == 'mark_read':
                announcement.mark_as_read_by(request.user)
                return Response({'status': 'marked as read'})
            
            elif action_type == 'toggle_like':
                like, created = AnnouncementLike.objects.get_or_create(
                    announcement=announcement,
                    user=request.user
                )
                if not created:
                    like.delete()
                    liked = False
                else:
                    liked = True
                
                return Response({
                    'liked': liked,
                    'total_likes': announcement.likes.count()
                })
            
            elif action_type == 'share':
                platform = serializer.validated_data.get('platform', 'unknown')
                AnnouncementShare.objects.create(
                    announcement=announcement,
                    user=request.user,
                    platform=platform
                )
                return Response({'status': 'shared'})
            
            elif action_type == 'feedback':
                feedback_type = serializer.validated_data.get('feedback_type')
                comment = serializer.validated_data.get('comment', '')
                
                feedback, created = AnnouncementFeedback.objects.get_or_create(
                    announcement=announcement,
                    user=request.user,
                    defaults={
                        'feedback_type': feedback_type,
                        'comment': comment
                    }
                )
                
                if not created:
                    feedback.feedback_type = feedback_type
                    feedback.comment = comment
                    feedback.save()
                
                return Response({'status': 'feedback submitted'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_announcements(self, request):
        """Get user's building announcements"""
        user = request.user
        
        try:
            if hasattr(user, 'apartment') and user.apartment:
                announcements = Announcement.objects.filter(
                    building=user.apartment.building,
                    status='published'
                ).select_related('category', 'created_by')
                
                # Apply filters
                category = request.query_params.get('category')
                if category:
                    announcements = announcements.filter(category_id=category)
                
                priority = request.query_params.get('priority')
                if priority:
                    announcements = announcements.filter(priority=priority)
                
                read_status = request.query_params.get('read_status')
                if read_status == 'unread':
                    read_ids = AnnouncementRead.objects.filter(
                        user=user
                    ).values_list('announcement_id', flat=True)
                    announcements = announcements.exclude(id__in=read_ids)
                elif read_status == 'read':
                    read_ids = AnnouncementRead.objects.filter(
                        user=user
                    ).values_list('announcement_id', flat=True)
                    announcements = announcements.filter(id__in=read_ids)
                
                # Order by pinned first, then by publish date
                announcements = announcements.order_by('-is_pinned', '-publish_at')
                
                # Paginate
                page = self.paginate_queryset(announcements)
                if page is not None:
                    serializer = AnnouncementListSerializer(
                        page, many=True, context={'request': request}
                    )
                    return self.get_paginated_response(serializer.data)
                
                serializer = AnnouncementListSerializer(
                    announcements, many=True, context={'request': request}
                )
                return Response(serializer.data)
            else:
                return Response([])
        except:
            return Response([])
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get announcement analytics"""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        building_id = request.query_params.get('building')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Get statistics
        stats = get_announcement_statistics(
            building_id=building_id,
            start_date=start_date,
            end_date=end_date
        )
        
        serializer = AnnouncementStatsSerializer(stats)
        return Response(serializer.data)


class AnnouncementCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for announcement comments"""
    
    serializer_class = AnnouncementCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return AnnouncementComment.objects.filter(
            is_approved=True
        ).select_related('user', 'announcement')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_approved=True)
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only allow users to edit/delete their own comments
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def check_object_permissions(self, request, obj):
        """Check object permissions"""
        super().check_object_permissions(request, obj)
        
        # Users can only edit/delete their own comments
        if self.action in ['update', 'partial_update', 'destroy']:
            if obj.user != request.user and not request.user.is_staff:
                self.permission_denied(request)


# Additional API views for specific functionality
class AnnouncementStatsAPIView(generics.RetrieveAPIView):
    """API view for announcement statistics"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Get user's building statistics
        stats = {}
        
        try:
            if hasattr(user, 'apartment') and user.apartment:
                building = user.apartment.building
                
                # Total announcements
                total_announcements = Announcement.objects.filter(
                    building=building,
                    status='published'
                ).count()
                
                # Read announcements
                read_announcements = AnnouncementRead.objects.filter(
                    user=user,
                    announcement__building=building
                ).count()
                
                # Unread announcements
                unread_announcements = total_announcements - read_announcements
                
                # Urgent announcements
                urgent_announcements = Announcement.objects.filter(
                    building=building,
                    status='published',
                    is_urgent=True
                ).count()
                
                # Read percentage
                read_percentage = (read_announcements / total_announcements * 100) if total_announcements > 0 else 0
                
                stats = {
                    'total': total_announcements,
                    'read': read_announcements,
                    'unread': unread_announcements,
                    'urgent': urgent_announcements,
                    'read_percentage': read_percentage
                }
            else:
                stats = {
                    'total': 0,
                    'read': 0,
                    'unread': 0,
                    'urgent': 0,
                    'read_percentage': 0
                }
        except:
            stats = {
                'total': 0,
                'read': 0,
                'unread': 0,
                'urgent': 0,
                'read_percentage': 0
            }
        
        return Response(stats)
