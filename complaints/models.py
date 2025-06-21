from django.db import models
from django.utils.translation import gettext_lazy as _
from buildings.models import Building, Apartment
from users.models import User


class Complaint(models.Model):
    """Complaints and requests from residents"""
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    RESOLVED = 'resolved'
    REJECTED = 'rejected'
    
    STATUS_CHOICES = (
        (NEW, _('New')),
        (IN_PROGRESS, _('In Progress')),
        (RESOLVED, _('Resolved')),
        (REJECTED, _('Rejected')),
    )
    
    MAINTENANCE = 'maintenance'
    NOISE = 'noise'
    CLEANLINESS = 'cleanliness'
    SECURITY = 'security'
    PARKING = 'parking'
    NEIGHBOR = 'neighbor'
    OTHER = 'other'
    
    CATEGORY_CHOICES = (
        (MAINTENANCE, _('Maintenance')),
        (NOISE, _('Noise')),
        (CLEANLINESS, _('Cleanliness')),
        (SECURITY, _('Security')),
        (PARKING, _('Parking')),
        (NEIGHBOR, _('Neighbor')),
        (OTHER, _('Other')),
    )
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='complaints')
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'))
    category = models.CharField(_('category'), max_length=20, choices=CATEGORY_CHOICES, default=MAINTENANCE)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default=NEW)
    priority = models.PositiveSmallIntegerField(_('priority'), default=1, help_text=_('1-5, where 5 is highest priority'))
    attachment = models.FileField(_('attachment'), upload_to='complaints/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_complaints')
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_complaints'
    )
    resolution_notes = models.TextField(_('resolution notes'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.apartment} - {self.title} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = _('Complaint')
        verbose_name_plural = _('Complaints')
        ordering = ['-created_at']


class ComplaintComment(models.Model):
    """Comments on complaints for communication"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaint_comments')
    comment = models.TextField(_('comment'))
    attachment = models.FileField(_('attachment'), upload_to='complaint_comments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment on {self.complaint.title} by {self.user.email}"
    
    class Meta:
        verbose_name = _('Complaint Comment')
        verbose_name_plural = _('Complaint Comments')
        ordering = ['created_at']
