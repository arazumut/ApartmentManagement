from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserProfile, UserActivity


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    full_name = serializers.ReadOnlyField()
    initials = serializers.ReadOnlyField(source='get_initials')
    role_display = serializers.ReadOnlyField(source='get_role_display')
    age = serializers.ReadOnlyField(source='get_age')
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'initials',
            'phone_number', 'role', 'role_display', 'profile_picture',
            'date_of_birth', 'age', 'is_verified', 'email_verified', 'phone_verified',
            'last_login', 'date_joined', 'is_active'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm', 'first_name', 'last_name',
            'phone_number', 'role'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password')
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for user activities"""
    user = UserSerializer(read_only=True)
    activity_type_display = serializers.ReadOnlyField(source='get_activity_type_display')
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'activity_type', 'activity_type_display',
            'description', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    residents = serializers.IntegerField()
    admins = serializers.IntegerField()
    caretakers = serializers.IntegerField()
    security = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    recent_registrations = serializers.IntegerField()


class UserDetailSerializer(UserSerializer):
    """Detailed serializer for user with additional information"""
    profile = UserProfileSerializer(read_only=True)
    buildings = serializers.SerializerMethodField()
    apartments = serializers.SerializerMethodField()
    notification_count = serializers.ReadOnlyField(source='get_notification_count')
    complaint_count = serializers.ReadOnlyField(source='get_complaint_count')
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'profile', 'buildings', 'apartments', 'notification_count',
            'complaint_count', 'address', 'city', 'language', 'timezone'
        ]
    
    def get_buildings(self, obj):
        """Get buildings associated with user"""
        buildings = obj.get_buildings()
        return [{'id': b.id, 'name': b.name} for b in buildings]
    
    def get_apartments(self, obj):
        """Get apartments associated with user"""
        apartments = obj.get_apartments()
        return [{'id': a.id, 'number': a.apartment_number, 'building': a.building.name} for a in apartments]
