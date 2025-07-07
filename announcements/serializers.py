from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    Announcement, AnnouncementCategory, AnnouncementTemplate,
    AnnouncementRead, AnnouncementComment, AnnouncementLike,
    AnnouncementView, AnnouncementShare, AnnouncementFeedback
)
from buildings.serializers import BuildingSerializer
from users.serializers import UserSerializer


class AnnouncementCategorySerializer(serializers.ModelSerializer):
    """Serializer for announcement categories"""
    
    class Meta:
        model = AnnouncementCategory
        fields = [
            'id', 'name', 'slug', 'description', 'color', 'icon',
            'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class AnnouncementTemplateSerializer(serializers.ModelSerializer):
    """Serializer for announcement templates"""
    
    category = AnnouncementCategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = AnnouncementTemplate
        fields = [
            'id', 'name', 'category', 'category_id', 'title_template',
            'content_template', 'priority', 'auto_send_notification',
            'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class AnnouncementReadSerializer(serializers.ModelSerializer):
    """Serializer for announcement reads"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AnnouncementRead
        fields = [
            'id', 'user', 'read_at', 'device_type', 'ip_address'
        ]
        read_only_fields = ['read_at', 'ip_address']


class AnnouncementCommentSerializer(serializers.ModelSerializer):
    """Serializer for announcement comments"""
    
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = AnnouncementComment
        fields = [
            'id', 'user', 'comment', 'parent', 'is_approved',
            'is_edited', 'created_at', 'updated_at', 'replies'
        ]
        read_only_fields = ['user', 'is_approved', 'is_edited', 'created_at', 'updated_at']
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return AnnouncementCommentSerializer(
                obj.replies.filter(is_approved=True), 
                many=True
            ).data
        return []


class AnnouncementLikeSerializer(serializers.ModelSerializer):
    """Serializer for announcement likes"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AnnouncementLike
        fields = ['id', 'user', 'created_at']
        read_only_fields = ['created_at']


class AnnouncementListSerializer(serializers.ModelSerializer):
    """Serializer for announcement list view"""
    
    category = AnnouncementCategorySerializer(read_only=True)
    building = BuildingSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    # Computed fields
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_announcement_type_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    read_percentage = serializers.SerializerMethodField()
    
    # User-specific fields
    is_read_by_user = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'short_description', 'category', 'building',
            'announcement_type', 'type_display', 'priority', 'priority_display',
            'status', 'status_display', 'is_pinned', 'is_urgent',
            'publish_at', 'expires_at', 'is_expired',
            'view_count', 'read_count', 'read_percentage',
            'created_by', 'created_at', 'updated_at',
            'is_read_by_user', 'is_liked_by_user'
        ]
    
    def get_read_percentage(self, obj):
        return obj.get_read_percentage()
    
    def get_is_read_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return AnnouncementRead.objects.filter(
                announcement=obj,
                user=request.user
            ).exists()
        return False
    
    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return AnnouncementLike.objects.filter(
                announcement=obj,
                user=request.user
            ).exists()
        return False


class AnnouncementDetailSerializer(serializers.ModelSerializer):
    """Serializer for announcement detail view"""
    
    category = AnnouncementCategorySerializer(read_only=True)
    building = BuildingSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Computed fields
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_announcement_type_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    read_percentage = serializers.SerializerMethodField()
    
    # User-specific fields
    is_read_by_user = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    
    # Related data
    comments = serializers.SerializerMethodField()
    total_likes = serializers.SerializerMethodField()
    total_comments = serializers.SerializerMethodField()
    
    # URLs
    image_url = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'short_description', 'content', 'category',
            'building', 'announcement_type', 'type_display', 'priority',
            'priority_display', 'status', 'status_display', 'is_pinned',
            'is_urgent', 'publish_at', 'expires_at', 'is_expired',
            'allow_comments', 'image', 'image_url', 'attachment', 'attachment_url',
            'tags', 'metadata', 'view_count', 'read_count', 'read_percentage',
            'created_by', 'updated_by', 'created_at', 'updated_at',
            'is_read_by_user', 'is_liked_by_user', 'comments',
            'total_likes', 'total_comments'
        ]
    
    def get_read_percentage(self, obj):
        return obj.get_read_percentage()
    
    def get_is_read_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return AnnouncementRead.objects.filter(
                announcement=obj,
                user=request.user
            ).exists()
        return False
    
    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return AnnouncementLike.objects.filter(
                announcement=obj,
                user=request.user
            ).exists()
        return False
    
    def get_comments(self, obj):
        if obj.allow_comments:
            comments = obj.comments.filter(is_approved=True, parent=None)
            return AnnouncementCommentSerializer(comments, many=True).data
        return []
    
    def get_total_likes(self, obj):
        return obj.likes.count()
    
    def get_total_comments(self, obj):
        return obj.comments.filter(is_approved=True).count()
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_attachment_url(self, obj):
        if obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            return obj.attachment.url
        return None


class AnnouncementCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating announcements"""
    
    category_id = serializers.IntegerField(required=False, allow_null=True)
    building_id = serializers.IntegerField()
    target_group_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    target_apartment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Announcement
        fields = [
            'title', 'short_description', 'content', 'category_id',
            'building_id', 'announcement_type', 'priority', 'status',
            'image', 'attachment', 'target_group_ids', 'target_apartment_ids',
            'publish_at', 'expires_at', 'allow_comments', 'is_pinned',
            'is_urgent', 'send_notification', 'send_email', 'send_sms',
            'tags', 'metadata'
        ]
    
    def validate_category_id(self, value):
        if value and not AnnouncementCategory.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError(_('Geçersiz kategori ID\'si'))
        return value
    
    def validate_building_id(self, value):
        from buildings.models import Building
        if not Building.objects.filter(id=value).exists():
            raise serializers.ValidationError(_('Geçersiz bina ID\'si'))
        return value
    
    def validate_target_group_ids(self, value):
        if value:
            from django.contrib.auth.models import Group
            existing_ids = set(Group.objects.filter(id__in=value).values_list('id', flat=True))
            if set(value) != existing_ids:
                raise serializers.ValidationError(_('Geçersiz grup ID\'leri'))
        return value
    
    def validate_target_apartment_ids(self, value):
        if value:
            from buildings.models import Apartment
            existing_ids = set(Apartment.objects.filter(id__in=value).values_list('id', flat=True))
            if set(value) != existing_ids:
                raise serializers.ValidationError(_('Geçersiz daire ID\'leri'))
        return value
    
    def validate(self, data):
        # Check if expires_at is after publish_at
        if data.get('expires_at') and data.get('publish_at'):
            if data['expires_at'] <= data['publish_at']:
                raise serializers.ValidationError({
                    'expires_at': _('Son geçerlilik tarihi yayın tarihinden sonra olmalıdır')
                })
        
        return data
    
    def create(self, validated_data):
        # Extract many-to-many data
        target_group_ids = validated_data.pop('target_group_ids', [])
        target_apartment_ids = validated_data.pop('target_apartment_ids', [])
        
        # Create announcement
        announcement = super().create(validated_data)
        
        # Set many-to-many relationships
        if target_group_ids:
            announcement.target_groups.set(target_group_ids)
        if target_apartment_ids:
            announcement.target_apartments.set(target_apartment_ids)
        
        return announcement
    
    def update(self, instance, validated_data):
        # Extract many-to-many data
        target_group_ids = validated_data.pop('target_group_ids', None)
        target_apartment_ids = validated_data.pop('target_apartment_ids', None)
        
        # Update announcement
        announcement = super().update(instance, validated_data)
        
        # Update many-to-many relationships
        if target_group_ids is not None:
            announcement.target_groups.set(target_group_ids)
        if target_apartment_ids is not None:
            announcement.target_apartments.set(target_apartment_ids)
        
        return announcement


class AnnouncementShareSerializer(serializers.ModelSerializer):
    """Serializer for announcement shares"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AnnouncementShare
        fields = ['id', 'user', 'platform', 'shared_at']
        read_only_fields = ['shared_at']


class AnnouncementFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for announcement feedback"""
    
    user = UserSerializer(read_only=True)
    feedback_type_display = serializers.CharField(source='get_feedback_type_display', read_only=True)
    
    class Meta:
        model = AnnouncementFeedback
        fields = [
            'id', 'user', 'feedback_type', 'feedback_type_display',
            'comment', 'created_at'
        ]
        read_only_fields = ['created_at']


class AnnouncementStatsSerializer(serializers.Serializer):
    """Serializer for announcement statistics"""
    
    total_announcements = serializers.IntegerField()
    published_announcements = serializers.IntegerField()
    draft_announcements = serializers.IntegerField()
    urgent_announcements = serializers.IntegerField()
    avg_read_percentage = serializers.FloatField()
    total_views = serializers.IntegerField()
    total_reads = serializers.IntegerField()
    announcements_by_category = serializers.ListField()
    announcements_by_priority = serializers.ListField()
    announcements_by_type = serializers.ListField()
    recent_activity = serializers.ListField()


class AnnouncementQuickActionSerializer(serializers.Serializer):
    """Serializer for announcement quick actions"""
    
    action = serializers.ChoiceField(choices=[
        ('mark_read', _('Okundu işaretle')),
        ('toggle_like', _('Beğeni durumunu değiştir')),
        ('share', _('Paylaş')),
        ('feedback', _('Geri bildirim ver')),
    ])
    
    # Optional fields based on action
    platform = serializers.CharField(required=False)  # for share action
    feedback_type = serializers.CharField(required=False)  # for feedback action
    comment = serializers.CharField(required=False)  # for feedback action
