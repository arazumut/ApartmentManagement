from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from .models import User

@admin.register(User)
class UserAdmin(ModelAdmin, BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture')}),
        (_('Permissions'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    
    # Unfold customizations
    unfold_form_direction = "horizontal" # "horizontal" or "vertical"
    unfold_form_template = "unfold/custom_form.html"
    
    actions = ["activate_users", "deactivate_users"]
    
    @admin.action(description=_("Activate selected users"))
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, _("Selected users have been activated."))
        
    @admin.action(description=_("Deactivate selected users"))
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, _("Selected users have been deactivated."))
