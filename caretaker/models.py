from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from buildings.models import Building
from users.models import User


class Task(models.Model):
    """Tasks assigned to caretakers"""
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = (
        (PENDING, _('Pending')),
        (IN_PROGRESS, _('In Progress')),
        (COMPLETED, _('Completed')),
        (CANCELLED, _('Cancelled')),
    )
    
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    ONE_TIME = 'one_time'
    
    FREQUENCY_CHOICES = (
        (DAILY, _('Daily')),
        (WEEKLY, _('Weekly')),
        (MONTHLY, _('Monthly')),
        (ONE_TIME, _('One Time')),
    )
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'))
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assigned_tasks',
        limit_choices_to={'role': User.CARETAKER}
    )
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default=PENDING)
    priority = models.PositiveSmallIntegerField(_('priority'), default=1, help_text=_('1-5, where 5 is highest priority'))
    due_date = models.DateTimeField(_('due date'))
    frequency = models.CharField(_('frequency'), max_length=20, choices=FREQUENCY_CHOICES, default=ONE_TIME)
    recurrence_end_date = models.DateField(_('recurrence end date'), blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    completion_notes = models.TextField(_('completion notes'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(_('completed at'), blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} - {self.assigned_to.get_full_name()} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')
        ordering = ['-due_date']
    
    def save(self, *args, **kwargs):
        # Update completed_at timestamp when status changes to completed
        if self.status == self.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        
        # If status is not completed, reset completed_at
        if self.status != self.COMPLETED and self.completed_at:
            self.completed_at = None
            
        super().save(*args, **kwargs)
        
        # If this is a recurring task that's been completed, create the next one
        if self.status == self.COMPLETED and self.frequency != self.ONE_TIME:
            self._create_next_recurring_task()
    
    def _create_next_recurring_task(self):
        """Create the next recurring task based on frequency"""
        if self.frequency == self.DAILY:
            next_due_date = self.due_date + timezone.timedelta(days=1)
        elif self.frequency == self.WEEKLY:
            next_due_date = self.due_date + timezone.timedelta(weeks=1)
        elif self.frequency == self.MONTHLY:
            # Use dateutil's relativedelta for accurate month addition
            from dateutil.relativedelta import relativedelta
            next_due_date = self.due_date + relativedelta(months=1)
        else:
            return
        
        # Don't create a new task if we've passed the recurrence end date
        if self.recurrence_end_date and next_due_date.date() > self.recurrence_end_date:
            return
        
        # Create the next task
        Task.objects.create(
            building=self.building,
            title=self.title,
            description=self.description,
            assigned_to=self.assigned_to,
            priority=self.priority,
            due_date=next_due_date,
            frequency=self.frequency,
            recurrence_end_date=self.recurrence_end_date,
            created_by=self.created_by,
        )


class TaskImage(models.Model):
    """Images associated with task completion"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(_('image'), upload_to='task_images/')
    caption = models.CharField(_('caption'), max_length=255, blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_task_images')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.task.title}"
    
    class Meta:
        verbose_name = _('Task Image')
        verbose_name_plural = _('Task Images')
