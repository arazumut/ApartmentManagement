from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from users.models import User
from buildings.models import Building, Apartment


class NotificationGroup(models.Model):
    """Model for grouping notifications by category"""
    SYSTEM = 'system'
    PAYMENT = 'payment'
    BUILDING = 'building'
    COMPLAINT = 'complaint'
    ANNOUNCEMENT = 'announcement'
    PACKAGE = 'package'
    
    CATEGORY_CHOICES = (
        (SYSTEM, _('Sistem')),
        (PAYMENT, _('Ödeme')),
        (BUILDING, _('Bina')),
        (COMPLAINT, _('Şikayet')),
        (ANNOUNCEMENT, _('Duyuru')),
        (PACKAGE, _('Paket')),
    )
    
    name = models.CharField(_('isim'), max_length=100)
    category = models.CharField(_('kategori'), max_length=20, choices=CATEGORY_CHOICES, default=SYSTEM)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='notification_groups', null=True, blank=True)
    is_active = models.BooleanField(_('aktif mi'), default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Bildirim Grubu')
        verbose_name_plural = _('Bildirim Grupları')


class Notification(models.Model):
    """Model for user notifications"""
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'
    
    TYPE_CHOICES = (
        (INFO, _('Bilgi')),
        (SUCCESS, _('Başarılı')),
        (WARNING, _('Uyarı')),
        (ERROR, _('Hata')),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    group = models.ForeignKey(NotificationGroup, on_delete=models.SET_NULL, related_name='notifications', null=True, blank=True)
    title = models.CharField(_('başlık'), max_length=255)
    message = models.TextField(_('mesaj'))
    notification_type = models.CharField(_('bildirim tipi'), max_length=10, choices=TYPE_CHOICES, default=INFO)
    is_read = models.BooleanField(_('okundu mu'), default=False)
    link = models.CharField(_('bağlantı'), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_('oluşturulma tarihi'), default=timezone.now)
    apartment = models.ForeignKey(Apartment, on_delete=models.SET_NULL, related_name='notifications', null=True, blank=True)
    is_email_sent = models.BooleanField(_('e-posta gönderildi mi'), default=False)
    is_sms_sent = models.BooleanField(_('SMS gönderildi mi'), default=False)
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    class Meta:
        verbose_name = _('Bildirim')
        verbose_name_plural = _('Bildirimler')
        ordering = ['-created_at']


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    email_notifications = models.BooleanField(_('e-posta bildirimleri'), default=True)
    sms_notifications = models.BooleanField(_('SMS bildirimleri'), default=False)
    push_notifications = models.BooleanField(_('anlık bildirimler'), default=True)
    
    # Kategori bazlı bildirim tercihleri
    payment_notifications = models.BooleanField(_('ödeme bildirimleri'), default=True)
    announcement_notifications = models.BooleanField(_('duyuru bildirimleri'), default=True)
    complaint_notifications = models.BooleanField(_('şikayet bildirimleri'), default=True)
    package_notifications = models.BooleanField(_('paket bildirimleri'), default=True)
    
    def __str__(self):
        return f"{self.user.email} - Bildirim Tercihleri"
    
    class Meta:
        verbose_name = _('Bildirim Tercihi')
        verbose_name_plural = _('Bildirim Tercihleri')


def create_notification(user, title, message, notification_type=Notification.INFO, link=None, group=None, apartment=None):
    """Helper function to create a notification"""
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        group=group,
        apartment=apartment
    )
    
    # Kullanıcının bildirim tercihlerine göre e-posta/SMS gönderme işlemleri burada yapılabilir
    
    return notification


def send_building_notification(building, title, message, notification_type=Notification.INFO, group=None, exclude_user=None):
    """Send notification to all residents of a building"""
    # Tüm daireleri bul
    apartments = Apartment.objects.filter(building=building, is_occupied=True)
    
    # Her daire için sakinine bildirim gönder
    notifications = []
    for apartment in apartments:
        if apartment.resident and apartment.resident != exclude_user:
            notification = create_notification(
                user=apartment.resident,
                title=title,
                message=message,
                notification_type=notification_type,
                group=group,
                apartment=apartment
            )
            notifications.append(notification)
    
    return notifications
