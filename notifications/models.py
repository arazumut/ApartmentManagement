from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from users.models import User


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
    title = models.CharField(_('başlık'), max_length=255)
    message = models.TextField(_('mesaj'))
    notification_type = models.CharField(_('bildirim tipi'), max_length=10, choices=TYPE_CHOICES, default=INFO)
    is_read = models.BooleanField(_('okundu mu'), default=False)
    link = models.CharField(_('bağlantı'), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_('oluşturulma tarihi'), default=timezone.now)
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    class Meta:
        verbose_name = _('Bildirim')
        verbose_name_plural = _('Bildirimler')
        ordering = ['-created_at']


def create_notification(user, title, message, notification_type=Notification.INFO, link=None):
    """Helper function to create a notification"""
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link
    )
