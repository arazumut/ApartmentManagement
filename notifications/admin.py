from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from .models import NotificationGroup, Notification, NotificationPreference


@admin.register(NotificationGroup)
class NotificationGroupAdmin(ModelAdmin):
    list_display = ('name', 'category', 'building', 'is_active')
    list_filter = ('category', 'is_active', 'building')
    search_fields = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'building', 'is_active'),
        }),
    )


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    """Admin interface for notifications"""
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at', 'group__category')
    search_fields = ('title', 'message', 'user__email', 'user__first_name', 'user__last_name')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'group', 'title', 'message'),
        }),
        (_('Notification Details'), {
            'fields': ('notification_type', 'link', 'apartment'),
        }),
        (_('Status'), {
            'fields': ('is_read', 'is_email_sent', 'is_sms_sent'),
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at',)
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    @admin.action(description=_("Mark selected notifications as read"))
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, _("Selected notifications have been marked as read."))
    
    @admin.action(description=_("Mark selected notifications as unread"))
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, _("Selected notifications have been marked as unread."))


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(ModelAdmin):
    list_display = ('user', 'email_notifications', 'sms_notifications', 'push_notifications')
    list_filter = ('email_notifications', 'sms_notifications', 'push_notifications')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    
    fieldsets = (
        (None, {
            'fields': ('user',),
        }),
        (_('Delivery Preferences'), {
            'fields': ('email_notifications', 'sms_notifications', 'push_notifications'),
        }),
        (_('Category Preferences'), {
            'fields': ('payment_notifications', 'announcement_notifications', 'complaint_notifications', 'package_notifications'),
        }),
    )
