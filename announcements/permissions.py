from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


class AnnouncementPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Staff and superusers have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for staff
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        try:
            if hasattr(request.user, 'apartment') and request.user.apartment:
                if obj.building != request.user.apartment.building:
                    return False
                
                if obj.status != 'published':
                    return False
                
                if request.method in permissions.SAFE_METHODS:
                    return True
                
                return False
            else:
                return False
        except:
            return False


class AnnouncementCommentPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return True
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return obj.user == request.user
        
        return True


class AnnouncementCategoryPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_staff or request.user.is_superuser


class AnnouncementTemplatePermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_staff or request.user.is_superuser


class AnnouncementAnalyticsPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return request.user.is_staff or request.user.is_superuser


class IsOwnerOrStaff(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return (request.user.is_staff or 
                request.user.is_superuser or 
                obj.user == request.user)


class IsBuildingResident(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Staff and superusers have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user is a resident of the building
        try:
            if hasattr(request.user, 'apartment') and request.user.apartment:
                return obj.building == request.user.apartment.building
            else:
                return False
        except:
            return False


class CanInteractWithAnnouncement(permissions.BasePermission):
    """Permission for interacting with announcements (like, comment, share)"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        if obj.status != 'published':
            return False
        
        try:
            if hasattr(request.user, 'apartment') and request.user.apartment:
                return obj.building == request.user.apartment.building
            else:
                return False
        except:
            return False


class CanViewAnnouncementAnalytics(permissions.BasePermission):
    """Permission for viewing announcement analytics"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return request.user.is_staff or request.user.is_superuser
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'managed_buildings'):
            return obj.building in request.user.managed_buildings.all()
        
        return False


class CanManageAnnouncementComments(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions for authenticated users
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permissions for comments"""
        if not request.user.is_authenticated:
            return False
        
        # Staff and superusers have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Users can only edit/delete their own comments
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return obj.user == request.user
        
        # Read permissions for all authenticated users
        return True


class CanCreateAnnouncement(permissions.BasePermission):
    def has_permission(self, request, view):
        """Check if user can create announcements"""
        if not request.user.is_authenticated:
            return False
        
        # Only staff and superusers can create announcements
        return request.user.is_staff or request.user.is_superuser


class CanUpdateAnnouncement(permissions.BasePermission):
    """Permission for updating announcements"""
    
    def has_object_permission(self, request, view, obj):
        """Check if user can update the announcement"""
        if not request.user.is_authenticated:
            return False
        
        # Staff and superusers have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Creators can update their own announcements
        if obj.created_by == request.user:
            return True
        
        return False


class CanDeleteAnnouncement(permissions.BasePermission):
    """Permission for deleting announcements"""
    
    def has_object_permission(self, request, view, obj):
        """Check if user can delete the announcement"""
        if not request.user.is_authenticated:
            return False
        
        # Only staff and superusers can delete announcements
        return request.user.is_staff or request.user.is_superuser
