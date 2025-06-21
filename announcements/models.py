from django.db import models
from django.utils.translation import gettext_lazy as _
from buildings.models import Building
from users.models import User


class Announcement(models.Model):
    """Announcements for residents of a building"""
    NORMAL = 'normal'
    IMPORTANT = 'important'
    URGENT = 'urgent'
    
    PRIORITY_CHOICES = (
        (NORMAL, _('Normal')),
        (IMPORTANT, _('Important')),
        (URGENT, _('Urgent')),
    )
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(_('title'), max_length=255)
    content = models.TextField(_('content'))
    priority = models.CharField(_('priority'), max_length=10, choices=PRIORITY_CHOICES, default=NORMAL)
    attachment = models.FileField(_('attachment'), upload_to='announcements/', blank=True, null=True)
    is_active = models.BooleanField(_('is active'), default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.building.name} - {self.title}"
    
    class Meta:
        verbose_name = _('Announcement')
        verbose_name_plural = _('Announcements')
        ordering = ['-created_at']


class AnnouncementRead(models.Model):
    """Tracking which users have read announcements"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='reads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_announcements')
    read_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} read {self.announcement.title}"
    
    class Meta:
        verbose_name = _('Announcement Read')
        verbose_name_plural = _('Announcement Reads')
        unique_together = ['announcement', 'user']
