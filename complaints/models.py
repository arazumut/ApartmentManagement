from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from buildings.models import Building, Apartment
from users.models import User


class Complaint(models.Model):
    """Enhanced complaints and requests from residents"""
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    RESOLVED = 'resolved'
    REJECTED = 'rejected'
    CLOSED = 'closed'
    
    STATUS_CHOICES = (
        (NEW, _('Yeni')),
        (IN_PROGRESS, _('Devam Ediyor')),
        (RESOLVED, _('Çözüldü')),
        (REJECTED, _('Reddedildi')),
        (CLOSED, _('Kapatıldı')),
    )
    
    # Enhanced categories
    MAINTENANCE = 'maintenance'
    NOISE = 'noise'
    CLEANLINESS = 'cleanliness'
    SECURITY = 'security'
    PARKING = 'parking'
    NEIGHBOR = 'neighbor'
    ELEVATOR = 'elevator'
    HEATING = 'heating'
    WATER = 'water'
    ELECTRICAL = 'electrical'
    GARDEN = 'garden'
    MANAGEMENT = 'management'
    OTHER = 'other'
    
    CATEGORY_CHOICES = (
        (MAINTENANCE, _('Bakım')),
        (NOISE, _('Gürültü')),
        (CLEANLINESS, _('Temizlik')),
        (SECURITY, _('Güvenlik')),
        (PARKING, _('Otopark')),
        (NEIGHBOR, _('Komşu')),
        (ELEVATOR, _('Asansör')),
        (HEATING, _('Isıtma')),
        (WATER, _('Su')),
        (ELECTRICAL, _('Elektrik')),
        (GARDEN, _('Bahçe')),
        (MANAGEMENT, _('Yönetim')),
        (OTHER, _('Diğer')),
    )
    
    # Priority levels
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    EMERGENCY = 5
    
    PRIORITY_CHOICES = (
        (LOW, _('Düşük')),
        (MEDIUM, _('Orta')),
        (HIGH, _('Yüksek')),
        (URGENT, _('Acil')),
        (EMERGENCY, _('Kritik')),
    )
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='complaints')
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(_('başlık'), max_length=255)
    description = models.TextField(_('açıklama'))
    category = models.CharField(_('kategori'), max_length=20, choices=CATEGORY_CHOICES, default=MAINTENANCE)
    status = models.CharField(_('durum'), max_length=20, choices=STATUS_CHOICES, default=NEW)
    priority = models.PositiveSmallIntegerField(_('öncelik'), choices=PRIORITY_CHOICES, default=MEDIUM)
    
    # Enhanced fields
    is_anonymous = models.BooleanField(_('anonim şikayet'), default=False)
    expected_resolution_date = models.DateField(_('beklenen çözüm tarihi'), null=True, blank=True)
    actual_resolution_date = models.DateField(_('gerçek çözüm tarihi'), null=True, blank=True)
    estimated_cost = models.DecimalField(_('tahmini maliyet'), max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(_('gerçek maliyet'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Files and attachments
    attachment = models.FileField(_('ek dosya'), upload_to='complaints/', blank=True, null=True)
    before_photo = models.ImageField(_('öncesi fotoğraf'), upload_to='complaints/before/', blank=True, null=True)
    after_photo = models.ImageField(_('sonrası fotoğraf'), upload_to='complaints/after/', blank=True, null=True)
    
    # People involved
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_complaints')
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_complaints'
    )
    
    # Resolution details
    resolution_notes = models.TextField(_('çözüm notları'), blank=True, null=True)
    satisfaction_rating = models.PositiveSmallIntegerField(_('memnuniyet puanı'), null=True, blank=True, choices=[
        (1, _('Çok Kötü')),
        (2, _('Kötü')),
        (3, _('Orta')),
        (4, _('İyi')),
        (5, _('Mükemmel')),
    ])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    # Tracking
    view_count = models.PositiveIntegerField(_('görüntülenme sayısı'), default=0)
    is_recurring = models.BooleanField(_('tekrarlanan sorun'), default=False)
    parent_complaint = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_complaints')
    
    def __str__(self):
        return f"{self.apartment} - {self.title} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Set resolution timestamp when status changes to resolved
        if self.status == self.RESOLVED and not self.resolved_at:
            self.resolved_at = timezone.now()
            self.actual_resolution_date = timezone.now().date()
        
        # Auto-assign to building caretaker if not assigned
        if not self.assigned_to and self.building.caretaker:
            self.assigned_to = self.building.caretaker
        
        super().save(*args, **kwargs)
        
        # Send notifications on status change
        if self.pk:
            old_complaint = Complaint.objects.get(pk=self.pk)
            if old_complaint.status != self.status:
                self._send_status_notification()
    
    def _send_status_notification(self):
        """Send notification when status changes"""
        from notifications.models import create_notification
        
        if self.status == self.IN_PROGRESS:
            create_notification(
                user=self.created_by,
                title=f"Şikayetiniz İnceleme Altında",
                message=f"'{self.title}' konulu şikayetiniz inceleme altına alındı.",
                notification_type='info',
                apartment=self.apartment
            )
        elif self.status == self.RESOLVED:
            create_notification(
                user=self.created_by,
                title=f"Şikayetiniz Çözüldü",
                message=f"'{self.title}' konulu şikayetiniz çözüldü. Lütfen değerlendirin.",
                notification_type='success',
                apartment=self.apartment,
                action_required=True,
                action_text='Değerlendir',
                action_url=f'/complaints/{self.pk}/rate/'
            )
    
    def get_priority_color(self):
        """Get color class based on priority"""
        color_map = {
            self.LOW: 'text-success',
            self.MEDIUM: 'text-info',
            self.HIGH: 'text-warning',
            self.URGENT: 'text-danger',
            self.EMERGENCY: 'text-danger'
        }
        return color_map.get(self.priority, 'text-secondary')
    
    def get_priority_icon(self):
        """Get icon based on priority"""
        icon_map = {
            self.LOW: 'fas fa-arrow-down',
            self.MEDIUM: 'fas fa-minus',
            self.HIGH: 'fas fa-arrow-up',
            self.URGENT: 'fas fa-exclamation',
            self.EMERGENCY: 'fas fa-fire'
        }
        return icon_map.get(self.priority, 'fas fa-circle')
    
    def get_days_since_created(self):
        """Get days since complaint was created"""
        return (timezone.now().date() - self.created_at.date()).days
    
    def is_overdue(self):
        """Check if complaint is overdue"""
        if self.expected_resolution_date and self.status not in [self.RESOLVED, self.CLOSED]:
            return timezone.now().date() > self.expected_resolution_date
        return False
    
    def get_resolution_time(self):
        """Get resolution time in days"""
        if self.resolved_at:
            return (self.resolved_at.date() - self.created_at.date()).days
        return None
    
    class Meta:
        verbose_name = _('Şikayet')
        verbose_name_plural = _('Şikayetler')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['building', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['priority']),
        ]


class ComplaintComment(models.Model):
    """Enhanced comments on complaints for better communication"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaint_comments')
    comment = models.TextField(_('yorum'))
    attachment = models.FileField(_('ek dosya'), upload_to='complaint_comments/', blank=True, null=True)
    is_internal = models.BooleanField(_('dahili yorum'), default=False, help_text=_('Sadece yönetim tarafından görülebilir'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment on {self.complaint.title} by {self.user.email}"
    
    class Meta:
        verbose_name = _('Şikayet Yorumu')
        verbose_name_plural = _('Şikayet Yorumları')
        ordering = ['created_at']


class ComplaintStatusHistory(models.Model):
    """Track complaint status changes"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(_('eski durum'), max_length=20, choices=Complaint.STATUS_CHOICES)
    new_status = models.CharField(_('yeni durum'), max_length=20, choices=Complaint.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='status_changes')
    notes = models.TextField(_('notlar'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.complaint.title} - {self.old_status} → {self.new_status}"
    
    class Meta:
        verbose_name = _('Durum Geçmişi')
        verbose_name_plural = _('Durum Geçmişleri')
        ordering = ['-created_at']


class ComplaintCategory(models.Model):
    """Custom complaint categories for buildings"""
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='custom_categories')
    name = models.CharField(_('kategori adı'), max_length=100)
    description = models.TextField(_('açıklama'), blank=True, null=True)
    icon = models.CharField(_('ikon'), max_length=50, blank=True, null=True)
    color = models.CharField(_('renk'), max_length=7, default='#007bff')
    is_active = models.BooleanField(_('aktif'), default=True)
    sort_order = models.PositiveIntegerField(_('sıralama'), default=0)
    
    def __str__(self):
        return f"{self.building.name} - {self.name}"
    
    class Meta:
        verbose_name = _('Özel Kategori')
        verbose_name_plural = _('Özel Kategoriler')
        ordering = ['sort_order', 'name']
        unique_together = ['building', 'name']


class ComplaintTemplate(models.Model):
    """Templates for common complaints"""
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='complaint_templates')
    title = models.CharField(_('şablon başlığı'), max_length=255)
    description = models.TextField(_('şablon açıklaması'))
    category = models.CharField(_('kategori'), max_length=20, choices=Complaint.CATEGORY_CHOICES)
    priority = models.PositiveSmallIntegerField(_('öncelik'), choices=Complaint.PRIORITY_CHOICES, default=Complaint.MEDIUM)
    expected_resolution_days = models.PositiveIntegerField(_('beklenen çözüm günü'), default=7)
    is_active = models.BooleanField(_('aktif'), default=True)
    usage_count = models.PositiveIntegerField(_('kullanım sayısı'), default=0)
    
    def __str__(self):
        return f"{self.building.name} - {self.title}"
    
    class Meta:
        verbose_name = _('Şikayet Şablonu')
        verbose_name_plural = _('Şikayet Şablonları')
        ordering = ['-usage_count', 'title']


class ComplaintSurvey(models.Model):
    """Satisfaction surveys for resolved complaints"""
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name='survey')
    response_time_rating = models.PositiveSmallIntegerField(_('tepki süresi puanı'), choices=[
        (1, _('Çok Yavaş')),
        (2, _('Yavaş')),
        (3, _('Normal')),
        (4, _('Hızlı')),
        (5, _('Çok Hızlı')),
    ])
    solution_quality_rating = models.PositiveSmallIntegerField(_('çözüm kalitesi puanı'), choices=[
        (1, _('Çok Kötü')),
        (2, _('Kötü')),
        (3, _('Orta')),
        (4, _('İyi')),
        (5, _('Mükemmel')),
    ])
    staff_politeness_rating = models.PositiveSmallIntegerField(_('personel nezaketi puanı'), choices=[
        (1, _('Çok Kötü')),
        (2, _('Kötü')),
        (3, _('Orta')),
        (4, _('İyi')),
        (5, _('Mükemmel')),
    ])
    overall_satisfaction = models.PositiveSmallIntegerField(_('genel memnuniyet'), choices=[
        (1, _('Çok Memnuniyetsiz')),
        (2, _('Memnuniyetsiz')),
        (3, _('Orta')),
        (4, _('Memnun')),
        (5, _('Çok Memnun')),
    ])
    additional_feedback = models.TextField(_('ek geri bildirim'), blank=True, null=True)
    would_recommend = models.BooleanField(_('tavsiye eder misiniz'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_average_rating(self):
        """Calculate average rating"""
        ratings = [
            self.response_time_rating,
            self.solution_quality_rating,
            self.staff_politeness_rating,
            self.overall_satisfaction
        ]
        return sum(ratings) / len(ratings)
    
    def __str__(self):
        return f"Survey for {self.complaint.title} - {self.overall_satisfaction}/5"
    
    class Meta:
        verbose_name = _('Memnuniyet Anketi')
        verbose_name_plural = _('Memnuniyet Anketleri')
        ordering = ['-created_at']


# Helper functions
def create_complaint_from_template(template, apartment, user, additional_description=''):
    """Create a complaint from a template"""
    complaint = Complaint.objects.create(
        building=apartment.building,
        apartment=apartment,
        title=template.title,
        description=template.description + '\n\n' + additional_description if additional_description else template.description,
        category=template.category,
        priority=template.priority,
        expected_resolution_date=timezone.now().date() + timezone.timedelta(days=template.expected_resolution_days),
        created_by=user
    )
    
    # Update template usage count
    template.usage_count += 1
    template.save()
    
    return complaint


def get_complaint_statistics(building, start_date=None, end_date=None):
    """Get complaint statistics for a building"""
    complaints = Complaint.objects.filter(building=building)
    
    if start_date:
        complaints = complaints.filter(created_at__gte=start_date)
    if end_date:
        complaints = complaints.filter(created_at__lte=end_date)
    
    total_complaints = complaints.count()
    resolved_complaints = complaints.filter(status=Complaint.RESOLVED).count()
    
    # Average resolution time
    resolved_with_time = complaints.filter(
        status=Complaint.RESOLVED,
        resolved_at__isnull=False
    )
    
    if resolved_with_time.exists():
        avg_resolution_time = sum([
            (complaint.resolved_at.date() - complaint.created_at.date()).days
            for complaint in resolved_with_time
        ]) / resolved_with_time.count()
    else:
        avg_resolution_time = 0
    
    # Category breakdown
    category_stats = {}
    for category, display_name in Complaint.CATEGORY_CHOICES:
        count = complaints.filter(category=category).count()
        if count > 0:
            category_stats[display_name] = count
    
    return {
        'total_complaints': total_complaints,
        'resolved_complaints': resolved_complaints,
        'pending_complaints': total_complaints - resolved_complaints,
        'resolution_rate': (resolved_complaints / total_complaints * 100) if total_complaints > 0 else 0,
        'avg_resolution_time': avg_resolution_time,
        'category_stats': category_stats
    }
