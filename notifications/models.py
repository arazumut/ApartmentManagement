from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from users.models import User
from buildings.models import Building, Apartment
import json


class NotificationGroup(models.Model):
    """Model for grouping notifications by category"""
    SYSTEM = 'system'
    PAYMENT = 'payment'
    BUILDING = 'building'
    COMPLAINT = 'complaint'
    ANNOUNCEMENT = 'announcement'
    PACKAGE = 'package'
    MAINTENANCE = 'maintenance'
    SECURITY = 'security'
    
    CATEGORY_CHOICES = (
        (SYSTEM, _('Sistem')),
        (PAYMENT, _('Ödeme')),
        (BUILDING, _('Bina')),
        (COMPLAINT, _('Şikayet')),
        (ANNOUNCEMENT, _('Duyuru')),
        (PACKAGE, _('Paket')),
        (MAINTENANCE, _('Bakım')),
        (SECURITY, _('Güvenlik')),
    )
    
    name = models.CharField(_('isim'), max_length=100)
    category = models.CharField(_('kategori'), max_length=20, choices=CATEGORY_CHOICES, default=SYSTEM)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='notification_groups', null=True, blank=True)
    is_active = models.BooleanField(_('aktif mi'), default=True)
    description = models.TextField(_('açıklama'), blank=True, null=True)
    priority = models.IntegerField(_('öncelik'), default=1, help_text=_('1=Düşük, 2=Orta, 3=Yüksek'))
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Bildirim Grubu')
        verbose_name_plural = _('Bildirim Grupları')


class Notification(models.Model):
    """Enhanced notification model with better features"""
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'
    URGENT = 'urgent'
    
    TYPE_CHOICES = (
        (INFO, _('Bilgi')),
        (SUCCESS, _('Başarılı')),
        (WARNING, _('Uyarı')),
        (ERROR, _('Hata')),
        (URGENT, _('Acil')),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    group = models.ForeignKey(NotificationGroup, on_delete=models.SET_NULL, related_name='notifications', null=True, blank=True)
    title = models.CharField(_('başlık'), max_length=255)
    message = models.TextField(_('mesaj'))
    notification_type = models.CharField(_('bildirim tipi'), max_length=10, choices=TYPE_CHOICES, default=INFO)
    is_read = models.BooleanField(_('okundu mu'), default=False)
    read_at = models.DateTimeField(_('okunma tarihi'), null=True, blank=True)
    link = models.CharField(_('bağlantı'), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_('oluşturulma tarihi'), default=timezone.now)
    apartment = models.ForeignKey(Apartment, on_delete=models.SET_NULL, related_name='notifications', null=True, blank=True)
    
    # Email and SMS tracking
    is_email_sent = models.BooleanField(_('e-posta gönderildi mi'), default=False)
    email_sent_at = models.DateTimeField(_('e-posta gönderilme tarihi'), null=True, blank=True)
    is_sms_sent = models.BooleanField(_('SMS gönderildi mi'), default=False)
    sms_sent_at = models.DateTimeField(_('SMS gönderilme tarihi'), null=True, blank=True)
    
    # Advanced features
    action_required = models.BooleanField(_('eylem gerekli mi'), default=False)
    action_url = models.CharField(_('eylem URL'), max_length=255, blank=True, null=True)
    action_text = models.CharField(_('eylem metni'), max_length=100, blank=True, null=True)
    expires_at = models.DateTimeField(_('son geçerlilik tarihi'), null=True, blank=True)
    metadata = models.JSONField(_('ek bilgiler'), default=dict, blank=True)
    
    # Tracking
    is_dismissed = models.BooleanField(_('kapatıldı mı'), default=False)
    dismissed_at = models.DateTimeField(_('kapatılma tarihi'), null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def dismiss(self):
        """Dismiss notification"""
        if not self.is_dismissed:
            self.is_dismissed = True
            self.dismissed_at = timezone.now()
            self.save()
    
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def get_icon(self):
        """Get icon class based on notification type"""
        icon_map = {
            'info': 'fas fa-info-circle',
            'success': 'fas fa-check-circle',
            'warning': 'fas fa-exclamation-triangle',
            'error': 'fas fa-times-circle',
            'urgent': 'fas fa-exclamation-circle'
        }
        return icon_map.get(self.notification_type, 'fas fa-bell')
    
    def get_color_class(self):
        """Get color class based on notification type"""
        color_map = {
            'info': 'text-info',
            'success': 'text-success',
            'warning': 'text-warning',
            'error': 'text-danger',
            'urgent': 'text-danger'
        }
        return color_map.get(self.notification_type, 'text-secondary')
    
    class Meta:
        verbose_name = _('Bildirim')
        verbose_name_plural = _('Bildirimler')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
            models.Index(fields=['notification_type']),
        ]


class NotificationPreference(models.Model):
    """Enhanced user preferences for notifications"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Channel preferences
    email_notifications = models.BooleanField(_('e-posta bildirimleri'), default=True)
    sms_notifications = models.BooleanField(_('SMS bildirimleri'), default=False)
    push_notifications = models.BooleanField(_('anlık bildirimler'), default=True)
    
    # Category preferences
    payment_notifications = models.BooleanField(_('ödeme bildirimleri'), default=True)
    announcement_notifications = models.BooleanField(_('duyuru bildirimleri'), default=True)
    complaint_notifications = models.BooleanField(_('şikayet bildirimleri'), default=True)
    package_notifications = models.BooleanField(_('paket bildirimleri'), default=True)
    maintenance_notifications = models.BooleanField(_('bakım bildirimleri'), default=True)
    security_notifications = models.BooleanField(_('güvenlik bildirimleri'), default=True)
    
    # Timing preferences
    quiet_hours_start = models.TimeField(_('sessiz saatler başlangıcı'), default='22:00')
    quiet_hours_end = models.TimeField(_('sessiz saatler bitişi'), default='08:00')
    weekend_notifications = models.BooleanField(_('hafta sonu bildirimleri'), default=True)
    
    # Frequency preferences
    digest_frequency = models.CharField(_('özet sıklığı'), max_length=20, choices=[
        ('immediately', _('Hemen')),
        ('hourly', _('Saatlik')),
        ('daily', _('Günlük')),
        ('weekly', _('Haftalık')),
        ('never', _('Hiçbir Zaman')),
    ], default='immediately')
    
    def __str__(self):
        return f"{self.user.email} - Bildirim Tercihleri"
    
    class Meta:
        verbose_name = _('Bildirim Tercihi')
        verbose_name_plural = _('Bildirim Tercihleri')


class NotificationTemplate(models.Model):
    """Templates for different types of notifications"""
    name = models.CharField(_('isim'), max_length=100, unique=True)
    category = models.CharField(_('kategori'), max_length=20, choices=NotificationGroup.CATEGORY_CHOICES)
    title_template = models.CharField(_('başlık şablonu'), max_length=255)
    message_template = models.TextField(_('mesaj şablonu'))
    email_template = models.TextField(_('e-posta şablonu'), blank=True, null=True)
    sms_template = models.TextField(_('SMS şablonu'), blank=True, null=True)
    is_active = models.BooleanField(_('aktif mi'), default=True)
    
    def __str__(self):
        return self.name
    
    def render_title(self, context):
        """Render title with context"""
        from django.template import Context, Template
        template = Template(self.title_template)
        return template.render(Context(context))
    
    def render_message(self, context):
        """Render message with context"""
        from django.template import Context, Template
        template = Template(self.message_template)
        return template.render(Context(context))
    
    class Meta:
        verbose_name = _('Bildirim Şablonu')
        verbose_name_plural = _('Bildirim Şablonları')


class NotificationLog(models.Model):
    """Log of all notification activities"""
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(_('eylem'), max_length=50, choices=[
        ('created', _('Oluşturuldu')),
        ('read', _('Okundu')),
        ('dismissed', _('Kapatıldı')),
        ('email_sent', _('E-posta Gönderildi')),
        ('sms_sent', _('SMS Gönderildi')),
        ('failed', _('Başarısız')),
    ])
    details = models.TextField(_('detaylar'), blank=True, null=True)
    timestamp = models.DateTimeField(_('zaman damgası'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Bildirim Günlüğü')
        verbose_name_plural = _('Bildirim Günlükleri')
        ordering = ['-timestamp']


# Enhanced Helper Functions
def create_notification(user, title, message, notification_type=Notification.INFO, 
                       link=None, group=None, apartment=None, action_required=False,
                       action_url=None, action_text=None, expires_at=None, metadata=None):
    """Enhanced helper function to create a notification"""
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        group=group,
        apartment=apartment,
        action_required=action_required,
        action_url=action_url,
        action_text=action_text,
        expires_at=expires_at,
        metadata=metadata or {}
    )
    
    # Log the creation
    NotificationLog.objects.create(
        notification=notification,
        action='created',
        details=f'Notification created for {user.email}'
    )
    
    # Send email/SMS based on user preferences
    _send_notification_channels(notification)
    
    return notification


def create_notification_from_template(user, template_name, context, **kwargs):
    """Create notification using a template"""
    try:
        template = NotificationTemplate.objects.get(name=template_name, is_active=True)
        title = template.render_title(context)
        message = template.render_message(context)
        
        return create_notification(
            user=user,
            title=title,
            message=message,
            **kwargs
        )
    except NotificationTemplate.DoesNotExist:
        # Fallback to basic notification
        return create_notification(
            user=user,
            title=context.get('title', 'Bildirim'),
            message=context.get('message', 'Yeni bir bildirim var.'),
            **kwargs
        )


def send_building_notification(building, title, message, notification_type=Notification.INFO, 
                              group=None, exclude_user=None, **kwargs):
    """Send notification to all residents of a building"""
    apartments = Apartment.objects.filter(building=building, is_occupied=True)
    
    notifications = []
    for apartment in apartments:
        if apartment.resident and apartment.resident != exclude_user:
            notification = create_notification(
                user=apartment.resident,
                title=title,
                message=message,
                notification_type=notification_type,
                group=group,
                apartment=apartment,
                **kwargs
            )
            notifications.append(notification)
    
    return notifications


def send_bulk_notification(users, title, message, **kwargs):
    """Send notification to multiple users"""
    notifications = []
    for user in users:
        notification = create_notification(
            user=user,
            title=title,
            message=message,
            **kwargs
        )
        notifications.append(notification)
    
    return notifications


def _send_notification_channels(notification):
    """Send notification through various channels based on user preferences"""
    try:
        prefs = notification.user.notification_preferences
    except NotificationPreference.DoesNotExist:
        # Create default preferences
        prefs = NotificationPreference.objects.create(user=notification.user)
    
    # Check if it's quiet hours
    current_time = timezone.now().time()
    if prefs.quiet_hours_start <= current_time <= prefs.quiet_hours_end:
        return  # Skip sending during quiet hours
    
    # Send email if enabled
    if prefs.email_notifications and not notification.is_email_sent:
        _send_email_notification(notification)
    
    # Send SMS if enabled (implement SMS service)
    if prefs.sms_notifications and not notification.is_sms_sent:
        _send_sms_notification(notification)


def _send_email_notification(notification):
    """Send email notification"""
    try:
        context = {
            'notification': notification,
            'user': notification.user,
            'apartment': notification.apartment,
        }
        
        html_message = render_to_string('notifications/email_notification.html', context)
        plain_message = notification.message
        
        send_mail(
            subject=f'[Apartman Yönetimi] {notification.title}',
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.user.email],
            fail_silently=False
        )
        
        notification.is_email_sent = True
        notification.email_sent_at = timezone.now()
        notification.save()
        
        # Log success
        NotificationLog.objects.create(
            notification=notification,
            action='email_sent',
            details=f'Email sent to {notification.user.email}'
        )
        
    except Exception as e:
        # Log failure
        NotificationLog.objects.create(
            notification=notification,
            action='failed',
            details=f'Email failed: {str(e)}'
        )


def _send_sms_notification(notification):
    """Send SMS notification (placeholder for SMS service integration)"""
    # This would integrate with an SMS service like Twilio, Nexmo, etc.
    # For now, just mark as sent
    notification.is_sms_sent = True
    notification.sms_sent_at = timezone.now()
    notification.save()
    
    NotificationLog.objects.create(
        notification=notification,
        action='sms_sent',
        details=f'SMS sent to {notification.user.phone}'
    )


def get_user_notification_stats(user):
    """Get notification statistics for a user"""
    total = user.notifications.count()
    unread = user.notifications.filter(is_read=False).count()
    urgent = user.notifications.filter(notification_type='urgent', is_read=False).count()
    
    return {
        'total': total,
        'unread': unread,
        'urgent': urgent,
        'read_rate': ((total - unread) / total * 100) if total > 0 else 0
    }
