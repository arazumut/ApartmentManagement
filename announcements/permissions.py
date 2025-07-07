from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


class AnnouncementPermission(permissions.BasePermission):
    """Custom permission for announcements"""
    
    def has_permission(self, request, view):
        """Check if user has permission to access announcements"""
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
        """Check object-level permissions"""
        if not request.user.is_authenticated:
            return False
        
        # Staff and superusers have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user has access to this announcement's building
        try:
            if hasattr(request.user, 'apartment') and request.user.apartment:
                # User must be in the same building
                if obj.building != request.user.apartment.building:
                    return False
                
                # Check if announcement is published for regular users
                if obj.status != 'published':
                    return False
                
                # Read permissions for building residents
                if request.method in permissions.SAFE_METHODS:
                    return True
                
                # Write permissions only for staff
                return False
            else:
                # User has no apartment assigned
                return False
        except:
            return False


class AnnouncementCommentPermission(permissions.BasePermission):
    """Custom permission for announcement comments"""
    
    def has_permission(self, request, view):
        """Check if user has permission to access comments"""
        if not request.user.is_authenticated:
            return False
        
        # All authenticated users can read comments
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # All authenticated users can post comments
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


class AnnouncementCategoryPermission(permissions.BasePermission):
    """Custom permission for announcement categories"""
    
    def has_permission(self, request, view):
        """Check if user has permission to access categories"""
        if not request.user.is_authenticated:
            return False
        
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for staff
        return request.user.is_staff or request.user.is_superuser


class AnnouncementTemplatePermission(permissions.BasePermission):
    """Custom permission for announcement templates"""
    
    def has_permission(self, request, view):
        """Check if user has permission to access templates"""
        if not request.user.is_authenticated:
            return False
        
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for staff
        return request.user.is_staff or request.user.is_superuser


class AnnouncementAnalyticsPermission(permissions.BasePermission):
    """Custom permission for announcement analytics"""
    
    def has_permission(self, request, view):
        """Check if user has permission to access analytics"""
        if not request.user.is_authenticated:
            return False
        
        # Analytics only for staff and superusers
        return request.user.is_staff or request.user.is_superuser


class IsOwnerOrStaff(permissions.BasePermission):
    """Permission that allows owners of an object or staff to edit it"""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions for staff or owner
        return (request.user.is_staff or 
                request.user.is_superuser or 
                obj.user == request.user)


class IsBuildingResident(permissions.BasePermission):
    """Permission that checks if user is a resident of the building"""
    
    def has_object_permission(self, request, view, obj):
        """Check if user is a resident of the announcement's building"""
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
        """Check if user can interact with the announcement"""
        if not request.user.is_authenticated:
            return False
        
        # Staff and superusers have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if announcement is published
        if obj.status != 'published':
            return False
        
        # Check if user is a resident of the building
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
        """Check if user can view analytics"""
        if not request.user.is_authenticated:
            return False
        
        # Only staff and superusers can view analytics
        return request.user.is_staff or request.user.is_superuser
    
    def has_object_permission(self, request, view, obj):
        """Check if user can view analytics for specific announcement"""
        if not request.user.is_authenticated:
            return False
        
        # Staff and superusers have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Building managers can view analytics for their building
        if hasattr(request.user, 'managed_buildings'):
            return obj.building in request.user.managed_buildings.all()
        
        return False


class CanManageAnnouncementComments(permissions.BasePermission):
    """Permission for managing announcement comments"""
    
    def has_permission(self, request, view):
        """Check if user can manage comments"""
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
    """Permission for creating announcements"""
    
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
