from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
from buildings.models import Building
from users.models import User


class MaintenanceTask(models.Model):
    """Smart maintenance task management"""
    
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'
    
    FREQUENCY_CHOICES = [
        (DAILY, _('Günlük')),
        (WEEKLY, _('Haftalık')),
        (MONTHLY, _('Aylık')),
        (QUARTERLY, _('3 Aylık')),
        (YEARLY, _('Yıllık')),
    ]
    
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    
    PRIORITY_CHOICES = [
        (LOW, _('Düşük')),
        (MEDIUM, _('Orta')),
        (HIGH, _('Yüksek')),
        (CRITICAL, _('Kritik')),
    ]
    
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    OVERDUE = 'overdue'
    
    STATUS_CHOICES = [
        (PENDING, _('Beklemede')),
        (IN_PROGRESS, _('Devam Ediyor')),
        (COMPLETED, _('Tamamlandı')),
        (CANCELLED, _('İptal Edildi')),
        (OVERDUE, _('Vadesi Geçti')),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='maintenance_tasks')
    title = models.CharField(_('başlık'), max_length=200)
    description = models.TextField(_('açıklama'))
    category = models.CharField(_('kategori'), max_length=50, choices=[
        ('electrical', _('Elektrik')),
        ('plumbing', _('Tesisat')),
        ('hvac', _('Isıtma/Soğutma')),
        ('elevator', _('Asansör')),
        ('security', _('Güvenlik')),
        ('cleaning', _('Temizlik')),
        ('landscaping', _('Peyzaj')),
        ('structural', _('Yapısal')),
        ('fire_safety', _('Yangın Güvenliği')),
        ('other', _('Diğer')),
    ])
    
    priority = models.IntegerField(_('öncelik'), choices=PRIORITY_CHOICES, default=MEDIUM)
    status = models.CharField(_('durum'), max_length=20, choices=STATUS_CHOICES, default=PENDING)
    
    # Scheduling
    is_recurring = models.BooleanField(_('tekrarlanan görev'), default=False)
    frequency = models.CharField(_('sıklık'), max_length=20, choices=FREQUENCY_CHOICES, blank=True, null=True)
    
    # Dates
    scheduled_date = models.DateTimeField(_('planlanan tarih'))
    due_date = models.DateTimeField(_('bitiş tarihi'))
    completed_date = models.DateTimeField(_('tamamlanma tarihi'), null=True, blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_maintenance_tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_maintenance_tasks')
    
    # Cost and time estimation
    estimated_duration = models.DurationField(_('tahmini süre'), default=timedelta(hours=1))
    actual_duration = models.DurationField(_('gerçek süre'), null=True, blank=True)
    estimated_cost = models.DecimalField(_('tahmini maliyet'), max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(_('gerçek maliyet'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Equipment and materials
    required_materials = models.TextField(_('gerekli malzemeler'), blank=True, null=True)
    required_tools = models.TextField(_('gerekli aletler'), blank=True, null=True)
    
    # Documentation
    before_photos = models.JSONField(_('öncesi fotoğraflar'), default=list, blank=True)
    after_photos = models.JSONField(_('sonrası fotoğraflar'), default=list, blank=True)
    completion_notes = models.TextField(_('tamamlama notları'), blank=True, null=True)
    
    # Notifications
    notify_before_days = models.IntegerField(_('kaç gün önce bildirim'), default=1)
    notify_on_overdue = models.BooleanField(_('vadesi geçince bildirim'), default=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Bakım Görevi')
        verbose_name_plural = _('Bakım Görevleri')
        ordering = ['-priority', 'due_date']
        indexes = [
            models.Index(fields=['building', 'status']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.building.name} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Update status based on dates
        now = timezone.now()
        if self.status == self.PENDING and now > self.due_date:
            self.status = self.OVERDUE
        
        # Auto-assign to building caretaker if not assigned
        if not self.assigned_to and self.building.caretaker:
            self.assigned_to = self.building.caretaker
        
        super().save(*args, **kwargs)
        
        # Create recurring task if needed
        if self.is_recurring and self.status == self.COMPLETED:
            self.create_next_occurrence()
    
    def create_next_occurrence(self):
        """Create next occurrence for recurring tasks"""
        if not self.is_recurring or not self.frequency:
            return
        
        next_date = self.scheduled_date
        
        if self.frequency == self.DAILY:
            next_date += timedelta(days=1)
        elif self.frequency == self.WEEKLY:
            next_date += timedelta(weeks=1)
        elif self.frequency == self.MONTHLY:
            next_date += timedelta(days=30)
        elif self.frequency == self.QUARTERLY:
            next_date += timedelta(days=90)
        elif self.frequency == self.YEARLY:
            next_date += timedelta(days=365)
        
        # Create new task
        MaintenanceTask.objects.create(
            building=self.building,
            title=self.title,
            description=self.description,
            category=self.category,
            priority=self.priority,
            is_recurring=True,
            frequency=self.frequency,
            scheduled_date=next_date,
            due_date=next_date + (self.due_date - self.scheduled_date),
            assigned_to=self.assigned_to,
            created_by=self.created_by,
            estimated_duration=self.estimated_duration,
            estimated_cost=self.estimated_cost,
            required_materials=self.required_materials,
            required_tools=self.required_tools,
            notify_before_days=self.notify_before_days
        )
    
    def is_overdue(self):
        """Check if task is overdue"""
        return timezone.now() > self.due_date and self.status not in [self.COMPLETED, self.CANCELLED]
    
    def get_priority_color(self):
        """Get color class for priority"""
        colors = {
            self.LOW: 'success',
            self.MEDIUM: 'info',
            self.HIGH: 'warning',
            self.CRITICAL: 'danger'
        }
        return colors.get(self.priority, 'secondary')
    
    def get_status_color(self):
        """Get color class for status"""
        colors = {
            self.PENDING: 'warning',
            self.IN_PROGRESS: 'info',
            self.COMPLETED: 'success',
            self.CANCELLED: 'secondary',
            self.OVERDUE: 'danger'
        }
        return colors.get(self.status, 'secondary')


class MaintenanceSchedule(models.Model):
    """Preventive maintenance schedule template"""
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='maintenance_schedules')
    name = models.CharField(_('plan adı'), max_length=100)
    description = models.TextField(_('açıklama'), blank=True, null=True)
    
    # Asset/Equipment details
    equipment_type = models.CharField(_('ekipman türü'), max_length=100)
    location = models.CharField(_('konum'), max_length=200)
    
    # Schedule settings
    frequency = models.CharField(_('sıklık'), max_length=20, choices=MaintenanceTask.FREQUENCY_CHOICES)
    start_date = models.DateField(_('başlangıç tarihi'))
    is_active = models.BooleanField(_('aktif'), default=True)
    
    # Task template
    task_title_template = models.CharField(_('görev başlığı şablonu'), max_length=200)
    task_description_template = models.TextField(_('görev açıklaması şablonu'))
    task_category = models.CharField(_('görev kategorisi'), max_length=50)
    task_priority = models.IntegerField(_('görev önceliği'), choices=MaintenanceTask.PRIORITY_CHOICES, default=MaintenanceTask.MEDIUM)
    estimated_duration = models.DurationField(_('tahmini süre'), default=timedelta(hours=2))
    estimated_cost = models.DecimalField(_('tahmini maliyet'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Assignment
    default_assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='default_maintenance_schedules')
    
    # Last execution
    last_scheduled = models.DateTimeField(_('son planlandığı tarih'), null=True, blank=True)
    next_scheduled = models.DateTimeField(_('sonraki planlanan tarih'), null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Bakım Planı Şablonu')
        verbose_name = _('Bakım Planı')
        verbose_name_plural = _('Bakım Planları')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.building.name} - {self.name}"
    
    def generate_next_task(self):
        """Generate next maintenance task from this schedule"""
        if not self.is_active:
            return None
        
        # Calculate next date
        if self.last_scheduled:
            base_date = self.last_scheduled
        else:
            base_date = timezone.now()
        
        if self.frequency == MaintenanceTask.DAILY:
            next_date = base_date + timedelta(days=1)
        elif self.frequency == MaintenanceTask.WEEKLY:
            next_date = base_date + timedelta(weeks=1)
        elif self.frequency == MaintenanceTask.MONTHLY:
            next_date = base_date + timedelta(days=30)
        elif self.frequency == MaintenanceTask.QUARTERLY:
            next_date = base_date + timedelta(days=90)
        elif self.frequency == MaintenanceTask.YEARLY:
            next_date = base_date + timedelta(days=365)
        else:
            return None
        
        # Create task
        task = MaintenanceTask.objects.create(
            building=self.building,
            title=self.task_title_template.format(
                equipment=self.equipment_type,
                location=self.location,
                date=next_date.strftime('%d.%m.%Y')
            ),
            description=self.task_description_template,
            category=self.task_category,
            priority=self.task_priority,
            is_recurring=True,
            frequency=self.frequency,
            scheduled_date=next_date,
            due_date=next_date + self.estimated_duration,
            assigned_to=self.default_assignee or self.building.caretaker,
            created_by=self.building.admin,
            estimated_duration=self.estimated_duration,
            estimated_cost=self.estimated_cost
        )
        
        # Update schedule
        self.last_scheduled = next_date
        self.next_scheduled = self.calculate_next_date(next_date)
        self.save()
        
        return task
    
    def calculate_next_date(self, from_date):
        """Calculate next scheduled date"""
        if self.frequency == MaintenanceTask.DAILY:
            return from_date + timedelta(days=1)
        elif self.frequency == MaintenanceTask.WEEKLY:
            return from_date + timedelta(weeks=1)
        elif self.frequency == MaintenanceTask.MONTHLY:
            return from_date + timedelta(days=30)
        elif self.frequency == MaintenanceTask.QUARTERLY:
            return from_date + timedelta(days=90)
        elif self.frequency == MaintenanceTask.YEARLY:
            return from_date + timedelta(days=365)
        return None


class MaintenanceSupplier(models.Model):
    """Maintenance suppliers and service providers"""
    
    name = models.CharField(_('firma adı'), max_length=100)
    contact_person = models.CharField(_('iletişim kişisi'), max_length=100, blank=True, null=True)
    phone = models.CharField(_('telefon'), max_length=20)
    email = models.EmailField(_('e-posta'), blank=True, null=True)
    address = models.TextField(_('adres'), blank=True, null=True)
    
    # Services
    services = models.TextField(_('hizmetler'), help_text=_('Virgülle ayrılmış hizmet listesi'))
    coverage_areas = models.TextField(_('hizmet bölgeleri'), blank=True, null=True)
    
    # Rating and performance
    rating = models.DecimalField(_('değerlendirme'), max_digits=3, decimal_places=2, 
                                validators=[MinValueValidator(0), MaxValueValidator(5)], 
                                null=True, blank=True)
    total_jobs_completed = models.PositiveIntegerField(_('tamamlanan iş sayısı'), default=0)
    average_response_time = models.DurationField(_('ortalama tepki süresi'), null=True, blank=True)
    
    # Contract details
    contract_start = models.DateField(_('sözleşme başlangıcı'), null=True, blank=True)
    contract_end = models.DateField(_('sözleşme bitişi'), null=True, blank=True)
    hourly_rate = models.DecimalField(_('saatlik ücret'), max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(_('aktif'), default=True)
    is_preferred = models.BooleanField(_('tercihli tedarikçi'), default=False)
    
    # Notes
    notes = models.TextField(_('notlar'), blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Bakım Tedarikçisi')
        verbose_name_plural = _('Bakım Tedarikçileri')
        ordering = ['-is_preferred', '-rating', 'name']
    
    def __str__(self):
        return self.name
    
    def get_services_list(self):
        """Get services as a list"""
        return [s.strip() for s in self.services.split(',') if s.strip()]


class MaintenanceWorkOrder(models.Model):
    """Work order for maintenance tasks"""
    
    task = models.OneToOneField(MaintenanceTask, on_delete=models.CASCADE, related_name='work_order')
    supplier = models.ForeignKey(MaintenanceSupplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_orders')
    
    # Work order details
    work_order_number = models.CharField(_('iş emri no'), max_length=50, unique=True)
    description = models.TextField(_('iş tanımı'))
    special_instructions = models.TextField(_('özel talimatlar'), blank=True, null=True)
    
    # Scheduling
    requested_date = models.DateTimeField(_('talep edilen tarih'))
    confirmed_date = models.DateTimeField(_('onaylanan tarih'), null=True, blank=True)
    started_at = models.DateTimeField(_('başlangıç zamanı'), null=True, blank=True)
    completed_at = models.DateTimeField(_('bitiş zamanı'), null=True, blank=True)
    
    # Personnel
    technicians = models.ManyToManyField(User, related_name='maintenance_work_orders', blank=True)
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_work_orders')
    
    # Materials and costs
    materials_used = models.TextField(_('kullanılan malzemeler'), blank=True, null=True)
    labor_hours = models.DecimalField(_('işçilik saati'), max_digits=6, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(_('toplam maliyet'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Quality and feedback
    quality_rating = models.IntegerField(_('kalite puanı'), choices=[
        (1, _('Çok Kötü')),
        (2, _('Kötü')),
        (3, _('Orta')),
        (4, _('İyi')),
        (5, _('Mükemmel')),
    ], null=True, blank=True)
    
    customer_feedback = models.TextField(_('müşteri geri bildirimi'), blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('İş Emri')
        verbose_name_plural = _('İş Emirleri')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"İş Emri {self.work_order_number} - {self.task.title}"
    
    def save(self, *args, **kwargs):
        if not self.work_order_number:
            # Generate unique work order number
            import uuid
            self.work_order_number = f"WO-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class MaintenanceInventory(models.Model):
    """Inventory management for maintenance supplies"""
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='maintenance_inventory')
    name = models.CharField(_('malzeme adı'), max_length=100)
    description = models.TextField(_('açıklama'), blank=True, null=True)
    category = models.CharField(_('kategori'), max_length=50)
    
    # Stock information
    current_stock = models.PositiveIntegerField(_('mevcut stok'), default=0)
    minimum_stock = models.PositiveIntegerField(_('minimum stok'), default=5)
    maximum_stock = models.PositiveIntegerField(_('maksimum stok'), default=100)
    unit = models.CharField(_('birim'), max_length=20, default='adet')
    
    # Cost information
    unit_cost = models.DecimalField(_('birim maliyet'), max_digits=8, decimal_places=2)
    total_value = models.DecimalField(_('toplam değer'), max_digits=10, decimal_places=2, default=0)
    
    # Location
    storage_location = models.CharField(_('depo konumu'), max_length=100, blank=True, null=True)
    
    # Supplier
    supplier = models.ForeignKey(MaintenanceSupplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplied_items')
    
    # Tracking
    last_updated = models.DateTimeField(_('son güncelleme'), auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Bakım Malzemesi')
        verbose_name_plural = _('Bakım Malzemeleri')
        ordering = ['category', 'name']
        unique_together = ['building', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"
    
    def save(self, *args, **kwargs):
        self.total_value = self.current_stock * self.unit_cost
        super().save(*args, **kwargs)
    
    def is_low_stock(self):
        """Check if item is low on stock"""
        return self.current_stock <= self.minimum_stock
    
    def add_stock(self, quantity, cost_per_unit=None):
        """Add stock"""
        self.current_stock += quantity
        if cost_per_unit:
            # Update weighted average cost
            total_cost = (self.current_stock - quantity) * self.unit_cost + quantity * cost_per_unit
            self.unit_cost = total_cost / self.current_stock
        self.save()
    
    def remove_stock(self, quantity):
        """Remove stock"""
        if quantity <= self.current_stock:
            self.current_stock -= quantity
            self.save()
            return True
        return False
