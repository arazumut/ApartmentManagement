from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.contrib.filters.admin import RangeDateFilter
from .models import (
    Announcement, AnnouncementCategory, AnnouncementTemplate,
    AnnouncementRead, AnnouncementComment, AnnouncementLike,
    AnnouncementView, AnnouncementShare, AnnouncementFeedback
)


class AnnouncementReadInline(TabularInline):
    model = AnnouncementRead
    extra = 0
    readonly_fields = ('user', 'read_at', 'device_type', 'ip_address')
    
    def has_add_permission(self, request, obj=None):
        return False


class AnnouncementCommentInline(TabularInline):
    model = AnnouncementComment
    extra = 0
    readonly_fields = ('user', 'created_at', 'is_approved')
    fields = ('user', 'comment', 'is_approved', 'created_at')


class AnnouncementLikeInline(TabularInline):
    model = AnnouncementLike
    extra = 0
    readonly_fields = ('user', 'created_at')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AnnouncementCategory)
class AnnouncementCategoryAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'colored_badge', 'announcement_count', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('announcement_count',)
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('name', 'slug', 'description'),
        }),
        (_('Görünüm'), {
            'fields': ('color', 'icon'),
        }),
        (_('Durum'), {
            'fields': ('is_active',),
        }),
    )
    
    def colored_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">'
            '<i class="{}"></i> {}</span>',
            obj.color, obj.icon, obj.name
        )
    colored_badge.short_description = _('Kategori')
    
    def announcement_count(self, obj):
        count = obj.announcements.count()
        return format_html(
            '<a href="{}?category__id__exact={}">{} duyuru</a>',
            reverse('admin:announcements_announcement_changelist'),
            obj.id, count
        )
    announcement_count.short_description = _('Duyuru Sayısı')


@admin.register(AnnouncementTemplate)
class AnnouncementTemplateAdmin(ModelAdmin):
    list_display = ('name', 'category', 'priority', 'auto_send_notification', 'is_active')
    list_filter = ('category', 'priority', 'auto_send_notification', 'is_active')
    search_fields = ('name', 'title_template', 'content_template')
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('name', 'category'),
        }),
        (_('Şablon'), {
            'fields': ('title_template', 'content_template'),
        }),
        (_('Ayarlar'), {
            'fields': ('priority', 'auto_send_notification', 'is_active'),
        }),
    )


@admin.register(Announcement)
class AnnouncementAdmin(ModelAdmin):
    list_display = ('title', 'building', 'category_badge', 'priority_badge', 'status_badge', 
                   'read_percentage', 'view_count', 'created_at', 'actions_column')
    list_filter = ('status', 'priority', 'announcement_type', 'category', 'building', 
                   'is_pinned', 'is_urgent', ('created_at', RangeDateFilter))
    search_fields = ('title', 'content', 'short_description', 'tags')
    readonly_fields = ('view_count', 'read_count', 'read_percentage_display', 
                      'created_at', 'updated_at', 'target_user_count')
    filter_horizontal = ('target_groups', 'target_apartments')
    date_hierarchy = 'created_at'
    actions = ['publish_announcements', 'archive_announcements', 'send_notifications']
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('title', 'short_description', 'content', 'building', 'category'),
        }),
        (_('Sınıflandırma'), {
            'fields': ('announcement_type', 'priority', 'status', 'tags'),
        }),
        (_('Medya'), {
            'fields': ('image', 'attachment'),
        }),
        (_('Hedefleme'), {
            'fields': ('target_groups', 'target_apartments', 'target_user_count'),
        }),
        (_('Zamanlama'), {
            'fields': ('publish_at', 'expires_at'),
        }),
        (_('Etkileşim'), {
            'fields': ('allow_comments', 'is_pinned', 'is_urgent'),
        }),
        (_('Bildirimler'), {
            'fields': ('send_notification', 'send_email', 'send_sms'),
        }),
        (_('İstatistikler'), {
            'fields': ('view_count', 'read_count', 'read_percentage_display'),
            'classes': ('collapse',),
        }),
        (_('Audit'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [AnnouncementReadInline, AnnouncementCommentInline, AnnouncementLikeInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'building', 'category', 'created_by'
        ).prefetch_related('reads', 'comments', 'likes')
    
    def category_badge(self, obj):
        if obj.category:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">'
                '<i class="{}"></i> {}</span>',
                obj.category.color, obj.category.icon, obj.category.name
            )
        return '-'
    category_badge.short_description = _('Kategori')
    
    def priority_badge(self, obj):
        colors = {
            'low': '#6c757d',
            'normal': '#007bff',
            'high': '#ffc107',
            'urgent': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">'
            '<i class="{}"></i> {}</span>',
            colors.get(obj.priority, '#007bff'), obj.get_priority_icon(), obj.get_priority_display()
        )
    priority_badge.short_description = _('Öncelik')
    
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'published': '#28a745',
            'archived': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.status, '#007bff'), obj.get_status_display()
        )
    status_badge.short_description = _('Durum')
    
    def read_percentage(self, obj):
        percentage = obj.get_read_percentage()
        color = '#28a745' if percentage >= 70 else '#ffc107' if percentage >= 40 else '#dc3545'
        return format_html(
            '<div style="width: 100px; background-color: #f8f9fa; border-radius: 10px; overflow: hidden;">'
            '<div style="width: {}%; height: 20px; background-color: {}; display: flex; align-items: center; justify-content: center; color: white; font-size: 11px;">'
            '{}%</div></div>',
            percentage, color, int(percentage)
        )
    read_percentage.short_description = _('Okunma Oranı')
    
    def read_percentage_display(self, obj):
        return f"{obj.get_read_percentage():.1f}%"
    read_percentage_display.short_description = _('Okunma Oranı')
    
    def target_user_count(self, obj):
        return obj.get_target_users().count()
    target_user_count.short_description = _('Hedef Kullanıcı Sayısı')
    
    def actions_column(self, obj):
        actions = []
        if obj.status == 'draft':
            actions.append(
                f'<a href="{reverse("admin:announcements_announcement_change", args=[obj.pk])}" '
                f'class="btn btn-sm btn-primary">Düzenle</a>'
            )
        actions.append(
            f'<a href="{obj.get_absolute_url()}" target="_blank" '
            f'class="btn btn-sm btn-info">Görüntüle</a>'
        )
        return format_html(' '.join(actions))
    actions_column.short_description = _('İşlemler')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    @admin.action(description=_('Seçili duyuruları yayınla'))
    def publish_announcements(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} duyuru yayınlandı.')
    
    @admin.action(description=_('Seçili duyuruları arşivle'))
    def archive_announcements(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} duyuru arşivlendi.')
    
    @admin.action(description=_('Seçili duyurular için bildirim gönder'))
    def send_notifications(self, request, queryset):
        count = 0
        for announcement in queryset:
            if announcement.status == 'published':
                announcement.send_notifications()
                count += 1
        self.message_user(request, f'{count} duyuru için bildirim gönderildi.')


@admin.register(AnnouncementRead)
class AnnouncementReadAdmin(ModelAdmin):
    list_display = ('announcement', 'user', 'device_type', 'read_at')
    list_filter = ('device_type', 'read_at', 'announcement__building')
    search_fields = ('announcement__title', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('announcement', 'user', 'read_at', 'device_type', 'ip_address')
    
    def has_add_permission(self, request):
        return False


@admin.register(AnnouncementComment)
class AnnouncementCommentAdmin(ModelAdmin):
    list_display = ('announcement', 'user', 'comment_preview', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at', 'announcement__building')
    search_fields = ('announcement__title', 'user__email', 'comment')
    actions = ['approve_comments', 'disapprove_comments']
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = _('Yorum')
    
    @admin.action(description=_('Seçili yorumları onayla'))
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} yorum onaylandı.')
    
    @admin.action(description=_('Seçili yorumları reddet'))
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} yorum reddedildi.')


@admin.register(AnnouncementLike)
class AnnouncementLikeAdmin(ModelAdmin):
    list_display = ('announcement', 'user', 'created_at')
    list_filter = ('created_at', 'announcement__building')
    search_fields = ('announcement__title', 'user__email')
    readonly_fields = ('announcement', 'user', 'created_at')
    
    def has_add_permission(self, request):
        return False


@admin.register(AnnouncementView)
class AnnouncementViewAdmin(ModelAdmin):
    list_display = ('announcement', 'user', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at', 'announcement__building')
    search_fields = ('announcement__title', 'user__email', 'ip_address')
    readonly_fields = ('announcement', 'user', 'ip_address', 'user_agent', 'viewed_at')
    
    def has_add_permission(self, request):
        return False


@admin.register(AnnouncementShare)
class AnnouncementShareAdmin(ModelAdmin):
    list_display = ('announcement', 'user', 'platform', 'shared_at')
    list_filter = ('platform', 'shared_at', 'announcement__building')
    search_fields = ('announcement__title', 'user__email')
    readonly_fields = ('announcement', 'user', 'platform', 'shared_at')
    
    def has_add_permission(self, request):
        return False


@admin.register(AnnouncementFeedback)
class AnnouncementFeedbackAdmin(ModelAdmin):
    list_display = ('announcement', 'user', 'feedback_type', 'created_at')
    list_filter = ('feedback_type', 'created_at', 'announcement__building')
    search_fields = ('announcement__title', 'user__email', 'comment')
    readonly_fields = ('announcement', 'user', 'feedback_type', 'created_at')
    
    def has_add_permission(self, request):
        return False


# Custom admin site modifications
admin.site.site_header = _('Apartman Yönetim Sistemi')
admin.site.site_title = _('Duyuru Yönetimi')
admin.site.index_title = _('Duyuru Yönetim Paneli')
