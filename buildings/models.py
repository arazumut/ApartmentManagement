from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User


class Building(models.Model):
    """Model for buildings/apartment complexes"""
    name = models.CharField(_('name'), max_length=255)
    address = models.TextField(_('address'))
    block_count = models.PositiveSmallIntegerField(_('block count'), default=1)
    floors_per_block = models.PositiveSmallIntegerField(_('floors per block'), default=1)
    apartments_per_floor = models.PositiveSmallIntegerField(_('apartments per floor'), default=1)
    caretaker = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='managed_buildings',
        limit_choices_to={'role': User.CARETAKER}
    )
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='administered_buildings',
        limit_choices_to={'role': User.ADMIN}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Building')
        verbose_name_plural = _('Buildings')


class Apartment(models.Model):
    """Model for individual apartments within a building"""
    OWNER = 'owner'
    TENANT = 'tenant'
    
    RESIDENT_TYPE_CHOICES = (
        (OWNER, _('Owner')),
        (TENANT, _('Tenant')),
    )
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='apartments')
    block = models.CharField(_('block'), max_length=10, blank=True, null=True)
    floor = models.PositiveSmallIntegerField(_('floor'))
    number = models.CharField(_('number'), max_length=10)
    size_sqm = models.PositiveIntegerField(_('size (m²)'), default=0)
    bedroom_count = models.PositiveSmallIntegerField(_('bedroom count'), default=1)
    resident = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='apartments',
        limit_choices_to={'role': User.RESIDENT}
    )
    resident_type = models.CharField(_('resident type'), max_length=10, choices=RESIDENT_TYPE_CHOICES, default=OWNER)
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_apartments',
        limit_choices_to={'role': User.RESIDENT}
    )
    is_occupied = models.BooleanField(_('is occupied'), default=True)
    occupant_count = models.PositiveSmallIntegerField(_('occupant count'), default=1)
    
    def __str__(self):
        if self.block:
            return f"{self.building.name} - Block {self.block}, No: {self.number}"
        return f"{self.building.name} - Floor {self.floor}, No: {self.number}"
    
    class Meta:
        verbose_name = _('Apartment')
        verbose_name_plural = _('Apartments')
        unique_together = ['building', 'block', 'number']
