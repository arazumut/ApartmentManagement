from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from buildings.models import Building
from users.models import User
import json


class AnnouncementCategory(models.Model):
    """Categories for announcements"""
    name = models.CharField(_('kategori adı'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True)
    description = models.TextField(_('açıklama'), blank=True)
    color = models.CharField(_('renk'), max_length=7, default='#007bff', 
                           help_text=_('Hex renk kodu'))
    icon = models.CharField(_('ikon'), max_length=100, default='ri-notification-line',
                          help_text=_('Remix Icon sınıfı'))
    is_active = models.BooleanField(_('aktif'), default=True)
    created_at = models.DateTimeField(_('oluşturulma tarihi'), auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Duyuru Kategorisi')
        verbose_name_plural = _('Duyuru Kategorileri')
        ordering = ['name']


class AnnouncementTemplate(models.Model):
    """Templates for common announcements"""
    name = models.CharField(_('şablon adı'), max_length=200)
    category = models.ForeignKey(AnnouncementCategory, on_delete=models.CASCADE,
                               related_name='templates', verbose_name=_('kategori'))
    title_template = models.CharField(_('başlık şablonu'), max_length=255)
    content_template = models.TextField(_('içerik şablonu'))
    priority = models.CharField(_('öncelik'), max_length=10, choices=[
        ('low', _('Düşük')),
        ('normal', _('Normal')),
        ('high', _('Yüksek')),
        ('urgent', _('Acil')),
    ], default='normal')
    auto_send_notification = models.BooleanField(_('otomatik bildirim gönder'), default=True)
    is_active = models.BooleanField(_('aktif'), default=True)
    created_at = models.DateTimeField(_('oluşturulma tarihi'), auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Duyuru Şablonu')
        verbose_name_plural = _('Duyuru Şablonları')
        ordering = ['name']


class Announcement(models.Model):
    """Enhanced announcements for residents of a building"""
    PRIORITY_CHOICES = [
        ('low', _('Düşük')),
        ('normal', _('Normal')),
        ('high', _('Yüksek')),
        ('urgent', _('Acil')),
    ]
    
    TYPE_CHOICES = [
        ('general', _('Genel')),
        ('maintenance', _('Bakım')),
        ('security', _('Güvenlik')),
        ('financial', _('Mali')),
        ('social', _('Sosyal')),
        ('emergency', _('Acil Durum')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Taslak')),
        ('published', _('Yayınlandı')),
        ('archived', _('Arşivlendi')),
    ]
    
    # Basic fields
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='announcements')
    category = models.ForeignKey(AnnouncementCategory, on_delete=models.SET_NULL, 
                               null=True, blank=True, related_name='announcements')
    title = models.CharField(_('başlık'), max_length=255)
    content = models.TextField(_('içerik'))
    short_description = models.CharField(_('kısa açıklama'), max_length=500, blank=True,
                                       help_text=_('Önizleme ve bildirimler için'))
    
    # Classification
    announcement_type = models.CharField(_('duyuru türü'), max_length=20, 
                                       choices=TYPE_CHOICES, default='general')
    priority = models.CharField(_('öncelik'), max_length=10, 
                              choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(_('durum'), max_length=10, 
                            choices=STATUS_CHOICES, default='draft')
    
    # Media
    attachment = models.FileField(_('ek dosya'), upload_to='announcements/attachments/', 
                                blank=True, null=True)
    image = models.ImageField(_('görsel'), upload_to='announcements/images/', 
                            blank=True, null=True)
    
    # Targeting
    target_groups = models.ManyToManyField(Group, blank=True, 
                                         verbose_name=_('hedef gruplar'),
                                         help_text=_('Boş bırakılırsa tüm sakinler'))
    target_apartments = models.ManyToManyField('buildings.Apartment', blank=True,
                                             verbose_name=_('hedef daireler'))
    
    # Timing
    publish_at = models.DateTimeField(_('yayın tarihi'), default=timezone.now)
    expires_at = models.DateTimeField(_('son geçerlilik tarihi'), null=True, blank=True)
    
    # Interaction
    allow_comments = models.BooleanField(_('yorumlara izin ver'), default=False)
    is_pinned = models.BooleanField(_('sabitlenmiş'), default=False)
    is_urgent = models.BooleanField(_('acil'), default=False)
    
    # Notifications
    send_notification = models.BooleanField(_('bildirim gönder'), default=True)
    send_email = models.BooleanField(_('e-posta gönder'), default=False)
    send_sms = models.BooleanField(_('SMS gönder'), default=False)
    
    # Metadata
    tags = models.JSONField(_('etiketler'), default=list, blank=True)
    metadata = models.JSONField(_('ek bilgiler'), default=dict, blank=True)
    
    # Tracking
    view_count = models.PositiveIntegerField(_('görüntülenme sayısı'), default=0)
    read_count = models.PositiveIntegerField(_('okunma sayısı'), default=0)
    
    # Audit
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                 related_name='created_announcements')
    created_at = models.DateTimeField(_('oluşturulma tarihi'), auto_now_add=True)
    updated_at = models.DateTimeField(_('güncellenme tarihi'), auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='updated_announcements')
    
    def __str__(self):
        return f"{self.building.name} - {self.title}"
    
    def get_absolute_url(self):
        return reverse('announcement_detail', kwargs={'pk': self.pk})
    
    def is_published(self):
        return self.status == 'published' and self.publish_at <= timezone.now()
    
    def is_expired(self):
        return self.expires_at and self.expires_at <= timezone.now()
    
    def get_target_users(self):
        """Get all users who should receive this announcement"""
        from buildings.models import Apartment
        
        # Start with building residents
        users = User.objects.filter(apartment__building=self.building)
        
        # Filter by target groups if specified
        if self.target_groups.exists():
            users = users.filter(groups__in=self.target_groups.all())
        
        # Filter by target apartments if specified
        if self.target_apartments.exists():
            users = users.filter(apartment__in=self.target_apartments.all())
        
        return users.distinct()
    
    def get_read_percentage(self):
        """Calculate read percentage"""
        total_users = self.get_target_users().count()
        if total_users == 0:
            return 0
        return (self.read_count / total_users) * 100
    
    def get_priority_color(self):
        """Get color class for priority"""
        colors = {
            'low': 'text-muted',
            'normal': 'text-primary',
            'high': 'text-warning',
            'urgent': 'text-danger'
        }
        return colors.get(self.priority, 'text-primary')
    
    def get_priority_icon(self):
        """Get icon for priority"""
        icons = {
            'low': 'ri-volume-down-line',
            'normal': 'ri-notification-line',
            'high': 'ri-volume-up-line',
            'urgent': 'ri-alarm-warning-line'
        }
        return icons.get(self.priority, 'ri-notification-line')
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def mark_as_read_by(self, user):
        """Mark announcement as read by user"""
        read_obj, created = AnnouncementRead.objects.get_or_create(
            announcement=self,
            user=user,
            defaults={'read_at': timezone.now()}
        )
        
        if created:
            # Update read count
            self.read_count += 1
            self.save(update_fields=['read_count'])
            
            # Send analytics event
            self._track_read_event(user)
        
        return read_obj
    
    def _track_read_event(self, user):
        """Track read event for analytics"""
        try:
            from core.models import ActivityLog
            ActivityLog.objects.create(
                user=user,
                action='announcement_read',
                object_id=self.pk,
                metadata={
                    'announcement_title': self.title,
                    'building_id': self.building.id,
                    'priority': self.priority,
                    'category': self.category.name if self.category else None
                }
            )
        except:
            pass
    
    def send_notifications(self):
        """Send notifications to target users"""
        if not self.send_notification:
            return
            
        from notifications.models import create_notification
        
        users = self.get_target_users()
        for user in users:
            create_notification(
                user=user,
                title=f'Yeni Duyuru: {self.title}',
                message=self.short_description or self.content[:200] + '...',
                notification_type='info' if self.priority == 'normal' else 'warning',
                link=self.get_absolute_url(),
                apartment=user.apartment if hasattr(user, 'apartment') else None
            )
    
    def save(self, *args, **kwargs):
        # Auto-generate short description if not provided
        if not self.short_description:
            self.short_description = self.content[:200] + '...' if len(self.content) > 200 else self.content
        
        # Set urgent flag based on priority
        if self.priority == 'urgent':
            self.is_urgent = True
        
        # Set publish date if status changed to published
        if self.status == 'published' and not self.publish_at:
            self.publish_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Send notifications if published
        if self.status == 'published' and self.send_notification:
            self.send_notifications()
    
    class Meta:
        verbose_name = _('Duyuru')
        verbose_name_plural = _('Duyurular')
        ordering = ['-is_pinned', '-publish_at']
        indexes = [
            models.Index(fields=['building', 'status']),
            models.Index(fields=['publish_at']),
            models.Index(fields=['priority']),
            models.Index(fields=['is_pinned']),
        ]


class AnnouncementRead(models.Model):
    """Enhanced tracking of which users have read announcements"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='reads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_announcements')
    read_at = models.DateTimeField(auto_now_add=True)
    
    # Additional tracking
    device_type = models.CharField(_('cihaz türü'), max_length=20, 
                                 choices=[
                                     ('web', _('Web')),
                                     ('mobile', _('Mobil')),
                                     ('email', _('E-posta')),
                                     ('sms', _('SMS')),
                                 ], default='web')
    ip_address = models.GenericIPAddressField(_('IP adresi'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    
    def __str__(self):
        return f"{self.user.email} read {self.announcement.title}"
    
    class Meta:
        verbose_name = _('Duyuru Okundu')
        verbose_name_plural = _('Duyuru Okunma Kayıtları')
        unique_together = ['announcement', 'user']
        indexes = [
            models.Index(fields=['announcement', 'read_at']),
            models.Index(fields=['user', 'read_at']),
        ]


class AnnouncementComment(models.Model):
    """Comments on announcements"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcement_comments')
    comment = models.TextField(_('yorum'))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                             related_name='replies', verbose_name=_('yanıt'))
    
    # Status
    is_approved = models.BooleanField(_('onaylandı'), default=False)
    is_edited = models.BooleanField(_('düzenlendi'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(_('oluşturulma tarihi'), auto_now_add=True)
    updated_at = models.DateTimeField(_('güncellenme tarihi'), auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.announcement.title}"
    
    @property
    def is_reply(self):
        return self.parent is not None
    
    class Meta:
        verbose_name = _('Duyuru Yorumu')
        verbose_name_plural = _('Duyuru Yorumları')
        ordering = ['-created_at']


class AnnouncementLike(models.Model):
    """Likes for announcements"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcement_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} liked {self.announcement.title}"
    
    class Meta:
        verbose_name = _('Duyuru Beğeni')
        verbose_name_plural = _('Duyuru Beğenileri')
        unique_together = ['announcement', 'user']


class AnnouncementView(models.Model):
    """Track announcement views for analytics"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(_('IP adresi'))
    user_agent = models.TextField(_('user agent'), blank=True)
    referer = models.URLField(_('referrer'), blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"View of {self.announcement.title}"
    
    class Meta:
        verbose_name = _('Duyuru Görüntülenme')
        verbose_name_plural = _('Duyuru Görüntülenmeler')
        indexes = [
            models.Index(fields=['announcement', 'viewed_at']),
            models.Index(fields=['user', 'viewed_at']),
        ]


class AnnouncementShare(models.Model):
    """Track announcement shares"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcement_shares')
    platform = models.CharField(_('platform'), max_length=50, choices=[
        ('email', _('E-posta')),
        ('whatsapp', _('WhatsApp')),
        ('telegram', _('Telegram')),
        ('facebook', _('Facebook')),
        ('twitter', _('Twitter')),
        ('linkedin', _('LinkedIn')),
        ('copy_link', _('Link Kopyala')),
    ])
    shared_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} shared {self.announcement.title} on {self.platform}"
    
    class Meta:
        verbose_name = _('Duyuru Paylaşım')
        verbose_name_plural = _('Duyuru Paylaşımları')


class AnnouncementFeedback(models.Model):
    """Feedback on announcements"""
    FEEDBACK_TYPES = [
        ('helpful', _('Yararlı')),
        ('not_helpful', _('Yararlı Değil')),
        ('outdated', _('Güncel Değil')),
        ('incorrect', _('Yanlış')),
        ('suggestion', _('Öneri')),
    ]
    
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcement_feedbacks')
    feedback_type = models.CharField(_('geri bildirim türü'), max_length=20, choices=FEEDBACK_TYPES)
    comment = models.TextField(_('yorum'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_feedback_type_display()}"
    
    class Meta:
        verbose_name = _('Duyuru Geri Bildirimi')
        verbose_name_plural = _('Duyuru Geri Bildirimleri')
        unique_together = ['announcement', 'user']


# Utility functions
def get_announcement_statistics(building=None, start_date=None, end_date=None):
    """Get announcement statistics"""
    from django.db.models import Count, Avg, Q
    from django.utils import timezone
    
    queryset = Announcement.objects.all()
    
    if building:
        queryset = queryset.filter(building=building)
    
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    
    if end_date:
        queryset = queryset.filter(created_at__lte=end_date)
    
    stats = {
        'total_announcements': queryset.count(),
        'published_announcements': queryset.filter(status='published').count(),
        'draft_announcements': queryset.filter(status='draft').count(),
        'urgent_announcements': queryset.filter(priority='urgent').count(),
        'avg_read_percentage': queryset.aggregate(
            avg_read=Avg('read_count')
        )['avg_read'] or 0,
        'total_views': sum(a.view_count for a in queryset),
        'total_reads': sum(a.read_count for a in queryset),
        'announcements_by_category': queryset.values('category__name').annotate(
            count=Count('id')
        ),
        'announcements_by_priority': queryset.values('priority').annotate(
            count=Count('id')
        ),
    }
    
    return stats


def create_announcement_from_template(template, building, user, context=None):
    """Create announcement from template"""
    from django.template import Context, Template
    
    context = context or {}
    context.update({
        'building': building,
        'user': user,
        'today': timezone.now().date(),
    })
    
    # Render templates
    title = Template(template.title_template).render(Context(context))
    content = Template(template.content_template).render(Context(context))
    
    announcement = Announcement.objects.create(
        building=building,
        category=template.category,
        title=title,
        content=content,
        priority=template.priority,
        send_notification=template.auto_send_notification,
        created_by=user,
        status='published'
    )
    
    return announcement
