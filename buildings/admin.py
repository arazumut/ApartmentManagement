from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from .models import Building, Apartment


class ApartmentInline(TabularInline):
    model = Apartment
    extra = 0
    fields = ('block', 'floor', 'number', 'resident', 'resident_type', 'is_occupied')
    autocomplete_fields = ['resident']
    can_delete = False
    show_change_link = True


@admin.register(Building)
class BuildingAdmin(ModelAdmin):
    list_display = ('name', 'address', 'block_count', 'apartment_count', 'caretaker', 'admin')
    list_filter = ('block_count',)
    search_fields = ('name', 'address')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['caretaker', 'admin']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'address'),
        }),
        (_('Building Information'), {
            'fields': ('block_count', 'floors_per_block', 'apartments_per_floor', 'construction_year', 'total_area_sqm'),
        }),
        (_('Additional Information'), {
            'fields': ('energy_efficiency_class', 'common_areas'),
            'classes': ('collapse',),
        }),
        (_('Management'), {
            'fields': ('caretaker', 'admin'),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [ApartmentInline]
    
    def apartment_count(self, obj):
        return obj.apartments.count()
    apartment_count.short_description = _('Apartment Count')


@admin.register(Apartment)
class ApartmentAdmin(ModelAdmin):
    list_display = ('building', 'block', 'floor', 'number', 'resident', 'resident_type', 'is_occupied')
    list_filter = ('building', 'floor', 'resident_type', 'is_occupied')
    search_fields = ('number', 'resident__first_name', 'resident__last_name', 'resident__email')
    autocomplete_fields = ['resident', 'owner', 'building']
    
    fieldsets = (
        (None, {
            'fields': ('building', 'block', 'floor', 'number'),
        }),
        (_('Apartment Details'), {
            'fields': ('size_sqm', 'bedroom_count'),
        }),
        (_('Residency Information'), {
            'fields': ('resident', 'resident_type', 'owner', 'is_occupied', 'occupant_count'),
        }),
    )
    
    actions = ['mark_as_occupied', 'mark_as_vacant']
    
    @admin.action(description=_("Mark selected apartments as occupied"))
    def mark_as_occupied(self, request, queryset):
        queryset.update(is_occupied=True)
        self.message_user(request, _("Selected apartments have been marked as occupied."))
    
    @admin.action(description=_("Mark selected apartments as vacant"))
    def mark_as_vacant(self, request, queryset):
        queryset.update(is_occupied=False)
        self.message_user(request, _("Selected apartments have been marked as vacant."))
