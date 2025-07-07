from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from buildings.models import Building, Apartment
from users.models import User


class Package(models.Model):
    """Packages delivered to residents"""
    PENDING = 'pending'
    DELIVERED = 'delivered'
    
    STATUS_CHOICES = (
        (PENDING, _('Pending')),
        (DELIVERED, _('Delivered')),
    )
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='packages')
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='packages')
    tracking_number = models.CharField(_('tracking number'), max_length=100, blank=True, null=True)
    sender = models.CharField(_('sender'), max_length=255, blank=True, null=True)
    description = models.TextField(_('description'), blank=True, null=True)
    image = models.ImageField(_('image'), upload_to='packages/', blank=True, null=True)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default=PENDING)
    received_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_packages',
        limit_choices_to={'role': User.CARETAKER}
    )
    received_at = models.DateTimeField(_('received at'), default=timezone.now)
    delivered_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='collected_packages'
    )
    delivered_at = models.DateTimeField(_('delivered at'), blank=True, null=True)
    delivery_signature = models.ImageField(_('delivery signature'), upload_to='signatures/', blank=True, null=True)
    notes = models.TextField(_('notes'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), default=timezone.now)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    def __str__(self):
        return f"Package for {self.apartment} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = _('Package')
        verbose_name_plural = _('Packages')
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Update delivered_at timestamp when status changes to delivered
        if self.status == self.DELIVERED and not self.delivered_at:
            self.delivered_at = timezone.now()
            
        # If status is not delivered, reset delivered_at
        if self.status != self.DELIVERED and self.delivered_at:
            self.delivered_at = None
            
        super().save(*args, **kwargs)


class Visitor(models.Model):
    """Visitors to the building"""
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='visitors')
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='visitors')
    name = models.CharField(_('name'), max_length=255)
    id_number = models.CharField(_('ID number'), max_length=50, blank=True, null=True)
    purpose = models.CharField(_('purpose of visit'), max_length=255)
    arrival_time = models.DateTimeField(_('arrival time'), default=timezone.now)
    departure_time = models.DateTimeField(_('departure time'), blank=True, null=True)
    vehicle_plate = models.CharField(_('vehicle plate'), max_length=20, blank=True, null=True)
    recorded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='recorded_visitors',
        limit_choices_to={'role': User.CARETAKER}
    )
    host = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hosted_visitors'
    )
    notes = models.TextField(_('notes'), blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - Visit to {self.apartment} - {self.arrival_time.strftime('%d/%m/%Y %H:%M')}"
    
    class Meta:
        verbose_name = _('Visitor')
        verbose_name_plural = _('Visitors')
        ordering = ['-arrival_time']
